#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class EnvironmentsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def cvt_node_env_value_map_ctl(self, wf_nodes_meta, wf_node_env_map_pool, wf_env_pool) -> dict:
        nodes_env_value_map = {}
        for node_id, node_meta in wf_nodes_meta.items():
            module_info = node_meta.get('class_info')
            if not module_info: continue
            module_env_info = module_info.get('environments')
            if not module_env_info: continue
            env_params = module_env_info.get('params')
            if not env_params: continue

            node_env_map = wf_node_env_map_pool.get(node_id)
            for node_env_param_name, node_env_map in node_env_map.items():
                ref_type = node_env_map.get('refer_type')
                if ref_type.lower() == 'direct':
                    value = node_env_map.get('value')
                else:
                    env_map_id = node_env_map.get('value')
                    value = wf_env_pool.get(env_map_id)
                env_id = f"{node_id}.{node_env_param_name}"
                nodes_env_value_map[env_id] = value
        return nodes_env_value_map

