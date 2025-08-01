#!/usr/bin/env python
# -*- coding: utf-8 -*-

from serving.workflow_execution_controller import WorkflowExecutionController
from typing import Dict


class WorkflowExecutionService:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._datastore = datastore
        self._meta_pack = datastore.get_meta_pack()
        self._service_pool = self._meta_pack["service_pool"]
        self._start_nodes = self._meta_pack["start_nodes"]
        self._engine_controller = WorkflowExecutionController(logger, self._meta_pack)

    def check_start_params(self, request_params):
        valid_params = self._engine_controller.valid_start_input_params(request_params)
        return valid_params

    def get_start_params(self):
        service_info = self._service_pool.get(self._start_nodes)
        if not service_info.get('params') or not service_info['params'].get('input'):
            return {}
        node_params = service_info['params']['input']
        return node_params

    def extract_params(self, src_params, node_params=None):
        def extract_required_params(node_params):
            req_params = []
            opt_params = []
            for param_info in node_params:
                if param_info.get('required'):
                    req_params.append(param_info.get('key'))
                else:
                    opt_params.append(param_info.get('key'))
            return req_params, opt_params

        if not node_params:
            node_params = self.get_start_params()

        req_params, opt_params = extract_required_params(node_params)
        input_params = {}
        for param_key in req_params:
            value = src_params[param_key]
            input_params[param_key] = value
        for param_key in opt_params:
            value = src_params.get(param_key)
            if value:
                input_params[param_key] = value
        return input_params

    def run_workflow(self, input_params) -> Dict:
        self._engine_controller.clear_result_map()
        self._engine_controller.start_job_order(input_params)
        # self._engine_controller.set_job_orders()
        result_map = self._engine_controller.run_result_handler()
        return result_map