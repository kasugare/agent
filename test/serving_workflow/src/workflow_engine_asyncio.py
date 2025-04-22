from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp


class APIWorkflowExecutor:
    def __init__(self, dag: Dict):
        self.dag = dag
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self.results: Dict[str, any] = {}
        self.session = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    def get_ready_nodes(self) -> List[str]:
        """실행 가능한 노드 목록 반환"""
        ready_nodes = []
        for node_id, node in self.dag["nodes"].items():
            if (node_id not in self.completed
                    and node_id not in self.failed
                    and all(dep in self.completed for dep in node["dependencies"])):
                ready_nodes.append(node_id)
        return ready_nodes

    async def execute_node(self, node_id: str):
        """개별 노드 실행"""
        node = self.dag["nodes"][node_id]
        try:
            if node["type"] == "start":
                # API 게이트웨이 역할
                result = await self.execute_api_request(node)
                self.results[node_id] = result

            elif node["type"] == "task":
                # 비즈니스 API 실행
                input_data = self.prepare_input_data(node)
                result = await self.execute_api_request(node, input_data)
                self.results[node_id] = result

            elif node["type"] == "end":
                # 결과 취합
                result = self.aggregate_results(node)
                self.results[node_id] = result

            self.completed.add(node_id)
            return True

        except Exception as e:
            self.failed.add(node_id)
            return False

    async def execute_api_request(self, node: Dict, input_data: Dict = None):
        """API 요청 실행"""
        config = node["config"]["api"]
        url = config.get("url", f"http://api.example.com/{node['id']}")

        async with self.session.post(url, json=input_data) as response:
            return await response.json()

    def prepare_input_data(self, node: Dict) -> Dict:
        """노드 실행에 필요한 입력 데이터 준비"""
        input_data = {}
        for dep in node["dependencies"]:
            input_data[dep] = self.results[dep]
        return input_data

    def aggregate_results(self, node: Dict) -> Dict:
        """최종 결과 취합"""
        result = {}
        for source in node["config"]["aggregation"]["sourceNodes"]:
            result.update(self.results[source])
        return result

    async def execute(self):
        """워크플로우 실행"""
        await self.init_session()

        try:
            while True:
                ready_nodes = self.get_ready_nodes()
                if not ready_nodes:
                    break

                # 병렬 실행 가능한 노드들 동시 실행
                tasks = [self.execute_node(node_id) for node_id in ready_nodes]
                await asyncio.gather(*tasks)

        finally:
            await self.close_session()

        # 최종 결과 반환
        return self.results.get("node_e")

    def add_monitoring(self):
        self.metrics = {
            "execution_time": {},
            "retry_count": {},
            "status": {}
        }

    async def execute_with_timeout(self, node_id):
        timeout = self.dag["nodes"][node_id]["config"]["api"]["timeout"]
        async with asyncio.timeout(timeout / 1000):
            return await self.execute_node(node_id)


# 사용 예시
async def main():
    workflow = APIWorkflowExecutor(dag)
    result = await workflow.execute()
    return result


if __name__ == "__main__":
    asyncio.run(main())