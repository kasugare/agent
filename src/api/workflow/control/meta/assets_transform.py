#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class AssetsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def cvt_node_asset_value_map_ctl(self, wf_nodes_meta, wf_node_asset_map_pool, wf_asset_pool) -> dict:
        nodes_asset_value_map = {}
        for node_id, node_meta in wf_nodes_meta.items():
            module_info = node_meta.get('module_info')
            if not module_info: continue
            module_asset_info = module_info.get('asset_environments')
            if not module_asset_info: continue
            asset_params = module_asset_info.get('params')
            if not asset_params: continue

            node_asset_map = wf_node_asset_map_pool.get(node_id)
            for node_asset_param_name, node_asset_map in node_asset_map.items():
                ref_type = node_asset_map.get('refer_type')
                if ref_type.lower() == 'direct':
                    value = node_asset_map.get('value')
                else:
                    asset_map_id = node_asset_map.get('value')
                    value = wf_asset_pool.get(asset_map_id)
                asset_id = f"{node_id}.{node_asset_param_name}"
                nodes_asset_value_map[asset_id] = value
        return nodes_asset_value_map
