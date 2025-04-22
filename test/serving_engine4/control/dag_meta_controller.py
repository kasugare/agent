#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.serving.access.dag_file_access import DagFileAccess
from typing import Dict, List, Any
import traceback
import json
import os


class DagMetaController:
    def __init__(self, logger):
        self._logger = logger
        self._dag_file_access = DagFileAccess(logger)

    def load_wf_config(self) -> Dict:
        wf_config = self._dag_file_access.get_wf_config_on_file()
        return wf_config

    def save_wf_config(self, wf_config:Dict) -> None:
        self._dag_file_access.set_wf_config_on_file(wf_config)

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
        return nodes_meta

    def find_start_nodes(self, edge_map: Dict) -> List:
        all_nodes = set(edge_map.keys())
        reachable_nodes = set()
        for node in edge_map:
            reachable_nodes.update(edge_map[node])
        start_nodes = all_nodes - reachable_nodes
        return sorted(list(start_nodes))
