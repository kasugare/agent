#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.data.cached_io_data_access import CachedIODataAccess

class DataIoController:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        self._logger = logger
        self._data_access = CachedIODataAccess(logger)

    def get_params(self, service_id):
        data_map = self._data_access.get(service_id)
        params = data_map.get('input')
        return params

    def get_result(self, service_id):
        data_map = self._data_access.get(service_id)
        result = data_map.get('output')
        return result

    def set_service_params(self, service_id, params):
        node_io_data_map = self._data_access.get(service_id)

        if node_io_data_map:
            input_node_data_map = node_io_data_map.get('input')
            if input_node_data_map:
                input_node_data_map.update(params)
            else:
                input_node_data_map = {"intput": params}
            node_io_data_map.update(input_node_data_map)
        else:
            node_io_data_map = {"input": params}
        self._data_access.set(service_id, node_io_data_map)

    def set_service_result(self, service_id, result):
        node_io_data_map = self._data_access.get(service_id)
        if node_io_data_map:
            output_node_data_map = node_io_data_map.get('output')
            if output_node_data_map:
                output_node_data_map.update(result)
            else:
                output_node_data_map = {"output": result}
            node_io_data_map.update(output_node_data_map)
        else:
            node_io_data_map = {"output": result}
            self._data_access.set(service_id, node_io_data_map)

    def get_result_value_by_service_io_id(self, service_io_id):
        splited_service_io_id = service_io_id.split('.')
        service_id = ".".join(splited_service_io_id[:2])
        key_name = splited_service_io_id[-1]
        output_data_map = self.get_result(service_id)
        if output_data_map:
            output_value = output_data_map.get(key_name)
            return output_value
        return None

    def get_data_pool(self):
        data_pool = self._data_access.get_all()
        return data_pool
