#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.data.metastore_controller import MetastoreController
from typing import Dict, Any


class MetaStoreService:
    def __init__(self, logger):
        self._logger = logger
        self._metastore_controller = MetastoreController(logger)

    def clear(self):
        self._metastore_controller.clear_ctl()

    def set_cache_key_service(self, wf_key):
        self._metastore_controller.set_cache_key_ctl(wf_key)

    def set_wf_meta_service(self, wf_meta):
        self._metastore_controller.set_wf_meta_ctl(wf_meta)

    def get_wf_meta_service(self):
        wf_meta = self._metastore_controller.get_wf_meta_ctl()
        return wf_meta

    def set_comm_meta_service(self, wf_comm_meta):
        project_id = wf_comm_meta.get('proj_id')
        workflow_id = wf_comm_meta.get('wf_id')
        wf_key = f"{project_id}-{workflow_id}"
        self.set_cache_key_service(wf_key)
        self._metastore_controller.set_comm_meta_ctl(wf_comm_meta)

    def get_comm_meta_service(self):
        wf_comm_meta = self._metastore_controller.get_comm_meta_ctl()
        return wf_comm_meta

    def set_env_pool_service(self, wf_env_pool):
        self._metastore_controller.set_env_pool_ctl(wf_env_pool)

    def get_env_pool_service(self):
        wf_env_pool = self._metastore_controller.get_env_pool_ctl()
        return wf_env_pool

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

    def set_nodes_env_value_map_service(self, wf_nodes_env_map_pool):
        self._metastore_controller.set_nodes_env_value_map_ctl(wf_nodes_env_map_pool)

    def get_node_env_value_map_service(self):
        wf_nodes_env_map_pool = self._metastore_controller.get_nodes_env_value_map_ctl()
        return wf_nodes_env_map_pool

    def set_nodes_asset_value_map_service(self, wf_nodes_asset_map_pool):
        self._metastore_controller.set_nodes_asset_value_map_ctl(wf_nodes_asset_map_pool)

    def get_nodes_asset_value_map_service(self):
        wf_nodes_asset_map_pool = self._metastore_controller.get_nodes_asset_value_map_ctl()
        return wf_nodes_asset_map_pool

    def get_edge_info_by_edge_id(self, edge_id):
        wf_edge_meta = self._metastore_controller.get_edge_meta_by_edge_id_ctl(edge_id)
        return wf_edge_meta

    def set_custom_result_meta_service(self, custom_result_meta):
        self._metastore_controller.set_custom_result_meta_ctl(custom_result_meta)

    def get_custom_result_meta_service(self):
        custom_result_meta = self._metastore_controller.get_custom_result_meta_ctl()
        return custom_result_meta

    def get_custom_result_meta_by_service_id_service(self, service_id):
        custom_result_meta = self._metastore_controller.get_custom_result_meta_by_service_id_ctl(service_id)
        return custom_result_meta

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

    def set_wf_meta_file_service(self, wf_meta: Dict, dirpath: str = None, filename: str = None) -> None:
        self._metastore_controller.save_wf_meta_on_file(wf_meta, dirpath, filename)

    def get_wf_meta_file_service(self, dirpath: str = None, filename: str = None) -> Dict:
        wf_meta = self._metastore_controller.load_wf_meta_on_file()
        return wf_meta
