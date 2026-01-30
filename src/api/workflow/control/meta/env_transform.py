#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from api.workflow.error_pool.error import EnvironmentKeyError


class EnvironmentsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def _check_valid_env(self, node_env_params, edge_env_map):
        if not node_env_params:
            node_env_keys = set()
        else:
            node_env_keys = set([node_env_param.get('key') for node_env_param in node_env_params])

        if not edge_env_map:
            edge_env_keys = set()
        else:
            edge_env_keys = set(edge_env_map.keys())

        if node_env_keys != (node_env_keys | edge_env_keys):
            raise EnvironmentKeyError
        return True

    def _find_node_env_param(self, node_env_params, env_key):
        for node_env_param_map in node_env_params:
            if node_env_param_map.get('key') == env_key:
                return node_env_param_map
        return None

    def cvt_node_env_value_map_ctl(self, wf_nodes_meta, wf_node_env_map_pool, wf_env_pool) -> dict:
        nodes_env_value_map = {}
        for node_id, node_meta in wf_nodes_meta.items():
            module_env_info = node_meta.get('environments')
            if not module_env_info:
                continue
            node_env_params = module_env_info.get('params')
            if not node_env_params:
                continue

            edge_env_params_map = wf_node_env_map_pool.get(node_id, {})
            self._check_valid_env(node_env_params, edge_env_params_map)

            node_env_keys = set([node_env_param.get('key') for node_env_param in node_env_params])
            for node_env_key in node_env_keys:
                edge_env_map = edge_env_params_map.get(node_env_key)
                if edge_env_map:
                    ref_type = edge_env_map.get('refer_type')
                    if ref_type.lower() == 'direct':
                        value = edge_env_map.get('value')
                    else:
                        env_map_id = edge_env_map.get('value')
                        value = wf_env_pool.get(env_map_id)
                    env_id = f"{node_id}.{node_env_key}"
                    nodes_env_value_map[env_id] = value
                else:
                    node_env_param_map = self._find_node_env_param(node_env_params, node_env_key)
                    if node_env_param_map.get('default'):
                        value = node_env_param_map.get('default')
                        env_id = f"{node_id}.{node_env_key}"
                        nodes_env_value_map[env_id] = value
                    elif node_env_param_map.get('required'):
                        raise ValueError
        return nodes_env_value_map
