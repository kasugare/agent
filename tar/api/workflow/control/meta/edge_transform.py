#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any


class EdgeTransformer:
    def __init__(self, logger):
        self._logger = logger

    def _get_data_type(self, param_key: str, service_info: Dict, find_type: str) -> Any:
        if find_type == 'key':
            mapper_info = service_info['params']
        elif find_type == 'value':
            mapper_info = service_info['result']
        elif find_type == 'values':
            return 'object', False
        else:
            return None, None

        for data_map in mapper_info:
            if data_map.get('key') == param_key:
                data_type = data_map.get('type')
                required = data_map.get('required')
                return data_type, required
        return None, None

    def _set_default_params_info(self, service_id, service_info):
        params_info = []
        input_params = service_info['params']
        for input_map in input_params:
            params_name = input_map.get('key')
            params_value = f"{service_id}.{params_name}"
            params_map = {
                'refer_type': 'direct',
                'key': params_name,
                'value': params_value
            }
            params_info.append(params_map)
        return params_info

    def _add_data_type_on_params_info(self, params_info, tar_service_info):
        for param_map in params_info:
            refer_type = param_map.get('refer_type')
            param_key_path = param_map.get('key')
            tar_data_type, required = self._get_data_type(param_key_path, tar_service_info, find_type='key')
            param_map['key_data_type'] = tar_data_type
            param_map['key_required'] = required

            if refer_type == 'direct':
                src_value = param_map.get('value')
                param_map['value_data_type'] = type(src_value).__name__
            else:
                src_value_path = param_map.get('value')
                src_data_type, _ = self._get_data_type(src_value_path, tar_service_info, find_type='value')
                if not src_data_type:
                    src_data_type = tar_data_type
                param_map['value_data_type'] = src_data_type
        return params_info

    def cvt_service_edges(self, wf_config: Dict, wf_service_pool: Dict) -> Dict:
        edges_map = {}
        edges_meta = wf_config.get('edges')
        for edge_info in edges_meta:
            src_service_id = edge_info.get('source')
            tar_service_id = edge_info.get('target')
            edge_id = f"{src_service_id}-{tar_service_id}"

            src_service_info = wf_service_pool.get(src_service_id)
            tar_service_info = wf_service_pool.get(tar_service_id)
            edges_map[edge_id] = edge_info
            edges_map[edge_id]['source_info'] = src_service_info
            edges_map[edge_id]['target_info'] = tar_service_info
            params_info = edge_info.get('param_info')
            self._add_data_type_on_params_info(params_info, tar_service_info)
        return edges_map

    def cvt_params_map_ctl(self, start_nodes, wf_service_pool, wf_edges_meta) -> dict:
        edge_params_map = dict()
        for edge_id, edge_info in wf_edges_meta.items():
            src_service_id = edge_info.get('source')
            tar_service_id = edge_info.get('target')
            if src_service_id in start_nodes:
                start_edge_id = f"{None}-{src_service_id}"
                src_service_info = wf_service_pool.get(src_service_id)
                params_info = self._set_default_params_info(src_service_id, src_service_info)
                params_info = self._add_data_type_on_params_info(params_info, src_service_info)
                edge_params_map[start_edge_id] = params_info
            edge_params_map[edge_id] = edge_info.get('param_info')
        return edge_params_map