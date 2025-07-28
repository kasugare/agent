#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.error_pool.error import NotPreparedPrevJob
from api.workflow.control.data.type_transfer import DataTypeTransfer
from api.workflow.control.data.data_io_controller import DataIoController
from api.workflow.control.data.metastore_controller import MetastoreController
from api.workflow.control.data.task_pool_controller import TaskPoolController
from typing import Dict

class DataStoreService:
    def __init__(self, logger):
        self._logger = logger
        self._type_casting = DataTypeTransfer(logger)
        self._data_controller = DataIoController(logger)
        self._metastore_controller = MetastoreController(logger)
        self._taskpool_controller = TaskPoolController(logger)

    def _extract_param_name(self, key_path):
        param_name = key_path.split('.')[-1]
        return param_name

    def set_init_service_params_service(self, wf_edges_meta):
        self._data_controller.set_init_service_params_ctl(wf_edges_meta)

    def set_service_params_service(self, service_id: str, params_map: dict):
        """ service_id = {node_id}.{service_name}"""
        if not params_map:
            return
        self._data_controller.set_service_params_ctl(service_id, params_map)

    def set_service_result_service(self, service_id: str, result: dict):
        """ service_id = {node_id}.{service_name}"""
        self._data_controller.set_service_result_ctl(service_id, result)

    def get_start_service_params_service(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        params = self._data_controller.get_start_service_params_ctl(service_id)
        return params

    def get_service_params_service(self, service_id: str) -> dict:
        """ service_id = {node_id}.{service_name}"""
        wf_edges_meta = self.get_edges_meta_service()
        params = self._data_controller.get_service_params_ctl(service_id, wf_edges_meta)
        return params

    def get_service_data_pool_service(self) -> Dict:
        data_pool = self._data_controller.get_data_pool_ctl()
        return data_pool

    def get_param_value_service(self, value_id):
        param_value = self._data_controller.get_param_value_control(value_id)
        return param_value

    def get_service_info_service(self, service_id) -> Dict:
        data_pool = self.get_service_data_pool_service()
        service_node_info = data_pool.get(service_id)
        return service_node_info

    def set_comm_meta_service(self, wf_comm_meta):
        self._metastore_controller.set_comm_meta_ctl(wf_comm_meta)

    def set_nodes_meta_service(self, wf_nodes_meta):
        self._metastore_controller.set_nodes_meta_ctl(wf_nodes_meta)

    def set_node_service_pool_service(self, wf_service_pool):
        self._metastore_controller.set_node_service_pool_ctl(wf_service_pool)

    def get_node_service_pool_service(self):
        service_pool = self._metastore_controller.get_node_service_pool_ctl()
        return service_pool

    def set_edges_meta_service(self, wf_edges_meta):
        self._metastore_controller.set_edges_meta_ctl(wf_edges_meta)

    def get_edges_meta_service(self):
        wf_edges_meta = self._metastore_controller.get_edges_meta_ctl()
        return wf_edges_meta

    def get_edge_info_by_edge_id(self, edge_id):
        wf_edge_meta = self._metastore_controller.get_edge_meta_by_edge_id_ctl(edge_id)
        return wf_edge_meta

    def set_forward_edge_graph_meta_service(self, wf_forward_edge_edge_graph):
        self._metastore_controller.set_forward_edge_graph_meta_ctl(wf_forward_edge_edge_graph)

    def set_forward_graph_meta_service(self, wf_forward_edge_graph):
        self._metastore_controller.set_forward_graph_meta_ctl(wf_forward_edge_graph)

    def get_forward_graph_meta_service(self):
        return self._metastore_controller.get_forward_graph_meta_ctl()

    def set_backward_graph_meta_service(self, wf_backward_edge_graph):
        self._metastore_controller.set_backward_graph_meta_ctl(wf_backward_edge_graph)

    def get_backward_graph_meta_service(self):
        return self._metastore_controller.get_backward_graph_meta_ctl()

    def set_resources_meta_service(self, wf_resources_meta):
        self._metastore_controller.set_resources_meta_ctl(wf_resources_meta)

    def set_start_nodes_meta_service(self, start_nodes):
        self._metastore_controller.set_start_nodes_meta_ctl(start_nodes)

    def get_start_nodes_meta_service(self):
        self._metastore_controller.get_start_nodes_meta_ctl()

    def set_end_nodes_meta_service(self, end_nodes):
        self._metastore_controller.set_end_nodes_meta_ctl(end_nodes)

    def set_edges_param_map_service(self, service_params_map):
        self._metastore_controller.set_edges_param_map_ctl(service_params_map)

    def get_edges_param_map_service(self):
        edges_param_map = self._metastore_controller.get_edges_param_map_ctl()
        return edges_param_map

    def get_meta_pack_service(self) -> Dict:
        meta_pack = self._metastore_controller.get_metas_ctl()
        return meta_pack

    def set_wf_meta_service(self, wf_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._metastore_controller.save_wf_meta_on_file(wf_meta, dirpath, filename)

    def get_wf_meta_file_service(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._metastore_controller.load_wf_meta_on_file()
        return wf_meta

    def set_init_task_map_service(self, task_map):
        self._taskpool_controller.set_init_task_map_control(task_map)

    def get_init_task_map_service(self):
        task_map = self._taskpool_controller.get_init_task_map_control()
        return task_map