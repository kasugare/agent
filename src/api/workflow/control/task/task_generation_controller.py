#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.execute.task import Task
from common.conf_system import getWorkflowTimeoutConfig


class TaskGenerationController:
    def __init__(self, logger, meta_pack):
        self._logger = logger
        self._meta_pack = meta_pack

    def _extract_processing_type_map(self):
        edges_info = self._meta_pack.get('edges_info')
        proc_type_map = {}
        for edge_id, edge_info in edges_info.items():
            splited_edge_id = edge_id.split('-')
            target_service_id = splited_edge_id[-1]
            target_handler = edge_info.get('target_handler')
            proc_type = target_handler.get('type')
            proc_type_map[target_service_id] = proc_type
        return proc_type_map

    def make_task_map(self, active_service_ids=[]):
        proc_type_map = self._extract_processing_type_map()
        task_map = {}
        service_pool = self._meta_pack.get('service_pool')
        if not active_service_ids:
            edges_param_map = self._meta_pack.get('edges_param_map')
            active_edge_ids = list(edges_param_map.keys())
            for service_id, service_info in service_pool.items():
                for active_edge_id in active_edge_ids:
                    if active_edge_id.find(service_id) > -1:
                        active_service_ids.append(service_id)

        active_service_ids = list(set(active_service_ids))
        timeout_config = getWorkflowTimeoutConfig()
        for active_service_id in active_service_ids:
            service_info = service_pool.get(active_service_id)
            proc_type = proc_type_map.get(active_service_id)
            if not proc_type:
                proc_type = 'sequence'
            task_obj = Task(self._logger, active_service_id, service_info, timeout_config, proc_type)
            task_obj.set_assigned_ts()
            task_map[active_service_id] = task_obj
        return task_map
