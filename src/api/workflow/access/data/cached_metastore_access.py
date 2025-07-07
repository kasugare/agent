#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
import threading

class CachedMetastoreAccess:
    def __init__(self, logger):
        self._logger = logger
        self._thread_lock = threading.Lock()
        self._dag_meta = {}
        self._edge_map = {}

        self._wf_comm_meta = {}
        self._wf_nodes_meta = {}
        self._wf_node_service_pool = {}
        self._wf_edges_meta = []
        self._wf_forward_edge_graph = {}
        self._wf_reverse_edge_graph = {}
        self._wf_resources_meta = {}
        self._start_nodes = []
        self._end_nodes = []

    def set_comm_meta_access(self, wf_comm_meta: Dict) -> None:
        self._wf_comm_meta = wf_comm_meta

    def set_nodes_meta_access(self, wf_nodes_meta: Dict) -> None:
        self._wf_nodes_meta = wf_nodes_meta

    def set_node_service_pool_access(self, wf_service_pool: Dict) -> None:
        self._wf_node_service_pool = wf_service_pool

    def set_edges_meta_access(self, wf_edges_meta: Dict) -> None:
        self._wf_edges_meta = wf_edges_meta

    def get_edges_meta_access(self) -> List:
        return self._wf_edges_meta

    def set_forward_graph_meta_access(self, wf_forward_edge_graph: Dict) -> None:
        self._wf_forward_edge_graph = wf_forward_edge_graph

    def get_forward_graph_meta_access(self) -> Dict:
        return self._wf_forward_edge_graph

    def set_reverse_graph_meta_access(self, wf_reverse_edge_graph: Dict) -> None:
        self._wf_reverse_edge_graph = wf_reverse_edge_graph

    def get_reverse_graph_meta_access(self) -> Dict:
        return self._wf_reverse_edge_graph

    def set_resources_meta_access(self, wf_resources_meta: Dict) -> None:
        self._wf_resources_meta = wf_resources_meta

    def set_start_nodes_meta_access(self, start_nodes: str) -> None:
        self._start_nodes = start_nodes

    def set_end_nodes_meta_access(self, end_nodes: str) -> None:
        self._end_nodes = end_nodes

    def get_dag_access(self) -> Dict:
        return self._dag_meta

    def get_comm_meta_access(self) -> Dict:
        return self._wf_comm_meta

    def get_node_service_pool_access(self) -> Dict:
        return self._wf_node_service_pool

    def get_nodes_meta_access(self) -> Dict:
        return self._wf_nodes_meta

    def get_edges_graph_meta_access(self) -> Dict:
        return self._wf_edges_graph

    def get_prev_edges_grpae_meta_access(self) -> Dict:
        return self._wf_prev_edge_graph

    def get_resources_meta_access(self) -> Dict:
        return self._wf_resources_meta

    def get_start_nodes_meta_access(self) -> List:
        return self._start_nodes

    def get_end_nodes_meta_access(self) -> List:
        return self._end_nodes
