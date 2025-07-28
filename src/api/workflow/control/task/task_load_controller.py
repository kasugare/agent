#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task import Task


class TaskLoadController:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._datastore = datastore
        self._node_graph = {}

    def make_task_map(self, active_service_ids=[]):
        task_map = {}
        service_pool = self._datastore.get_node_service_pool_service()
        if not active_service_ids:
            edges_param_map = self._datastore.get_edges_param_map_service()
            active_edge_ids = list(edges_param_map.keys())
            for service_id, service_info in service_pool.items():
                for active_edge_id in active_edge_ids:
                    if active_edge_id.find(service_id) > -1:
                        active_service_ids.append(service_id)
        active_service_ids = list(set(active_service_ids))
        for active_service_id in active_service_ids:
            service_info = service_pool.get(active_service_id)
            task_obj = Task(self._logger, active_service_id, service_info)
            task_map[active_service_id] = task_obj
        return task_map
