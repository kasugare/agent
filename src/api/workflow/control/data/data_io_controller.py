#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.data.cached_io_data_access import CachedIODataAccess
from api.workflow.error_pool.error import NotExistedData

class DataIoController:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        self._logger = logger
        self._data_access = CachedIODataAccess(logger)

    def set_init_service_params_ctl(self, wf_edges_meta):
        for edge_id, edge_meta in wf_edges_meta.items():
            service_id = edge_meta.get('target')
            params_info = edge_meta.get('params_info')
            for params_map in params_info:
                if params_map.get('refer_type') == 'direct':
                    param_name = params_map.get('key')
                    value = params_map.get('value')
                    self.set_service_params_ctl(service_id, params_map={param_name: value})

    def set_service_params_ctl(self, service_id, params_map: dict):
        self._set_data_ctl(service_id, params_map, io_type="I")

    def set_service_result_ctl(self, service_id, result):
        self._set_data_ctl(service_id, result, io_type='O')

    def _set_data_ctl(self, service_id, data_map, io_type):
        """ value_id = {io_type}.{service_id}.{param_name}"""
        if io_type not in ['I', 'O']:
            raise Exception

        for key_name, value in data_map.items():
            value_id = f"{io_type}.{service_id}.{key_name}"
            self._data_access.set_data(value_id, value)

    def get_start_service_params_ctl(self, service_id):
        params = {}
        data_pool = self._data_access.get_all()
        for key, value in data_pool.items():
            if key.find(f"I.{service_id}") == 0:
                params_name = key.split(".")[-1]
                params[params_name] = value
            elif key.find(f"O.{service_id}") == 0:
                params_name = key.split(".")[-1]
                params[params_name] = value
        return params

    def _get_service_value_ctl(self, key_name, io_type='O'):
        """ key_name = {node_id}.{service_name}.{param_name}
            value_id = {io_type}.{node_id}.{service_name}.{param_name}"""
        value_id = f"{io_type}.{key_name}"
        value = self._data_access.get_data(value_id)
        return value

    def get_service_params_ctl(self, service_id, wf_edges_meta):
        def _extract_param_name(key_name):
            return key_name.split('.')[-1]

        params = {}
        for edge_id, edge_meta in wf_edges_meta.items():
            if service_id != edge_id.split("-")[-1]:
                continue
            refer_params_info = edge_meta.get('params_info')
            for ref_param_map in refer_params_info:
                refer_type = ref_param_map.get('refer_type')
                key = ref_param_map.get('key')
                if refer_type.lower() == 'indirect':
                    ref_value_id = ref_param_map.get('value')
                    value = self._get_service_value_ctl(ref_value_id, io_type="O")
                else:
                    value = self._get_service_value_ctl(key, io_type="I")#ref_param_map.get('value')
                param_name = _extract_param_name(key)
                params[param_name] = value
        return params

    def get_data_pool_ctl(self):
        data_pool = self._data_access.get_all()
        return data_pool

    def get_param_value_control(self, value_id):
        param_value = self._data_access.get_data(value_id)
        return param_value

