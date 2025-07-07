#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task import Task


class TaskGenerator:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._datastore = datastore
        self._meta_pack = datastore.get_meta_pack()
        self._node_graph = {}
        self._task_map = {}

    def get_edge_info(self, edge_id):
        edges_info = self._meta_pack.get('edges_info')
        edge_info = edges_info.get(edge_id)
        return edge_info

    def get_node_info(self, service_id):
        node_pool = self._meta_pack.get('service_pool')
        node_info = node_pool.get(service_id)
        return node_info

    def get_next_service_ids(self, service_id):
        edges_grape = self._meta_pack['edges_grape']
        next_service_ids = edges_grape.get(service_id)
        return next_service_ids

    def get_start_nodes(self):
        start_nodes = self._meta_pack['start_nodes']
        return start_nodes

    def add_task(self, service_id, node_info):
        task = Task(self._logger, self._datastore, service_id, node_info)
        self._task_map[service_id] = task

    def make_tasks(self, curr_service_ids=[]):
        if not curr_service_ids:
            curr_service_ids = self.get_start_nodes()
            for curr_service_id in curr_service_ids:
                node_info = self.get_node_info(curr_service_id)
                self.add_task(curr_service_id, node_info)

        for curr_service_id in curr_service_ids:
            next_service_ids = self.get_next_service_ids(curr_service_id)
            if not next_service_ids:
                return
            for task_service_id in next_service_ids:
                node_info = self.get_node_info(task_service_id)
                self.add_task(task_service_id, node_info)
                self.make_tasks([task_service_id])
        return self._task_map

    def get_task_map(self):
        return self._task_map
