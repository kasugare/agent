#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.data.data_io_controller import DataIoController
from typing import Dict, Any


class DataStoreService:
    def __init__(self, logger, cache_key):
        self._logger = logger
        self._data_controller = DataIoController(logger, cache_key)

    def set_init_values(self, meta_pack):
        wf_edges_meta = meta_pack.get('edges_info')
        self.set_init_service_params_service(wf_edges_meta)

        wf_env_value_map = meta_pack.get('nodes_env_value_map')
        self.set_init_nodes_env_params_service(wf_env_value_map)

        wf_asset_value_map = meta_pack.get('nodes_env_value_map')
        self.set_init_nodes_asset_params_service(wf_asset_value_map)

    def clear(self):
        self._data_controller.clear_ctl()

    def clear_data(self):
        self._data_controller.clear_ctl()

    def set_cache_key_service(self, wf_key):
        self._data_controller.set_cache_key_ctl(wf_key)

    def set_init_nodes_env_params_service(self, nodes_env_value_map):
        self._data_controller.set_init_nodes_env_params_ctl(nodes_env_value_map)

    def set_init_nodes_asset_params_service(self, nodes_asset_value_map):
        self._data_controller.set_init_nodes_asset_params_ctl(nodes_asset_value_map)

    def set_init_service_params_service(self, wf_edges_meta):
        self._data_controller.set_init_service_params_ctl(wf_edges_meta)

    def set_service_params_service(self, service_id: str, params_map: dict):
        """ service_id = {node_id}.{service_name}"""
        if not params_map:
            return
        self._data_controller.set_service_params_ctl(service_id, params_map)

    def set_service_result_service(self, service_id: str, result: Any):
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_result_ctl(service_id, result)

    def get_start_service_params_service(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        params = self._data_controller.get_start_service_params_ctl(service_id)
        return params

    def get_service_data_pool_service(self) -> Dict:
        data_pool = self._data_controller.get_data_pool_ctl()
        return data_pool

    def get_param_value_service(self, value_id):
        param_value = self._data_controller.get_param_value_control(value_id)
        return param_value

    def get_env_value(self, value_id):
        env_value_id = f"E.{value_id}"
        return self.get_param_value_service(env_value_id)

    def get_asset_value(self, value_id):
        asset_value_id = f"A.{value_id}"
        return self.get_param_value_service(asset_value_id)

    def get_input_value(self, value_id):
        input_value_id = f"I.{value_id}"
        return self.get_param_value_service(input_value_id)

    def get_output_value(self, value_id):
        output_value_id = f"O.{value_id}"
        return self.get_param_value_service(output_value_id)

    def find_io_value_service(self, value_id):
        io_value = self._data_controller.find_io_value_control(value_id)
        return io_value

    def get_service_info_service(self, service_id) -> Dict:
        data_pool = self.get_service_data_pool_service()
        service_node_info = data_pool.get(service_id)
        return service_node_info
