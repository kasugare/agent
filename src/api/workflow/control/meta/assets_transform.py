#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from api.workflow.error_pool.error import AssetKeyError, MismatchedRequirementsError, NotExistRequiredNodesError


class AssetsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def _find_required_node_ids(self, node_id, refer_key, wf_edges_meta):
        req_node_ids = []
        for edge_id, edge_meta in wf_edges_meta.items():
            service_id = edge_meta.get('target')
            if node_id != service_id.split(".")[0]:
                continue
            target_handler = edge_meta.get('target_handler', {})
            references = target_handler.get('references', [])
            for required_node_info in references:
                if refer_key == required_node_info.get("refer_key", ""):
                    req_node_id = required_node_info.get("node_id")
                    req_node_ids.append(req_node_id)
        return req_node_ids

    def _get_node_url(self, req_node_id, wf_nodes_meta, req_value):
        node_meta = wf_nodes_meta.get(req_node_id)
        api_info = node_meta.get('api_info')
        base_url = api_info.get(req_value)
        return base_url

    def _extract_required_asset(self, node_id, req_nodes_info, wf_nodes_meta, wf_edges_meta):
        req_asset_env_pool = {}
        for req_node_map in req_nodes_info:
            refer_key = req_node_map.get('refer_key')
            req_value = req_node_map.get('req_value')

            req_node_ids = self._find_required_node_ids(node_id, refer_key, wf_edges_meta)
            for req_node_id in req_node_ids:
                value = self._get_node_url(req_node_id, wf_nodes_meta, req_value)

                asset_key = f"{refer_key}.{req_value}"
                req_asset_env_pool[asset_key] = value
        return req_asset_env_pool

    def gen_asset_env_pool(self, wf_nodes_meta, wf_edges_meta):
        asset_env_pool = {}
        for node_id, node_info in wf_nodes_meta.items():
            req_nodes_info = node_info.get('required_nodes', [])
            if not req_nodes_info:
                continue
            req_asset_env_pool = self._extract_required_asset(node_id, req_nodes_info, wf_nodes_meta, wf_edges_meta)
            asset_env_pool[node_id] = req_asset_env_pool
        return asset_env_pool

    def _find_node_asset_param(self, node_asset_params, asset_key):
        for node_asset_param_map in node_asset_params:
            if node_asset_param_map.get('key') == asset_key:
                return node_asset_param_map
        return None

    def cvt_node_asset_value_map_ctl(self, wf_nodes_meta, wf_node_asset_map_pool, wf_asset_pool) -> dict:
        nodes_asset_value_map = {}
        for node_id, node_meta in wf_nodes_meta.items():
            module_asset_info = node_meta.get('asset_environments')
            if not module_asset_info:
                continue

            node_asset_params = module_asset_info.get('params')
            if not node_asset_params:
                continue

            edge_asset_params_map = wf_node_asset_map_pool.get(node_id, {})
            node_asset_keys = set([node_asset_param.get('key') for node_asset_param in node_asset_params])
            for node_asset_key in node_asset_keys:
                edge_asset_map = edge_asset_params_map.get(node_asset_key)
                if edge_asset_map:
                    ref_type = edge_asset_map.get('refer_type')
                    if ref_type.lower() == 'direct':
                        value = edge_asset_map.get('value')
                    else:
                        asset_map_id = edge_asset_map.get('value')
                        node_asset_pool = wf_asset_pool.get(node_id)
                        value = node_asset_pool.get(asset_map_id)
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
