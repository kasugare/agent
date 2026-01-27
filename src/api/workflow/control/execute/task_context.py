#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.execute.api_executor import ApiExecutor
from api.workflow.access.execute.start_executor import StartExecutor
from api.workflow.access.execute.end_executor import EndExecutor
from api.workflow.access.execute.conditional_executor import ConditionalExecutor
from api.workflow.access.execute.module_executor import ModuleExecutor
from api.workflow.error_pool.error import ExceedExecutionRetryError
import math
import time


class TaskContext:
    def __init__(self, logger, service_id, service_info, timeout_conf):
        self._logger = logger

        self._service_id = service_id
        self._service_info = service_info
        self._task_id = self._gen_task_id()

        self._conn_info = None
        self._location = None
        self._executor = None

        self._env_params = {}
        self._asset_params = {}
        self._params = {}
        self._result = None
        self._error = None
        self._state = None
        self._target_handler = {}

        self._init_context(service_info)
        self._init_timeout(timeout_conf)

    def _init_context(self, service_info):
        self._task_type = service_info.get('type')
        self._role = service_info.get('role')
        self._node_type = str(service_info.get('node_type')).lower()
        self._location = service_info.get('location')

        if self._node_type == 'rest-api':
            if self._role == 'start':
                self._set_start_executor()
            elif self._role == 'end':
                self._set_end_executor()
            else:
                self._conn_info = self._extract_api_info(service_info)
                self._set_api_executor(**self._conn_info)
        elif self._node_type == 'engine':
            if self._task_type.lower() == 'start_node':
                self._set_start_executor()
            else:
                self._conn_info = self._extract_module_info(service_info)
        elif self._node_type == 'module':
            if self._role == 'generation':
                self._conn_info = self._extract_module_info(service_info)
                self._set_class_executor(**self._conn_info)
            elif self._role == 'condition':
                self._set_conditional_executor()
            else:
                self._conn_info = self._extract_module_info(service_info)
                self._set_class_executor(**self._conn_info)
        else:
            self._conn_info = self._extract_api_info(service_info)
            self._set_api_executor(**self._conn_info)

    def _gen_task_id(self):
        task_id = "%X" %(int(time.time()*10000000))
        return task_id

    def _extract_api_info(self, service_info):
        api_info = service_info.get('api_info')
        route_path = service_info.get('function')
        url = f"{api_info.get('base_url')}{route_path}"
        conn_info = {
            'url': url,
            'method': api_info.get('method'),
            'header': service_info.get('header'),
            'body': service_info.get('body'),
            'api_keys': service_info.get('api_keys')
        }
        return conn_info

    def _extract_module_info(self, service_info):
        module_info = service_info.get('module_info')
        conn_info = {
            'module_path': module_info.get('module_path'),
            'class_name': module_info.get('class_name'),
            'function': service_info.get('function'),
            'api_keys': service_info.get('api_keys')
        }
        return conn_info

    def _set_api_executor(self, url=None, method=None, header={}, body={}, api_keys=[]):
        self._executor = ApiExecutor(self._logger, url, method, header, body)

    def _set_class_executor(self, module_path, class_name, function, api_keys=[]):
        self._executor = ModuleExecutor(self._logger, module_path, class_name, function)

    def _set_start_executor(self):
        self._executor = StartExecutor(self._logger)

    def _set_end_executor(self):
        self._executor = EndExecutor(self._logger)

    def _set_conditional_executor(self):
        self._executor = ConditionalExecutor(self._logger)

    def get_service_id(self):
        return self._service_id

    def get_task_id(self):
        return self._task_id

    def get_task_type(self):
        return self._task_type

    def get_role(self):
        return self._role

    def get_node_type(self):
        return self._node_type

    def get_service_info(self):
        return self._service_info

    def get_executor(self):
        return self._executor

    def get_location(self):
        return self._location

    def set_env_params(self, env_params=None):
        self._env_params = env_params
        executor = self.get_executor()
        executor.set_env(env_params)

    def set_asset_params(self, asset_params=None):
        self._asset_params = asset_params
        executor = self.get_executor()
        executor.set_asset(asset_params)

    def set_params(self, params=None):
        self._params = params

    def get_params(self):
        return self._params

    def get_env_params(self):
        return self._env_params

    def set_result(self, result):
        self._result = result

    def get_result(self):
        return self._result

    def set_error(self, error):
        self._error = error

    def get_error(self):
        return self._error

    def set_state(self, state):
        self._state = state

    def get_state(self):
        return self._state

    def set_handler(self, handler):
        self._target_handler = handler
        executor = self.get_executor()
        executor.set_target_handler(handler)

    def get_handler(self):
        return self._target_handler

    def _init_timeout(self, timeout_config):
        self._max_retries = timeout_config.get('max_retries', 3)
        self._timeout = timeout_config.get('timeout', 60.0)
        self._delay_time = timeout_config.get('delay_time', 3.0)
        self._exponential_backoff = timeout_config.get('exponential_backoff', True)
        self._retry_count = 0

    def init_retry_count(self):
        self._retry_count = 0

    def _increased_retry_count(self):
        self._retry_count += 1

    def get_current_retry_count(self):
        return self._retry_count

    def get_max_retries(self):
        return self._max_retries

    def sleep_delay(self):
        time.sleep(self._delay_time)

    def get_timeout(self):
        return self._timeout

    def get_exponential_backoff(self):
        return self._exponential_backoff

    def get_retry_timeout(self):
        self._increased_retry_count()

        curr_retry_cnt = self.get_current_retry_count()
        max_retry = self.get_max_retries()
        timeout = self.get_timeout()

        if curr_retry_cnt > max_retry:
           raise ExceedExecutionRetryError

        if self._exponential_backoff:
            timeout = math.pow(timeout, curr_retry_cnt)
            return timeout
        else:
            return timeout

