from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import Dict, List, Set
import time
import json
import os
from typing import Dict, Optional
from pathlib import Path


class DAGLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir

    def load_dag(self, filename: str) -> Dict:
        print("# JSON 파일에서 DAG 설정을 로드")
        try:
            file_path = self._get_file_path(filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                dag_dict = json.load(f)

            # DAG 유효성 검증
            self._validate_dag(dag_dict)
            return dag_dict

        except FileNotFoundError:
            raise Exception(f"DAG 설정 파일을 찾을 수 없습니다: {filename}")
        except json.JSONDecodeError:
            raise Exception(f"잘못된 JSON 형식입니다: {filename}")

    def _get_file_path(self, filename: str) -> str:
        """파일 경로 생성"""
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        return os.path.join(self.config_dir, filename)

    def _validate_dag(self, dag: Dict) -> None:
        """DAG 구조 유효성 검증"""
        required_fields = ['nodes', 'edges']
        for field in required_fields:
            if field not in dag:
                raise ValueError(f"필수 필드가 없습니다: {field}")

        # 노드 유효성 검증
        required_node_fields = ['id', 'type', 'dependencies', 'next']
        for node_id, node in dag['nodes'].items():
            for field in required_node_fields:
                if field not in node:
                    raise ValueError(f"노드 {node_id}에 필수 필드가 없습니다: {field}")

        # 엣지 유효성 검증
        for edge in dag['edges']:
            if 'source' not in edge or 'target' not in edge:
                raise ValueError("엣지에 source 또는 target이 없습니다")


class WorkflowDAGManager:
    def __init__(self, config_dir: str = "config"):
        self.loader = DAGLoader(config_dir)
        self.loaded_dags: Dict[str, Dict] = {}

    def get_dag(self, dag_id: str, refresh: bool = False) -> Dict:
        """DAG 설정 가져오기 (캐시 지원)"""
        if refresh or dag_id not in self.loaded_dags:
            self.loaded_dags[dag_id] = self.loader.load_dag(dag_id)
        return self.loaded_dags[dag_id]

    def reload_all(self) -> None:
        """모든 로드된 DAG 새로고침"""
        for dag_id in list(self.loaded_dags.keys()):
            self.get_dag(dag_id, refresh=True)

    def get_available_dags(self) -> list:
        """사용 가능한 모든 DAG 파일 목록 반환"""
        path = Path(self.loader.config_dir)
        return [f.stem for f in path.glob("*.json")]



class APIWorkflowExecutor:
    def __init__(self, dag: Dict, max_workers: int = 3):
        self.dag = dag
        self.max_workers = max_workers
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self.results: Dict[str, any] = {}

    def _genEndpoint(self, node_id):
        url = "http://localhost:8001/workflow/start"
        req_headers = {
            "Content-Type": "application/json"
        }
        req_data = {
            "workflow_id": node_id,
            "input_data": {
                "test": "data"
            }
        }
        return req_headers, req_data

    def execute_node(self, node_id: str):
        def execute_start_api_request(node: Dict, input_data: Dict = None):
            config = node["config"]["api"]
            node_id = node['id']
            url = config["url"] + config['route']
            header, data = self._genEndpoint(node_id)
            response = requests.post(url, headers=header, json=data, timeout=config["timeout"] / 1000)
            response.raise_for_status()  # HTTP 에러 체크
            print(" = Status Code:", response.status_code)
            print(" = Response:", json.dumps(response.json(), indent=2))
            return response.json()

        print("# 개별 노드 실행")
        node = self.dag["nodes"][node_id]
        try:
            if node["type"] == "start":
                print(" -- START -- ")
                result = execute_start_api_request(node)
                return node_id, result

            elif node["type"] == "task":
                print(" -- TASK -- ")
                input_data = self.prepare_input_data(node)
                result = self.execute_api_request(node, input_data)
                return node_id, result

            elif node["type"] == "end":
                print(" -- END --")
                result = self.aggregate_results(node)
                return node_id, result

        except Exception as e:
            return node_id, {"error_pool": str(e)}

    def execute(self):
        print("# ThreadPoolExecutor를 사용한 워크플로우 실행")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                # 실행 가능한 노드 찾기
                ready_nodes = self.get_ready_nodes()
                if not ready_nodes:
                    break
                print(f" - {ready_nodes} 노드에 대한 Future 객체 생성")
                future_to_node = {
                    executor.submit(self.execute_node, node_id): node_id
                    for node_id in ready_nodes
                }
                # for node_id in ready_nodes:
                #     node_id, result = self.execute_node(node_id)
                #     print(f"(completed) {node_id} : {result}")
                #     self.results[node_id] = result
                #     self.completed.add(node_id)

                print(future_to_node)
                print("# 완료된 작업 처리")
                for future in as_completed(future_to_node):
                    node_id, result = future.result()
                    print(f" - (completed) {node_id} : {result}")
                    if "error_pool" in result:
                        self.failed.add(node_id)
                    else:
                        self.results[node_id] = result
                        self.completed.add(node_id)

        return self.results.get("node_e")

    def get_ready_nodes(self) -> List[str]:
        print("# 실행 가능한 노드 찾기")
        ready_nodes = []
        for node_id, node in self.dag["nodes"].items():
            print(f" - {node_id} : {node.get('type')}, {node.get('role')}")
            if (node_id not in self.completed and node_id not in self.failed
                    and all(dep in self.completed for dep in node["dependencies"])):
                ready_nodes.append(node_id)
        print(f" - {ready_nodes}")
        return ready_nodes


# 재시도 로직을 포함한 버전
class APIWorkflowExecutorWithRetry(APIWorkflowExecutor):
    def execute_api_request(self, node: Dict, input_data: Dict = None):
        """재시도 로직이 포함된 API 요청"""
        config = node["config"]["api"]
        retry_config = config.get("retry", {})
        max_attempts = retry_config.get("maxAttempts", 3)
        backoff = retry_config.get("backoff", "exponential")

        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    url=config.get("url", f"http://api.example.com/{node['id']}"),
                    json=input_data,
                    timeout=config["timeout"] / 1000
                )
                return response.json()

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise

                # 지수 백오프 계산
                if backoff == "exponential":
                    wait_time = (2 ** attempt) * 1.0  # 1, 2, 4, 8... 초
                else:
                    wait_time = 1.0  # 고정 대기 시간

                time.sleep(wait_time)



# 사용 예시
def main():
    # 기본 사용
    config_dir = 'DAG'
    dag_filename = 'dag.json'
    loader = DAGLoader(config_dir)
    dag = loader.load_dag(dag_filename)

    # # 고급 사용
    # manager = WorkflowDAGManager(config_dir)
    #
    # # DAG 로드
    # dag1 = manager.get_dag(dag_filename)
    #
    # # 사용 가능한 모든 DAG 확인
    # available_dags = manager.get_available_dags()
    # print(f"사용 가능한 DAG 목록: {available_dags}")
    #
    # # 특정 DAG 새로고침
    # updated_dag = manager.get_dag(dag_filename, refresh=True)
    #
    # # 모든 DAG 새로고침
    # manager.reload_all()

    workflow = APIWorkflowExecutorWithRetry(dag, max_workers=3)
    result = workflow.execute()
    return result


if __name__ == "__main__":
    main()