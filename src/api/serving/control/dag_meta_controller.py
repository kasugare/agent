#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.serving.access.dag_file_access import DagFileAccess
from .edge_transform import EdgeTransformer
from typing import Dict, List, Any
import traceback
import json
import os


class DagMetaController:
    def __init__(self, logger):
        self._logger = logger
        self._dag_file_access = DagFileAccess(logger)
        self._edge_transformer = EdgeTransformer(logger)

    def load_wf_config(self) -> Dict:
        wf_config = self._dag_file_access.get_wf_config_on_file()
        return wf_config

    def save_wf_config(self, wf_config:Dict) -> None:
        self._dag_file_access.set_wf_config_on_file(wf_config)

    def get_wf_common_info(self, wf_config: Dict) -> Dict:
        wf_comm_meta = {
            'wf_id': wf_config.get('workflow_id'),
            'wf_name': wf_config.get('name'),
            'wf_version': wf_config.get('version'),
            'wf_description': wf_config.get('description'),
            'run_type': wf_config.get('run_mode')
        }
        return wf_comm_meta

    def get_wf_to_nodes(self, wf_config: Dict) -> Dict:
        nodes = wf_config.get('nodes')
        nodes_meta = {node.get('node_id'): node for node in nodes if node.get('node_id')}
        return nodes_meta

    def cvt_wf_to_service_pool(self, nodes_meta: Dict) -> Dict:
        service_pool = {}
        add_node_keys = ['node_type', 'role', 'location', 'api_keys', 'containable']
        for node_id, node_info in nodes_meta.items():
            services = node_info.get('services')
            for service_info in services:
                service_name = service_info.get('name')
                node_service_id = f"{node_id}.{service_name}"
                service_pool[node_service_id] = service_info
                for node_key in add_node_keys:
                    service_pool[node_service_id][node_key] = node_info[node_key]
        return service_pool

    def get_wf_to_edges(self, wf_config: Dict, wf_service_pool: Dict) -> List:
        edges_meta = self._edge_transformer.cvt_service_edges(wf_config, wf_service_pool)
        return edges_meta

    def cvt_edge_to_grape(self, edges_meta: List) -> Dict:
        edge_grape = {}
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('source')
            next_node = edge_info.get('target')
            if curr_node in edge_grape.keys():
                edge_grape[curr_node].append(next_node)
            else:
                edge_grape[curr_node] = [next_node]
        return edge_grape

    def get_edges_to_prev_nodes(self, edges_meta: List) -> Dict:
        prev_edge_grape = {}
        for edge_id, edge_info in edges_meta.items():
            curr_node = edge_info.get('target')
            prev_node = edge_info.get('source')
            if curr_node in prev_edge_grape.keys():
                prev_edge_grape[curr_node].append(prev_node)
            else:
                prev_edge_grape[curr_node] = [prev_node]
        return prev_edge_grape

    def get_wf_to_resources(self, wf_config: Dict) -> Dict:
        resources = wf_config.get('resources')
        return resources




    # ----------------------------------------------------#

    def cvt_wf_to_edge(self, nodes_meta: Dict) -> Dict:
        edge_map = {}
        for node_id, node_info in nodes_meta.items():
            next_nodes = node_info['next_nodes']
            edge_map[node_id] = next_nodes
        return edge_map

    def cvt_wf_to_dag(self, wf_config: Dict) -> Dict:
        if wf_config.get('nodes'):
            nodes_meta = wf_config.get('nodes')
        else:
            nodes_meta = {}

        if wf_config.get('edges'):
            edges_meta = wf_config.get('edges')
        else:
            edges_meta = {}

        return wf_config

    def find_start_node(self, edge_map: Dict) -> Any:
        start_nodes = self.find_start_nodes(edge_map)
        if start_nodes:
            return start_nodes[0]
        return None

    def find_start_nodes(self, edge_map: Dict) -> List:
        all_nodes = set(edge_map.keys())
        reachable_nodes = set()
        for node in edge_map:
            reachable_nodes.update(edge_map[node])
        start_nodes = all_nodes - reachable_nodes
        return sorted(list(start_nodes))
