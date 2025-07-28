#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.execute.start_executor import StartExecutor
from api.workflow.access.execute.end_executor import EndExecutor
from api.workflow.access.execute.api_executor import ApiExecutor
import time


class TaskContext:
    def __init__(self, logger, service_id, service_info):
        self._logger = logger
        self._service_info = service_info
        self._service_id = service_id
        self._task_id = self._gen_task_id()
        self._params_value_map = None
        self._executor = None
        self._conn_info = None

        self._init_context(service_info)

    def _init_context(self, service_info):
        self._task_type = service_info.get('type')
        self._role = service_info.get('role')
        self._node_type = service_info.get('node_type')
        self._location = service_info.get('location')
        # self._params_map = self._extract_params_map(edge_info)
        self._params_format = self._extract_params_format(service_info)
        self._result_format = self._extract_results_format(service_info)

        if self._node_type.lower() == 'rest-api':
            if self._role == 'start':
                self._set_start_executor()
            elif self._role == 'end':
                self._set_end_executor()
            else:
                self._conn_info = self._extract_api_info(service_info)
                self._set_api_executor(**self._conn_info)
        elif self._node_type.lower() == 'engine':
            if self._task_type.lower() == 'start_node':
                self._set_start_executor()
            else:
                self._conn_info = self._extract_api_info(service_info)
        else:
            self._conn_info = self._extract_api_info(service_info)
            self._set_api_executor(**self._conn_info)

        # self._print_service_info()

    def _gen_task_id(self):
        task_id = "%X" %(int(time.time()*10000000))
        return task_id

    def _extract_params_format(self, service_info):
        params_map = service_info.get('params')
        params_format = params_map.get('input')
        return params_format

    def _extract_results_format(self, result_info):
        result_map = result_info.get('result')
        result_format = result_map.get('output')
        return result_format

    def _extract_params_map(self, edge_info):
        self._logger.debug("f # Step 3. extract data_mapper")
        params_info = edge_info.get('params_info')
        params_map = {}
        for param_info in params_info:
            key_path = param_info.get('key')
            param_name = key_path.split('.')[-1]
            params_map[param_name] = param_info
        return params_map

    def _extract_api_info(self, node_info):
        url_info = {
            'url': node_info.get('url'),
            'method': node_info.get('method'),
            'header': node_info.get('header'),
            'body': node_info.get('body'),
            'api_keys': node_info.get('api_keys')
        }
        return url_info

    def _set_api_executor(self, url=None, method=None, header={}, body={}, api_keys=[]):
        self._executor = ApiExecutor(self._logger)
        self._executor.set_api(url=url, method=method, header=header, body=body)

    def _set_start_executor(self):
        self._executor = StartExecutor(self._logger)

    def _set_end_executor(self):
        self._executor = EndExecutor(self._logger)

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

    def get_result_format(self):
        return self._result_format

    def get_service_info(self):
        return self._service_info

    def _print_service_info(self):
        def print_params(params_format):
            for params_info in params_format:
                param_name = params_info.get('key')
                value_type = params_info.get('type')
                required = params_info.get('required')
                self._logger.debug(f"          L  [{required}] param_name: {param_name} ({value_type}) ")

        def print_result(results_format):
            for result_info in results_format:
                param_name = result_info.get('key')
                value_type = result_info.get('type')
                self._logger.debug(f"          L  param_name: {param_name} ({value_type}) ")

        def print_connection(conn_info):
            if not conn_info:
                return
            for k, v in conn_info.items():
                self._logger.debug(f"      L  {k}:\t{v}")

        self._logger.debug(f" - (common) task_type:\t {self._task_type}")
        self._logger.debug(f" - (common) role:    \t {self._role}")
        self._logger.debug(f" - (common) location:\t {self._location}")
        self._logger.debug(f" - (common) node_type:\t {self._node_type}")
        self._logger.debug(f" - (common) params_map")
        self._logger.debug(f" - (common) result_format")
        print_result(self._result_format)
        self._logger.debug(f" - (API) connection_info")
        # print_connection(self._conn_info)