#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.task.task_service_access_controller import TaskServiceAccessController
from api.workflow.control.task.task_store_access_controller import TaskStoreAccessController
from datetime import datetime, timezone, timedelta
from functools import wraps
import traceback
import time


class TaskStoreController:
    def __init__(self, logger, cache_key=None):
        self._logger = logger
        self._task_service_access = TaskServiceAccessController(logger, cache_key).get_task_access_instance()
        self._task_store_access = TaskStoreAccessController(logger, cache_key).get_task_access_instance()
        self._cache_key = cache_key
        if cache_key:
            self.set_cache_key_ctl(cache_key)

    def _gen_service_key(self, service_id):
        key = f"{self._cache_key}-{service_id}"
        return key

    def with_generated_key(func):
        @wraps(func)
        def wrapper(self, service_id, *args, **kwargs):
            key = self._gen_service_key(service_id)
            return func(self, key, *args, **kwargs)
        return wrapper

    def set_cache_key_ctl(self, cache_key):
        self._cache_key = cache_key
        self._task_store_access.set_cache_key_access(cache_key)
        self._task_service_access.set_cache_key_access(cache_key)

    def set_init_task_map_ctl(self, task_map):
        try:
            task_service_map ={
                "services": list(task_map.keys()),
                "assigned_ts": time.time(),
                "start_ts": 0.0,
                "end_ts": 0.0
            }
            self._task_service_access.set_init_data_access(task_service_map)

            for service_id, task in task_map.items():
                data_map = {
                    "duration_ts": task.get_duration(),
                    "assigned_ts": task.get_assigned_ts(),
                    "start_ts": task.get_start_ts(),
                    "end_ts": task.get_end_ts(),
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
                key = self._gen_service_key(service_id)
                self._task_store_access.set_mapping_data_access(key, data_map)
        except Exception as e:
            self._logger.error(traceback.print_exc())

    def set_workflow_start_ts(self):
        self._task_service_access.set_data_access("start_ts", time.time())

    def set_workflow_end_ts(self):
        self._task_service_access.set_data_access("end_ts", time.time())

    @with_generated_key
    def set_start_ts_clt(self, service_id):
        self._task_store_access.set_start_ts_access(service_id)

    @with_generated_key
    def set_end_ts_clt(self, service_id):
        self._task_store_access.set_end_ts_access(service_id)

    @with_generated_key
    def set_duration_ts_clt(self, service_id):
        start_ts = self._task_store_access.get_start_ts_access(service_id)
        end_ts = self._task_store_access.get_end_ts_access(service_id)
        duration_ts = end_ts - start_ts
        self._task_store_access.set_duration_ts_access(service_id, duration_ts)

    @with_generated_key
    def set_env_param_ctl(self, service_id, env_params):
        self._task_store_access.set_env_param_access(service_id, env_params)

    @with_generated_key
    def set_asset_param_ctl(self, service_id, asset_params):
        self._task_store_access.set_asset_param_access(service_id, asset_params)

    @with_generated_key
    def set_param_ctl(self, service_id, params):
        self._task_store_access.set_param_access(service_id, params)

    @with_generated_key
    def set_result_ctl(self, service_id, result):
        self._task_store_access.set_result_access(service_id, result)

    @with_generated_key
    def set_error_msg_ctl(self, service_id, error_msg):
        self._task_store_access.set_error_msg_access(service_id, error_msg)

    @with_generated_key
    def set_state_ctl(self, service_id, state):
        self._task_store_access.set_state_access(service_id, state)

    @with_generated_key
    def set_handler_ctl(self, service_id, handler):
        self._task_store_access.set_handler_access(service_id, handler)

    @with_generated_key
    def get_assigned_ts_ctl(self, service_id):
        return self._task_store_access.get_assigned_ts_access(service_id)

    @with_generated_key
    def get_start_ts_ctl(self, service_id):
        return self._task_store_access.get_start_ts_access(service_id)

    @with_generated_key
    def get_end_ts_ctl(self, service_id):
        return self._task_store_access.get_end_ts_access(service_id)

    @with_generated_key
    def get_env_params_ctl(self, service_id):
        return self._task_store_access.get_env_params_access(service_id)

    @with_generated_key
    def get_asset_params_ctl(self, service_id):
        return self._task_store_access.get_asset_params_access(service_id)

    @with_generated_key
    def get_params_ctl(self, service_id):
        return self._task_store_access.get_params_access(service_id)

    @with_generated_key
    def get_result_ctl(self, service_id):
        return self._task_store_access.get_result_access(service_id)

    @with_generated_key
    def get_error_msg_ctl(self, service_id):
        return self._task_store_access.get_error_msg_access(service_id)

    @with_generated_key
    def get_state_ctl(self, service_id):
        return self._task_store_access.get_state_access(service_id)

    @with_generated_key
    def get_handler_ctl(self, service_id):
        return self._task_store_access.get_handler_access(service_id)

    def get_task_status_ctl(self):
        service_ids = self._task_service_access.get_data_access("services")
        task_status_map = {}
        for service_id in service_ids:
            key = self._gen_service_key(service_id)
            status = self._task_store_access.get_state_access(key)
            task_status_map[service_id] = status
        return task_status_map

    def get_processing_time_ctl(self):
        def cvt_htime(timestamp, tz='utc9'):
            tz_code = timezone(timedelta(hours=9))
            htime = datetime.fromtimestamp(timestamp, tz=tz_code)
            htime = htime.strftime('%Y%m%d%H%M%S')
            return htime

        start_ts = self._task_service_access.get_data_access("start_ts")
        end_ts = self._task_service_access.get_data_access("end_ts")
        assigned_ts = self._task_service_access.get_data_access("assigned_ts")
        duration_ts = end_ts - start_ts

        processing_time = {
            "assigned_ts": assigned_ts,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "assigned_dt": cvt_htime(assigned_ts),
            "start_dt": cvt_htime(start_ts),
            "end_dt": cvt_htime(end_ts),
            "duration_ts": duration_ts
        }
        return processing_time

    def clear_ctl(self):
        self._task_store_access.clear_access()