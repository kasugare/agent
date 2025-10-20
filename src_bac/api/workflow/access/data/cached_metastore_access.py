#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from copy import deepcopy
import threading

class CachedMetastoreAccess:
    def __init__(self, logger):
        self._logger = logger
        self._thread_lock = threading.Lock()

        self._dag_meta = {}
        self._edge_map = {}

        self._wf_meta = {}
        self._wf_comm_meta = {}
        self._wf_nodes_meta = {}
        self._wf_node_service_pool = {}
        self._wf_edges_meta = []
        self._wf_custom_result_meta = {}
        self._wf_forward_edge_graph = {}
        self._wf_forward_graph = {}
        self._wf_backward_graph = {}
        self._wf_resources_meta = {}
        self._start_nodes = []
        self._end_nodes = []
        self._edges_param_map = {}

    def set_cache_key_access(self, wf_key):
        self._cache_key = wf_key

    def clear_access(self):
        self._wf_meta.clear()
        self._wf_comm_meta.clear()
        self._wf_nodes_meta.clear()
        self._wf_node_service_pool.clear()
        self._wf_edges_meta.clear()
        self._wf_custom_result_meta.clear()
        self._wf_forward_edge_graph.clear()
        self._wf_forward_graph.clear()
        self._wf_backward_graph.clear()
        self._wf_resources_meta.clear()
        self._start_nodes.clear()
        self._end_nodes.clear()
        self._edges_param_map.clear()

    def set_wf_meta_access(self, wf_meta: Dict) -> None:
        self._wf_meta = wf_meta

    def get_wf_meta_access(self) -> Dict:
        return self._wf_meta

    def set_comm_meta_access(self, wf_comm_meta: Dict) -> None:
        self._wf_comm_meta = wf_comm_meta

    def set_nodes_meta_access(self, wf_nodes_meta: Dict) -> None:
        self._wf_nodes_meta = wf_nodes_meta

    def set_node_service_pool_access(self, wf_service_pool: Dict) -> None:
        self._wf_node_service_pool = wf_service_pool

    def set_edges_meta_access(self, wf_edges_meta: Dict) -> None:
        self._wf_edges_meta = wf_edges_meta

    def get_edges_meta_access(self) -> List:
        return deepcopy(self._wf_edges_meta)

    def set_custom_result_meta_access(self, custom_result_meta: Dict) -> None:
        self._wf_custom_result_meta = custom_result_meta

    def get_custom_result_meta_access(self):
        custom_result_meta = self._wf_custom_result_meta
        return custom_result_meta

    def get_custom_result_meta_by_service_id_access(self, service_id):
        custom_result = self._wf_custom_result_meta.get(service_id)
        return custom_result

    def set_forward_edge_graph_meta_access(self, wf_forward_edge_graph: Dict) -> None:
        self._wf_forward_edge_graph = wf_forward_edge_graph

    def get_forward_edge_graph_meta_access(self) -> Dict:
        return deepcopy(self._wf_forward_edge_graph)

    def set_forward_graph_meta_access(self, wf_forward_graph: Dict) -> None:
        self._wf_forward_graph = wf_forward_graph

    def get_forward_graph_meta_access(self) -> Dict:
        return deepcopy(self._wf_forward_graph)

    def set_backward_graph_meta_access(self, wf_backward_graph: Dict) -> None:
        self._wf_backward_graph = wf_backward_graph

    def get_backward_graph_meta_access(self) -> Dict:
        return deepcopy(self._wf_backward_graph)

    def set_resources_meta_access(self, wf_resources_meta: Dict) -> None:
        self._wf_resources_meta = wf_resources_meta

    def set_start_nodes_meta_access(self, start_nodes: list) -> None:
        self._start_nodes = start_nodes

    def set_end_nodes_meta_access(self, end_nodes: list) -> None:
        self._end_nodes = end_nodes

    def set_edges_param_map_access(self, edge_params_map: dict) -> None:
        self._edges_param_map.update(edge_params_map)

    def get_edges_param_map_access(self) -> Dict:
        return deepcopy(self._edges_param_map)

    def get_dag_access(self) -> Dict:
        return deepcopy(self._dag_meta)

    def get_comm_meta_access(self) -> Dict:
        return deepcopy(self._wf_comm_meta)

    def get_node_service_pool_access(self) -> Dict:
        return deepcopy(self._wf_node_service_pool)

    def get_nodes_meta_access(self) -> Dict:
        return deepcopy(self._wf_nodes_meta)

    def get_forward_edges_graph_meta_access(self) -> Dict:
        return deepcopy(self._wf_forward_edge_graph)

    def get_resources_meta_access(self) -> Dict:
        return deepcopy(self._wf_resources_meta)

    def get_start_nodes_meta_access(self) -> List:
        return deepcopy(self._start_nodes)

    def get_end_nodes_meta_access(self) -> List:
        return deepcopy(self._end_nodes)

