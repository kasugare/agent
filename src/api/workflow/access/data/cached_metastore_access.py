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
        self._wf_edges_grape = {}
        self._wf_prev_edge_grape = {}
        self._wf_resources_meta = {}
        self._start_nodes = []
        self._end_nodes = []

    def set_comm_meta(self, wf_comm_meta: Dict) -> None:
        self._wf_comm_meta = wf_comm_meta

    def set_nodes_meta(self, wf_nodes_meta: Dict) -> None:
        self._wf_nodes_meta = wf_nodes_meta

    def set_node_service_pool(self, wf_service_pool: Dict) -> None:
        self._wf_node_service_pool = wf_service_pool

    def set_edges_meta(self, wf_edges_meta: Dict) -> None:
        self._wf_edges_meta = wf_edges_meta

    def set_edges_grape_meta(self, wf_edges_grape: Dict) -> None:
        self._wf_edges_grape = wf_edges_grape

    def set_prev_edge_grape_meta(self, wf_prev_edge_grape: Dict) -> None:
        self._wf_prev_edge_grape = wf_prev_edge_grape

    def set_resources_meta(self, wf_resources_meta: Dict) -> None:
        self._wf_resources_meta = wf_resources_meta

    def set_start_nodes_meta(self, start_nodes: str) -> None:
        self._start_nodes = start_nodes

    def set_end_nodes_meta(self, end_nodes: str) -> None:
        self._end_nodes = end_nodes

    def get_dag(self) -> Dict:
        return self._dag_meta

    def get_comm_meta(self) -> Dict:
        return self._wf_comm_meta

    def get_node_service_pool(self) -> Dict:
        return self._wf_node_service_pool

    def get_nodes_meta(self) -> Dict:
        return self._wf_nodes_meta

    def get_edges_meta(self) -> Dict:
        return self._wf_edges_meta

    def get_edges_grape_meta(self) -> Dict:
        return self._wf_edges_grape

    def get_prev_edges_grpae_meta(self) -> Dict:
        return self._wf_prev_edge_grape

    def get_resources_meta(self) -> Dict:
        return self._wf_resources_meta

    def get_start_nodes_meta(self) -> str:
        return self._start_nodes

    def get_end_nodes_meta(self) -> str:
        return self._end_nodes
