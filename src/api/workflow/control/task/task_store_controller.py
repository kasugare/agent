#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.task.task_service_access_controller import TaskServiceAccessController
from api.workflow.control.task.task_store_access_controller import TaskStoreAccessController
import traceback


class TaskStoreController:
    def __init__(self, logger, cache_key=None):
        self._logger = logger
        self._task_service_access = TaskServiceAccessController(logger, cache_key).get_task_access_instance()
        self._task_store_access = TaskStoreAccessController(logger, cache_key).get_task_access_instance()
        self._cache_key = cache_key
        if cache_key:
            self.set_cache_key_ctl(cache_key)

    def set_cache_key_ctl(self, cache_key):
        self._cache_key = cache_key
        self._task_store_access.set_cache_key_access(cache_key)
        self._task_service_access.set_cache_key_access(cache_key)

    def set_init_task_map_ctl(self, task_map):
        try:
            service_ids = list(task_map.keys())
            self._task_service_access.set_data_access(field='services', data=service_ids)

            for service_id, task in task_map.items():
                data_map = {
                    "duration": task.get_duration(),
                    "start_dt": task.get_start_dt(),
                    "end_dt": task.get_end_dt(),
                    "task_service_id": task.get_service_id(),
                    "task_id": task.get_task_id(),
                    "task_role": task.get_task_type(),
                    "task_node_type": task.get_node_type(),
                    "service_info": task.get_service_info(),
                    "location": task.get_location(),
                    "params": task.get_params(),
                    "env_params": task.get_env_params(),
                    "asset_params": task.get_asset_params(),
                    "result": task.get_result(),
                    "error_msg": task.get_error(),
                    "state": task.get_state(),
                    "handler": task.get_handler()
                }
                self._task_store_access.set_mapping_data_access(service_id, data_map)
        except Exception as e:
            self._logger.error(traceback.print_exc())

    def set_env_param_ctl(self, service_id, env_params):
        self._task_store_access.set_env_param_access(service_id, env_params)

    def set_asset_param_ctl(self, service_id, asset_params):
        self._task_store_access.set_asset_param_access(service_id, asset_params)

    def set_param_ctl(self, service_id, params):
        self._task_store_access.set_param_access(service_id, params)

    def set_result_ctl(self, service_id, result):
        self._task_store_access.set_result_access(service_id, result)

    def set_error_msg_ctl(self, service_id, error_msg):
        self._task_store_access.set_error_msg_access(service_id, error_msg)

    def set_state_ctl(self, service_id, state):
        self._task_store_access.set_state_access(service_id, state)

    def set_handler_ctl(self, service_id, handler):
        self._task_store_access.set_handler_access(service_id, handler)

    def clear_ctl(self):
        self._task_store_access.clear_access()