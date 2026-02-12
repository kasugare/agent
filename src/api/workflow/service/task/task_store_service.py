#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.task.task_store_controller import TaskStoreController
from typing import Dict, Any


class TaskStoreService:
    def __init__(self, logger, cache_key=None):
        self._logger = logger
        self._task_store_ctl = TaskStoreController(logger, cache_key)

    def clear(self):
        self._task_store_ctl.clear_ctl()

    def clear_data(self):
        self._task_store_ctl.clear_ctl()

    def set_workflow_start_ts(self):
        self._task_store_ctl.set_workflow_start_ts()

    def set_workflow_end_ts(self):
        self._task_store_ctl.set_workflow_end_ts()

    def set_cache_key(self, cache_key):
        self._task_store_ctl.set_cache_key_ctl(cache_key)

    def set_init_task_map(self, task_map):
        self._task_store_ctl.set_init_task_map_ctl(task_map)

    def set_env_params(self, service_id, env_params):
        self._task_store_ctl.set_env_param_ctl(service_id, env_params)

    def set_asset_params(self, service_id, asset_params):
        self._task_store_ctl.set_asset_param_ctl(service_id, asset_params)

    def set_params(self, service_id, params):
        self._task_store_ctl.set_param_ctl(service_id, params)

    def set_result(self, service_id, result):
        self._task_store_ctl.set_result_ctl(service_id, result)

    def set_error_msg(self, service_id, result):
        self._task_store_ctl.set_error_msg_ctl(service_id, result)

    def set_state(self, service_id, state):
        self._task_store_ctl.set_state_ctl(service_id, state)

    def set_handler(self, service_id, handler):
        self._task_store_ctl.set_handler_ctl(service_id, handler)

    def set_start_ts(self, service_id):
        self._task_store_ctl.set_start_ts_clt(service_id)

    def set_end_ts(self, service_id):
        self._task_store_ctl.set_end_ts_clt(service_id)

    def set_duration_ts(self, service_id):
        self._task_store_ctl.set_duration_ts_clt(service_id)

    def get_assigned_ts(self, service_id):
        return self._task_store_ctl.get_assigned_ts_ctl(service_id)

    def get_start_ts(self, service_id):
        return self._task_store_ctl.get_start_ts_ctl(service_id)

    def get_end_ts(self, service_id):
        return self._task_store_ctl.get_end_ts_ctl(service_id)

    def get_env_params(self, service_id):
        return self._task_store_ctl.get_env_params_ctl(service_id)

    def get_asset_params(self, service_id):
        return self._task_store_ctl.get_asset_params_ctl(service_id)

    def get_params(self, service_id):
        return self._task_store_ctl.get_params_ctl(service_id)

    def get_result(self, service_id):
        return self._task_store_ctl.get_result_ctl(service_id)

    def get_error_msg(self, service_id):
        return self._task_store_ctl.get_error_msg_ctl(service_id)

    def get_state_(self, service_id):
        return self._task_store_ctl.get_state_ctl(service_id)

    def get_handler(self, service_id):
        return self._task_store_ctl.get_handler_ctl(service_id)

    def get_workflow_status(self):
        return self._task_store_ctl.get_task_status_ctl()

    def get_processing_time(self):
        return self._task_store_ctl.get_processing_time_ctl()
