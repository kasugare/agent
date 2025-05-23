import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any
import traceback
from pathlib import Path
import os
import time


class WorkflowExecutor:
    def __init__(self, workflow_config: dict):
        self.workflow = workflow_config
        self.session = None
        self.results = {}
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('WorkflowExecutor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _execute_start_api_call(self, node_id: str, config: dict, input_data: dict) -> dict:
        """모든 노드에 대한 API 호출을 처리하는 통합 메서드"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        api_config = config['api']
        url = f"{api_config['url']}{api_config['route']}"
        print(f"   = url: {url}")

        retry_config = api_config.get('retry', {'maxAttempts': 1})
        max_attempts = retry_config.get('maxAttempts', 1)

        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Executing node {node_id} - Attempt {attempt + 1}/{max_attempts}")
                params = {
                    "workflow_id": "workflow_"+node_id,
                    "input_data": input_data
                }
                async with self.session.post(
                        url,
                        json=params,
                        timeout=api_config['timeout'] / 1000
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")

                    result = await response.json()
                    self.logger.info(f"Node {node_id} completed successfully")
                    return {"status": "success", "result": result}

            except Exception as e:
                self.logger.error(f"Error in node {node_id}: {str(e)}")
                if attempt == max_attempts - 1:
                    return {"status": "error_pool", "error_pool": str(e)}

                # Exponential backoff
                if retry_config.get('backoff') == 'exponential':
                    backoff_time = 2 ** attempt
                    self.logger.info(f"Retrying node {node_id} in {backoff_time} seconds")
                    await asyncio.sleep(backoff_time)

    async def _execute_task_api_call(self, node_id: str, config: dict, input_data: dict, request_id: str) -> dict:
        """모든 노드에 대한 API 호출을 처리하는 통합 메서드"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        api_config = config['api']
        url = f"{api_config['url']}{api_config['route']}"

        retry_config = api_config.get('retry', {'maxAttempts': 1})
        max_attempts = retry_config.get('maxAttempts', 1)

        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Executing node {node_id} - Attempt {attempt + 1}/{max_attempts}")
                params = {
                    "workflow_id": "workflow_" + node_id,
                    "input_data": input_data,
                    "request_id": request_id
                }
                async with self.session.post(
                        url,
                        json=params,
                        timeout=api_config['timeout'] / 1000
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")

                    result = await response.json()
                    self.logger.info(f"Node {node_id} completed successfully")
                    return {"status": "success", "result": result}

            except Exception as e:
                self.logger.error(f"Error in node {node_id}: {str(e)}")
                if attempt == max_attempts - 1:
                    return {"status": "error_pool", "error_pool": str(e)}

                # Exponential backoff
                if retry_config.get('backoff') == 'exponential':
                    backoff_time = 2 ** attempt
                    self.logger.info(f"Retrying node {node_id} in {backoff_time} seconds")
                    await asyncio.sleep(backoff_time)

    async def _execute_node(self, node_id: str) -> dict:
        """단일 노드 실행"""
        print("-" * 40)
        print("\t\t", node_id)
        print("-" * 40)

        node = self.workflow['nodes'][node_id]

        print(f" - (1) 의존성 노드들의 결과 수집: {node_id}")
        input_data = {dep: self.results.get(dep, {}) for dep in node['dependencies']}
        if input_data:
            print("### INPUT", input_data)
            params_map = {}
            for tar_node_id, result_map in input_data.items():
                print(result_map)
                status = result_map['status']
                if status is not 'success':
                    error = result_map['error_pool']
                    raise Exception(f"{tar_node_id} 실행 실패: {error}")
                else:
                    result = result_map['result']
                    params_map[tar_node_id] = result['data']

        print(f" - (2) 노드 실행: {node_id}")
        node_type = node['type']

        if node_type == 'start':
            result = await self._execute_start_api_call(node_id, node['config'], input_data)
            self.request_id = result['result']['request_id']
            print("=========", result)
        elif node_type == 'task':
            print(node_id, params_map)
            result = await self._execute_task_api_call(node_id, node['config'], params_map, self.request_id)
            print("=========", result)
        else:
            print(node_type)
            result = "END"

        self.results[node_id] = result
        return result

    async def _execute_parallel_tasks(self, tasks: List[str]) -> None:
        """ - 병렬 처리가 필요한 태스크들 실행"""
        if not tasks:
            return

        # self.logger.info(f"Executing parallel tasks: {tasks}")
        print(f" - (1) 병렬 처리 태스크: {tasks}")
        async_tasks = [self._execute_node(task_id) for task_id in tasks]
        print(f" - (2) 병렬 처리 결과: {async_tasks}")
        await asyncio.gather(*async_tasks)

    async def execute_workflow(self) -> Dict[str, Any]:
        #"워크플로우 실행"
        try:
            print("# Step 2-1: 의존성 레벨 구성")
            dependency_levels: Dict[int, List[str]] = {}
            visited = set()

            def get_node_level(node_id: str, level: int = 0):
                if node_id in visited:
                    return
                visited.add(node_id)

                dependency_levels.setdefault(level, []).append(node_id)
                node = self.workflow['nodes'][node_id]

                for next_node in node['next']:
                    get_node_level(next_node, level + 1)

            print("# Step 2-2: 시작 노드부터 실행")
            start_node = next(node_id for node_id, node in self.workflow['nodes'].items() if node['type'] == 'start')
            get_node_level(start_node)

            print("# Step 2-3: 레벨별 노드 실행")
            for level in sorted(dependency_levels.keys()):
                level_nodes = dependency_levels[level]
                self.logger.info(f"Executing level {level} nodes: {level_nodes}")

                print("# Step 2-3.1: 병렬/순차 실행 노드 분류")
                parallel_nodes = []
                sequential_nodes = []

                for node_id in level_nodes:
                    node = self.workflow['nodes'][node_id]
                    if node.get('config', {}).get('parallel', {}).get('enabled', False):
                        parallel_nodes.append(node_id)
                    else:
                        sequential_nodes.append(node_id)

                print("# Step 2-3.1: 병렬 노드 실행")
                if parallel_nodes:
                    await self._execute_parallel_tasks(parallel_nodes)

                print("# Step 2-3.3: 순차 노드 실행")
                for node_id in sequential_nodes:
                    await self._execute_node(node_id)

            return self.results

        except Exception as e:
            self.logger.error(f"Workflow execution error_pool: {str(e)}\n{traceback.format_exc()}")
            return {"status": "error_pool", "error_pool": str(e)}

        finally:
            if self.session:
                await self.session.close()


class DAGLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir

    def load_dag(self, filename: str) -> Dict:
        print("# JSON 파일에서 DAG 설정을 로드")
        try:
            file_path = self. _get_file_path(filename)
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



# 사용 예제
async def run_workflow():
    print("# Step 0: 워크플로우 설정 로드")
    config_dir = 'DAG'
    dag_filename = 'dag.json'
    loader = DAGLoader(config_dir)
    workflow_config = loader.load_dag(dag_filename)

    print("# Step 2: 워크플로우 설정 로드")
    executor = WorkflowExecutor(workflow_config)
    results = await executor.execute_workflow()

    print("# Step 3: 워크플로우 실행 결과")
    print(json.dumps(results, indent=2))


# 메인 실행
if __name__ == "__main__":
    asyncio.run(run_workflow())