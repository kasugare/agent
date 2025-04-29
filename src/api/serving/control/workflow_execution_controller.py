#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Queue
from typing import Dict, List, Any
from api.serving.executor.task_executor import TaskExecutor
import threading


class WorkflowExecutionController:
    def __init__(self, logger, meta_pack):
        self._logger = logger
        self._node_info = meta_pack["nodes_info"]
        self._service_pool = meta_pack["service_pool"]
        self._edges_info = meta_pack["edges_info"]
        self._edges_grape = meta_pack["edges_grape"]
        self._prev_edges_grape = meta_pack["prev_edges_grape"]
        self._start_node = meta_pack["start_node"]
        self._executorQ = Queue()

        self._input_params_map = {}
        self._output_result_map = {}
        self._result_map = {}

    def _set_input_params(self, node_service_id: str, input_params: Dict) -> None:
        if not input_params:
            input_id = f"{node_service_id}"
            self._input_params_map[input_id] = None
        else:
            for param_name, value in input_params.items():
                input_id = f"{node_service_id}.{param_name}"
                self._input_params_map[input_id] = value

    def _set_output_result(self, node_service_id, result):
        service_info = self._service_pool.get(node_service_id)
        result_meta = service_info["result"]
        output_list = result_meta['output']
        for output_info in output_list:
            output_key = output_info['key']
            value = result.get(output_key)
            output_id = f"{node_service_id}.{output_key}"
            self._output_result_map[output_id] = value


    def _set_result(self, result_map):
        node_id = result_map['node_id']
        result = result_map['result']
        node_result_map = self._result_map[node_id]
        node_result_map['result'] = result
        node_result_map['status'] = 'success'
        node_info = self._result_map[node_id]
        thread = node_info['thread_info']['thread']
        node_info['thread_info']['thread_status'] = thread.is_alive()
        return node_id

    def _is_completed_all_jobs(self, nodes_meta: Dict) -> bool:
        if set(nodes_meta.keys()) == set(self._result_map.keys()):
            return True
        else:
            return False

    def _is_completed_prev_job(self, prev_node_ids: List) -> bool:
        for prev_node_id in prev_node_ids:
            if self._result_map.get(prev_node_id):
                node_result_map = self._result_map[prev_node_id]
                if node_result_map['status'] is not 'success':
                    return False
            else:
                return False
        return True

    def execute_job(self, node_id: str, nodes_meta: Dict) -> None:
        self._logger.debug(f"# Assigned execution task: {node_id}")

        def run_task(logger: Any, executorQ: Any, node_id: str, dag_meta: Dict) -> None:
            executor = TaskExecutor(logger)
            result = executor.run(node_id, dag_meta)
            result_map = {
                'node_id': node_id,
                'result': result
            }
            executorQ.put_nowait(result_map)
            self._logger.warn(f"# Finished Task: {node_id}")

        dag_meta = nodes_meta[node_id]
        thread = threading.Thread(target=run_task, args=(self._logger, self._executorQ, node_id, dag_meta))
        thread.start()

        task_map = {
            'thread_info': {
                'thread': thread,
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            },
            'status': 'wait',
            'result': None
        }
        self._result_map[node_id] = task_map

    def valid_start_input_params(self, request_params):
        try:
            service_info = self._service_pool.get(self._start_node)
            params_list = service_info['params']['input']
            params_keys = [params_map['key'] for params_map in params_list if params_map.get('required')]
            set_req_params = set(request_params.keys())
            set_src_params = set(params_keys)
            if set_src_params.intersection(set_req_params) == set_src_params:
                return True
            else:
                return False
        except Exception as e:
            self._logger.error(e)

    def _cvt_edge_id(self, src_id: str, tar_id: str) -> str:
        edge_id = f"{src_id}_{tar_id}"
        return edge_id

    def start_job_order(self, params):
        node_service_id = self._start_node
        self._set_input_params(node_service_id, params)
        self._set_output_result(node_service_id, params)
        node_service_ids = self._dag_grape.get(node_service_id)
        for next_node_service_id in node_service_ids:
            edge_id = self._cvt_edge_id(node_service_id, next_node_service_id)
            edge_info = find_next_edge_info(next_node_service_id)

            self.set_job_orders(next_node_service_id, params_map)

    def set_job_orders(self, node_ids: List, dag_meta: Dict) -> None:
        for node_id in self._start_nodes:
            node_info = dag_meta[node_id]
            node_role = node_info['role']

            self._logger.debug(f"{node_id} - {node_role}")

            if node_role == 'result-aggregator':
                prev_node_ids = node_info['prev_nodes']
                if self._is_completed_prev_job(prev_node_ids):
                    self.execute_job(node_id, dag_meta)
                else:
                    continue
            else:
                self.execute_job(node_id, dag_meta)

    def clear_result_map(self) -> None:
        self._result_map.clear()
        # self._executorQ.close()
        # self._executorQ = Queue()

    def run_result_handler(self, nodes_meta: Dict, edge_map: Dict) -> Dict:
        while True:
            result_map = self._executorQ.get()
            node_id = self._set_result(result_map)
            if node_id in edge_map:
                next_nodes = edge_map[node_id]
            else:
                next_nodes = None

            if self._is_completed_all_jobs(nodes_meta):
                break

            if next_nodes:
                self.set_job_orders(next_nodes, nodes_meta)

        for node_id, node_result in self._result_map.items():
            self._logger.debug(f"{node_id} - {node_result['result']}")
        return self._result_map
