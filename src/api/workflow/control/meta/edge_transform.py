#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class EdgeTransformer:
    def __init__(self, logger):
        self._logger = logger
        self._index = 0

    def _get_data_type(self, svr_param_key: str, wf_service_pool: Dict, find_type: str) -> Any:
        splited_param_path = svr_param_key.split('.')
        service_id = ".".join(splited_param_path[:-1])
        key = splited_param_path[-1]
        service_info = wf_service_pool.get(service_id)

        if find_type == 'key':
            mapper_info = service_info['params']['input']
        elif find_type == 'value':
            mapper_info = service_info['result']['output']
        else:
            return None

        for data_map in mapper_info:
            if data_map.get('key') == key:
                data_type = data_map.get('type')
                # print(f"- [{find_type}]", splited_param_id, ":\t\t", data_map, "\t", data_type)
                return data_type
        return None

    def _add_data_type_on_data_mapper(self, data_mapper, wf_service_pool):
        for data_map in data_mapper:
            call_method = data_map.get('call_method')
            param_key_path = data_map.get('key')
            tar_data_type = self._get_data_type(param_key_path, wf_service_pool, find_type='key')
            data_map['key_type'] = tar_data_type
            if call_method == 'refer':
                src_value_path = data_map.get('value')
                src_data_type = self._get_data_type(src_value_path, wf_service_pool, find_type='value')
                data_map['value_type'] = src_data_type
            elif call_method == 'value':
                src_value = data_map.get('value')
                data_map['value_type'] = type(src_value).__name__
        return data_mapper

    def cvt_service_edges(self, wf_config: Dict, wf_service_pool: Dict) -> Dict:
        def get_service_info(service_id):
            service_info = wf_service_pool.get(service_id)
            return service_info

        edges_map = {}
        edges_meta = wf_config.get('edges')
        for edge_info in edges_meta:
            src_id = edge_info.get('source')
            tar_id = edge_info.get('target')
            edge_id = f"{src_id}-{tar_id}"
            edges_map[edge_id] = edge_info
            edges_map[edge_id]['source_info'] = get_service_info(src_id)
            edges_map[edge_id]['target_info'] = get_service_info(tar_id)
            data_mapper = edge_info.get('data_mapper')
            self._add_data_type_on_data_mapper(data_mapper, wf_service_pool)

        return edges_map
