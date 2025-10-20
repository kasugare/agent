#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from api.workflow.error_pool.error import AssetKeyError


class AssetsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def _check_valid_asset(self, node_asset_params, edge_asset_map):
        if not node_asset_params:
            node_asset_keys = set()
        else:
            node_asset_keys = set([node_asset_param.get('key') for node_asset_param in node_asset_params])

        if not edge_asset_map:
            edge_asset_keys = set()
        else:
            edge_asset_keys = set(edge_asset_map.keys())

        if node_asset_keys != (node_asset_keys | edge_asset_keys):
            raise AssetKeyError

    def _find_node_asset_param(self, node_asset_params, asset_key):
        for node_asset_param_map in node_asset_params:
            if node_asset_param_map.get('key') == asset_key:
                return node_asset_param_map
        return None

    def cvt_node_asset_value_map_ctl(self, wf_nodes_meta, wf_node_asset_map_pool, wf_asset_pool) -> dict:
        nodes_asset_value_map = {}
        for node_id, node_meta in wf_nodes_meta.items():
            module_info = node_meta.get('module_info')
            if not module_info:
                continue

            module_asset_info = module_info.get('asset_environments')
            if not module_asset_info:
                continue

            node_asset_params = module_asset_info.get('params')
            if not node_asset_params:
                continue

            edge_asset_params_map = wf_node_asset_map_pool.get(node_id, {})
            self._check_valid_asset(node_asset_params, edge_asset_params_map)

            node_asset_keys = set([node_asset_param.get('key') for node_asset_param in node_asset_params])
            for node_asset_key in node_asset_keys:
                edge_asset_map = edge_asset_params_map.get(node_asset_key)
                if edge_asset_map:
                    ref_type = edge_asset_map.get('refer_type')
                    if ref_type.lower() == 'direct':
                        value = edge_asset_map.get('value')
                    else:
                        asset_map_id = edge_asset_map.get('value')
                        value = wf_asset_pool.get(asset_map_id)
                    asset_id = f"{node_id}.{node_asset_key}"
                    nodes_asset_value_map[asset_id] = value
                else:
                    node_asset_param_map = self._find_node_asset_param(node_asset_params, node_asset_key)
                    if node_asset_param_map.get('default'):
                        value = node_asset_param_map.get('default')
                        asset_id = f"{node_id}.{node_asset_key}"
                        nodes_asset_value_map[asset_id] = value
                    elif node_asset_param_map.get('required'):
                        raise ValueError
        return nodes_asset_value_map
