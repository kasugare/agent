#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .task_executor import TaskExecutor
from multiprocessing import Process, Queue
from typing import Dict, List, Any
import threading
import copy


class WorkflowManager:
    def __init__(self, logger):
        self._logger = logger
        self._graph = None
        # self._nodes_meta = None
        self._threadQ = Queue()
        self._result_map = {}


    def set_meta(self, nodes_meta):
        self._nodes_meta = copy.deepcopy(nodes_meta)

    def set_graph(self, graph):
        self._graph = copy.deepcopy(graph)

    def _set_result(self, result_map):
        node_id = result_map['node_id']
        result = result_map['result']
        node_result_map = self._result_map[node_id]
        node_result_map['result'] = result
        node_result_map['status'] = 'success'
        node_info = self._result_map[node_id]
        thread = node_info['thread_info']['thread']
        node_info['thread_info']['thread_status'] = thread.is_alive()
        # self._logger.warn(self._result_map)
        return node_id


    def _run_result_handler(self, nodes_meta):
        while True:
            result_map = self._threadQ.get()
            node_id = self._set_result(result_map)
            if node_id in self._graph:
                next_nodes = self._graph[node_id]
            else:
                next_nodes = None
            # next_nodes = self._graph.get_next_nodes(node_id)

            # self._logger.error_pool(f" - {node_id} --> {next_nodes}")

            if self._is_completed_all_jobs(nodes_meta):
                self._logger.critical("COMPLETED")
                break

            if next_nodes:
                self._set_job_orders(next_nodes, nodes_meta)

        for node_id, node_result in self._result_map.items():
            self._logger.debug(f"{node_id} - {node_result['result']}")
        return self._result_map


    def _run_process(self, logger: Any, thread_q: Any, node_id: str, node_meta: Dict) -> None:
        self._logger.warn(f"# Run Task: {node_id}")
        executor = TaskExecutor(logger, thread_q)
        result = executor.run(node_id, node_meta)
        result_map = {
            'node_id': node_id,
            'result': result
        }
        self._logger.warn(f"# Finished Task: {node_id}")
        thread_q.put_nowait(result_map)

    def _set_job_order(self, node_id, nodes_meta):
        self._logger.debug(f"# Assigned execution task: {node_id}")
        node_meta = nodes_meta[node_id]
        thread = threading.Thread(target=self._run_process, args=(self._logger, self._threadQ, node_id, node_meta))
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

    def _is_completed_all_jobs(self, nodes_meta):
        self._logger.critical("CHECK")
        print(" - 1:", set(nodes_meta.keys()))
        print(" - 2:", set(self._result_map.keys()))
        if set(nodes_meta.keys()) == set(self._result_map.keys()):
            return True
        else:
            return False

    def _is_completed_prev_job(self, prev_node_ids):
        for prev_node_id in prev_node_ids:
            if self._result_map.get(prev_node_id):
                node_result_map = self._result_map[prev_node_id]
                if node_result_map['status'] is not 'success':
                    return False
            else:
                return False
        return True

    def _set_job_orders(self, node_ids, nodes_meta):
        """ Node Type/Role 별 실행 유형 결정 """
        for node_id in node_ids:
            node_meta = nodes_meta[node_id]
            node_role = node_meta['role']

            self._logger.debug(f"{node_id} - {node_role}")

            if node_role == 'result-aggregator':
                prev_node_ids = node_meta['prev_nodes']
                if self._is_completed_prev_job(prev_node_ids):
                    self._set_job_order(node_id, node_meta)
                else:
                    continue
            else:
                self._set_job_order(node_id, node_meta)

    def run_workflow(self, node_meta, node_graph, start_node_ids):
        self._node_meta = node_meta
        self._graph = node_graph

        # start_node_ids = self._graph.find_start_nodes()
        for node_id in start_node_ids:
            self._set_job_order(node_id, node_meta)
        result = self._run_result_handler(node_meta)
        return result