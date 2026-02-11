#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.meta.meta_parse_controller import MetaParseController
from typing import Dict, List


class WorkflowMetaHandler:
    def __init__(self, logger):
        self._logger = logger
        self._meta_controller = MetaParseController(logger)

    def check_meta_validation(self, wf_meta: Dict) -> bool:
        wf_comm_meta = self._meta_controller.check_meta_validation(wf_meta)


    def extract_wf_id(self, wf_meta: Dict) -> str:
        wf_comm_meta = self._meta_controller.extract_wf_common_info_ctl(wf_meta)
        wf_id = wf_comm_meta.get('wf_id')
        return wf_id

    def extract_wf_common_info(self, wf_meta: Dict) -> Dict:
        wf_comm_meta = self._meta_controller.extract_wf_common_info_ctl(wf_meta)
        return wf_comm_meta

    def extract_wf_common_env(self, wf_meta: Dict) -> Dict:
        wf_env_pool = self._meta_controller.extract_wf_common_env_ctl(wf_meta)
        return wf_env_pool

    def extract_wf_asset_env(self, wf_nodes_meta: Dict, wf_edges_meta: Dict) -> Dict:
        wf_asset_pool = self._meta_controller.extract_wf_asset_env_ctl(wf_nodes_meta, wf_edges_meta)
        return wf_asset_pool

    def extract_wf_node_env(self, wf_edges_meta: Dict) -> Dict:
        wf_node_env_map_pool = self._meta_controller.extract_wf_node_env_map_ctl(wf_edges_meta)
        return wf_node_env_map_pool

    def extract_wf_node_asset(self, wf_edges_meta: Dict) -> Dict:
        node_asset_map_pool = self._meta_controller.extract_wf_node_asset_map_ctl(wf_edges_meta)
        return node_asset_map_pool

    def extract_wf_to_nodes(self, wf_meta: Dict) -> Dict:
        wf_nodes_meta = self._meta_controller.extract_wf_to_nodes_ctl(wf_meta)
        return wf_nodes_meta

    def cvt_wf_to_service_pool(self, wf_nodes_meta: Dict) -> Dict:
        wf_service_pool = self._meta_controller.cvt_wf_to_service_pool_ctl(wf_nodes_meta)
        return wf_service_pool

    def extract_wf_to_edges(self, wf_meta, wf_service_pool: Dict) -> Dict:
        wf_edges_meta = self._meta_controller.extract_wf_to_edges_ctl(wf_meta, wf_service_pool)
        return wf_edges_meta

    def extract_forward_edge_graph(self, wf_edges_meta:Dict) -> Dict:
        wf_forward_edge_graph = self._meta_controller.extract_forward_edge_graph_ctl(wf_edges_meta)
        return wf_forward_edge_graph

    def extract_forward_graph(self, wf_edges_meta: Dict) -> Dict:
        wf_forward_graph = self._meta_controller.extract_forward_graph_ctl(wf_edges_meta)
        return wf_forward_graph

    def extract_backward_graph(self, wf_edges_meta: Dict) -> Dict:
        wf_backward_graph = self._meta_controller.extract_backward_graph_ctl(wf_edges_meta)
        return wf_backward_graph

    def reverse_forward_graph(self, wf_forward_graph) -> Dict:
        wf_backward_graph = self._meta_controller.reverse_forward_graph_ctl(wf_forward_graph)
        return wf_backward_graph

    def get_wf_to_resources(self, wf_meta: Dict) -> Dict:
        wf_resources_meta = self._meta_controller.get_wf_to_resources_ctl(wf_meta)
        return wf_resources_meta

    def find_start_nodes(self, wf_forward_graph: Dict) -> List:
        start_nodes = self._meta_controller.find_start_nodes_ctl(wf_forward_graph)
        return start_nodes

    def find_end_nodes(self, wf_backward_graph: Dict) -> List:
        end_nodes = self._meta_controller.find_end_nodes_ctl(wf_backward_graph)
        return end_nodes

    def extract_node_environments_value_map(self, wf_nodes_meta, wf_node_env_map_pool, wf_env_pool) -> Dict:
        nodes_env_value_map = self._meta_controller.extract_node_env_value_map_ctl(wf_nodes_meta, wf_node_env_map_pool, wf_env_pool)
        return nodes_env_value_map

    def extract_node_asset_value_map(self, wf_nodes_meta, wf_node_asset_map_pool, wf_env_pool) -> Dict:
        nodes_env_value_map = self._meta_controller.extract_node_asset_value_map_ctl(wf_nodes_meta, wf_node_asset_map_pool, wf_env_pool)
        return nodes_env_value_map

    def extract_custom_result_meta(self, wf_edges_meta: Dict) -> Dict:
        custom_result_meta = self._meta_controller.extract_custom_result_meta_ctl(wf_edges_meta)
        return custom_result_meta

    def extract_params_map(self, start_nodes, wf_service_pool, wf_edges_meta) -> Dict:
        edge_params_map = self._meta_controller.extract_params_map_ctl(start_nodes, wf_service_pool, wf_edges_meta)
        return edge_params_map

    def extract_target_handler_reference(self, wf_nodes_meta, wf_edges_meta):
        self._meta_controller.extract_target_handler_reference_ctl(wf_nodes_meta, wf_edges_meta)
