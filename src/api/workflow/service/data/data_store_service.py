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

    def set_init_service_params(self, wf_edges_meta):
        self._data_controller.set_init_service_params_ctl(wf_edges_meta)

    def set_service_params(self, service_id: str, params_map: dict):
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_params_ctl(service_id, params_map)

    def set_service_result(self, service_id: str, result: dict):
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_result_ctl(service_id, result)

    def get_start_service_params(self, service_id: str) -> dict:
        wf_edges_meta = self.get_edges_meta()
        params = self._data_controller.get_start_service_params_ctl(service_id)
        return params

    def get_service_params(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        wf_edges_meta = self.get_edges_meta()
        params = self._data_controller.get_service_params_ctl(service_id, wf_edges_meta)
        return params

    def get_service_result(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        result = {}
        return result

    def get_service_data_pool(self) -> Dict:
        data_pool = self._data_controller.get_data_pool_ctl()
        return data_pool

    def get_service_info(self, service_id) -> Dict:
        data_pool = self.get_service_data_pool()
        service_node_info = data_pool.get(service_id)
        return service_node_info

    def set_comm_meta(self, wf_comm_meta):
        self._metastore_controller.set_comm_meta_ctl(wf_comm_meta)

    def set_nodes_meta(self, wf_nodes_meta):
        self._metastore_controller.set_nodes_meta_ctl(wf_nodes_meta)

    def set_node_service_pool(self, wf_service_pool):
        self._metastore_controller.set_node_service_pool_ctl(wf_service_pool)

    def set_edges_meta(self, wf_edges_meta):
        self._metastore_controller.set_edges_meta_ctl(wf_edges_meta)

    def get_edges_meta(self):
        wf_edges_meta = self._metastore_controller.get_edges_meta_ctl()
        return wf_edges_meta

    def set_edges_grape_meta(self, wf_edges_grape):
        self._metastore_controller.set_edges_grape_meta_ctl(wf_edges_grape)

    def set_prev_edge_grape_meta(self, wf_prev_edge_grape):
        self._metastore_controller.set_prev_edge_grape_meta_ctl(wf_prev_edge_grape)

    def set_resources_meta(self, wf_resources_meta):
        self._metastore_controller.set_resources_meta_ctl(wf_resources_meta)

    def set_start_nodes_meta(self, start_nodes):
        self._metastore_controller.set_start_nodes_meta_ctl(start_nodes)

    def set_end_nodes_meta(self, end_nodes):
        self._metastore_controller.set_end_nodes_meta_ctl(end_nodes)

    def get_meta_pack(self) -> Dict:
        meta_pack = self._metastore_controller.get_metas_ctl()
        return meta_pack

    def set_wf_meta(self, wf_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._metastore_controller.save_wf_meta_on_file(wf_meta, dirpath, filename)

    def get_wf_meta_file(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._metastore_controller.load_wf_meta_on_file()
        return wf_meta
