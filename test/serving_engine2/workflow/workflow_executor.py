#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
import traceback
import asyncio
import aiohttp


class WorkflowExecutor:
    def __init__(self, logger, workflow_config: dict):
        self._logger = logger
        self.workflow = workflow_config
        self.session = None
        self.results = {}


    async def _execute_start_api_call(self, node_id: str, config: dict, input_data: dict) -> dict:
        """모든 노드에 대한 API 호출을 처리하는 통합 메서드"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        api_config = config['api']
        url = f"{api_config['url']}{api_config['route']}"

        params = {
            "node_id": node_id,
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
            self._logger.debug(f" - task completed successfully: {node_id}")
            return {"status": "success", "result": result}


    async def _execute_task_api_call(self, node_id: str, config: dict, input_data: dict, request_id: str) -> dict:
        """모든 노드에 대한 API 호출을 처리하는 통합 메서드"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        api_config = config['api']
        url = f"{api_config['url']}{api_config['route']}"

        params = {
            "node_id": node_id,
            "input_data": input_data,
            "request_id": request_id
        }

        self._logger.warn(f"- INSERT[{node_id}] - {input_data}")

        async with self.session.post(url, json=params, timeout=api_config['timeout'] / 1000) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"API call failed with status {response.status}: {error_text}")

            result = await response.json()
            self._logger.debug(f" - task completed successfully: {node_id}")
            return {"status": "success", "result": result}


    async def _execute_sequence_node(self, node_id: str) -> dict:
        """단일 노드 실행"""
        self._logger.critical("-" * 40)
        self._logger.critical(f"\t\t {node_id}\t\t        ")
        self._logger.critical("-" * 40)

        node = self.workflow['nodes'][node_id]

        self._logger.debug(f" - collect results from dependency nodes: {node_id}")
        input_data = {dep: self.results.get(dep, {}) for dep in node['dependencies']}
        if input_data:
            params_map = {}
            for tar_node_id, result_map in input_data.items():
                self._logger.debug(result_map)
                status = result_map['status']
                if status != 'success':
                    error = result_map['error']
                    raise Exception(f"{tar_node_id} 실행 실패: {error}")
                else:
                    result = result_map['result']
                    params_map[tar_node_id] = result['data']

        self._logger.debug(f" - execute task: {node_id}")
        node_type = node['type']

        if node_type == 'start':
            result = await self._execute_start_api_call(node_id, node['config'], input_data)
            self.request_id = result['result']['request_id']

        elif node_type == 'task':
            result = await self._execute_task_api_call(node_id, node['config'], params_map, self.request_id)

        else:
            result = "END"
        self._logger.warn(f"- RESULT[{node_id}] - {result}")

        # if type(result) == list:
        #     self.results[node_id] = result
        # else:
        #     self.results[node_id] = [result]
        # return result
        self.results[node_id] = result
        return result

    async def _execute_parallel_tasks(self, tasks: List[str]) -> None:
        if not tasks:
            return

        # self._logger.debug(f" - executing parallel tasks: {tasks}")
        async_tasks = [self._execute_sequence_node(task_id) for task_id in tasks]

        self._logger.debug(f" - parallel task result: {async_tasks}")
        await asyncio.gather(*async_tasks)

    async def execute_workflow(self) -> Dict[str, Any]:
        try:
            self._logger.info("# Step 2-1: set dependency levels")
            dependency_levels: Dict[int, List[str]] = {}
            # visited = set()

            def get_node_level(node_id: str, level: int = 0):
                # if node_id in visited:
                #     return
                # visited.add(node_id)
                #
                dependency_levels.setdefault(level, []).append(node_id)
                node = self.workflow['nodes'][node_id]

                for next_node in node['next']:
                    get_node_level(next_node, level + 1)

            self._logger.info("# Step 2-2: run start node")
            start_node = next(node_id for node_id, node in self.workflow['nodes'].items() if node['type'] == 'start')
            get_node_level(start_node)

            self._logger.info("# Step 2-3: run by node level")
            for level in sorted(dependency_levels.keys()):
                level_nodes = dependency_levels[level]
                self._logger.info("-" * 100)
                self._logger.info("# Step 2-3.1: set node classification as parallel/sequence")
                self._logger.error(f"executing level {level} nodes: {level_nodes}")
                parallel_nodes = []
                sequential_nodes = []


                for node_id in level_nodes:
                    node = self.workflow['nodes'][node_id]
                    if node.get('config', {}).get('parallel', {}).get('enabled', False):
                        parallel_nodes.append(node_id)
                    else:
                        sequential_nodes.append(node_id)

                self._logger.info("# Step 2-3.2: execute parallel tasks ")
                if parallel_nodes:
                    self._logger.error(f" - task nodes: {parallel_nodes}")
                    await self._execute_parallel_tasks(parallel_nodes)

                self._logger.info("# Step 2-3.3: execute sequence tasks")
                for node_id in sequential_nodes:
                    self._logger.error(f" - task node: {node_id}")
                    await self._execute_sequence_node(node_id)

            return self.results

        except Exception as e:
            self._logger.error(f"Workflow execution error: {str(e)}\n{traceback.format_exc()}")
            return {"status": "error", "error": str(e)}

        finally:
            if self.session:
                await self.session.close()



