#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.error_pool.error import NotPreparedPrevJob
from api.workflow.control.data.type_transfer import DataTypeTransfer
from api.workflow.control.data.data_io_controller import DataIoController
from api.workflow.control.data.metastore_controller import MetastoreController
from typing import Dict

class DataStoreService: # NodeDataService
    def __init__(self, logger):
        self._logger = logger
        self._type_casting = DataTypeTransfer(logger)
        self._data_controller = DataIoController(logger)
        self._metastore_controller = MetastoreController(logger)

    def _extract_param_name(self, key_path):
        param_name = key_path.split('.')[-1]
        return param_name

    def set_service_params(self, service_id: str, params: dict) -> bool:
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_params(service_id, params)

    def set_service_result(self, service_id: str, result: dict) -> bool:
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_result(service_id, result)

    def get_service_params(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        params = {}
        return params

    def get_service_result(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        result = {}
        return result

    def get_value_by_service_io_id(self, service_io_id: str):
        """ service_io_id = {node_id}.{service_name}.{parma/result}_name """
        value = self._data_controller.get_result_value_by_service_io_id(service_io_id)
        return value

    def get_next_service_params(self, edge_info: dict) -> dict:
        data_mapper = edge_info.get('data_mapper')
        value_params = {}
        for param_meta in data_mapper:
            call_method = param_meta.get('call_method')
            key_path = param_meta.get('key')
            value_path = param_meta.get('value')
            src_data_type = param_meta.get('key_type')
            tar_data_type = param_meta.get('value_type')
            param_name = self._extract_param_name(key_path)

            if call_method.lower() == 'refer':
                try:
                    value = self._data_controller.get_result_value_by_service_io_id(value_path)
                    type_casting_value = self._type_casting.trans_data_type(value, src_data_type, tar_data_type)
                    value_params[param_name] = type_casting_value
                except Exception as e:
                    raise NotPreparedPrevJob
            elif call_method.lower() == 'value':
                type_casting_value = self._type_casting.trans_data_type(value_path, src_data_type, tar_data_type)
                value_params[param_name] = type_casting_value
            else:
                pass
        return value_params

    def get_service_data_pool(self) -> Dict:
        data_pool = self._data_controller.get_data_pool()
        return data_pool

    def set_meta_pack(self, wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                  wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_nodes, end_nodes):
        self._metastore_controller.set_metas(wf_comm_meta, wf_nodes_meta, wf_service_pool, wf_edges_meta,
                  wf_edges_grape, wf_prev_edge_grape, wf_resources_meta, start_nodes, end_nodes)

    def get_meta_pack(self) -> Dict:
        meta_pack = self._metastore_controller.get_metas()
        return meta_pack

    def set_wf_meta(self, wf_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._metastore_controller.save_wf_meta_on_file(wf_meta, dirpath, filename)

    def get_wf_meta_file(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._metastore_controller.load_wf_meta_on_file()
        return wf_meta
