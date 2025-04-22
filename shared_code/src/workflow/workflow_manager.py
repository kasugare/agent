#!/usr/bin/env python
# -*- coding: utf-8 -*-

from workflow.task_executor import TaskExecutor
from multiprocessing import Process, Queue
from typing import Dict, List, Any
import threading


class WorkflowManager:
    def __init__(self, logger, graph):
        self._logger = logger
        self._graph = graph
        self._threadQ = Queue()

        self._nodes_meta = None
        self._edge_meta = None
        self._result_map = {}

    def set_meta(self, nodes_meta, edge_meta):
        self._nodes_meta = nodes_meta
        self._edge_meta = edge_meta

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


    def _run_result_handler(self):
        while True:
            result_map = self._threadQ.get()
            node_id = self._set_result(result_map)
            next_nodes = self._graph.get_next_nodes(node_id)
            if self._is_completed_all_jobs():
                break

            self._set_job_orders(next_nodes)

        for node_id, node_result in self._result_map.items():
            self._logger.debug(f"{node_id} - {node_result['result']}")


    def _run_process(self, logger: Any, thread_q: Any, node_id: str, node_meta: Dict) -> None:
        self._logger.error(f"# Run Task: {node_id}")
        executor = TaskExecutor(logger, thread_q)
        result = executor.run(node_id, node_meta)
        result_map = {
            'node_id': node_id,
            'result': result
        }
        thread_q.put_nowait(result_map)

    def _set_job_order(self, node_id):
        self._logger.error(f"# Assigned execution task: {node_id}")
        node_meta = self._nodes_meta[node_id]
        thread = threading.Thread(target=self._run_process, args=(self._logger, self._threadQ, node_id, node_meta))
        thread.daemon = True
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

    def _is_completed_all_jobs(self):
        wait_nodes = set(self._nodes_meta.keys()).difference(set(self._result_map.keys()))

        if len(wait_nodes) == 0:
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

    def _set_job_orders(self, node_ids):
        """ Node Type/Role 별 실행 유형 결정 """
        for node_id in node_ids:
            self._logger.critical(node_id)
            node_meta = self._nodes_meta[node_id]
            node_role = node_meta['role']

            self._logger.debug(f"{node_id} - {node_role}")

            if node_role == 'result-aggregator':
                prev_node_ids = node_meta['prev_nodes']
                if self._is_completed_prev_job(prev_node_ids):
                    self._set_job_order(node_id)
                else:
                    continue
            else:
                self._set_job_order(node_id)

    def run_workflow(self):
        start_node_ids = self._graph.find_start_nodes()
        for node_id in start_node_ids:
            self._set_job_order(node_id)
        self._run_result_handler()