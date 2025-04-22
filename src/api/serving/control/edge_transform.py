#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class EdgeTransformer:
    def __init__(self, logger):
        self._logger = logger
        self._result_map = {}
        self._index = 0

    def _get_data_type(self, svr_param_id: str, wf_service_pool: Dict, find_type: str) -> Any:
        splited_param_id = svr_param_id.split('.')
        service_id = ".".join(splited_param_id[:-1])
        key = splited_param_id[-1]
        service_info = wf_service_pool.get(service_id)
        if find_type == 'tar':
            mapper_info = service_info['params']['input']
        elif find_type == 'src':
            self._result_map[svr_param_id] = self._index + 1
            mapper_info = service_info['result']['output']
        else:
            return None

        for data_map in mapper_info:
            if data_map.get('key') == key:
                data_type = data_map.get('type')
                print(f"- [{find_type}]", splited_param_id, ":\t\t", data_map, "\t", data_type)
                return data_type
        return None

    def _add_data_type_on_data_mapper(self, data_mapper, wf_service_pool):
        for data_map in data_mapper:
            input_type = data_map.get('input_type')
            service_tar_key = data_map.get('tar')
            tar_data_type = self._get_data_type(service_tar_key, wf_service_pool, find_type='tar')
            data_map['tar'] = service_tar_key.split('.')[-1]
            data_map['tar_type'] = tar_data_type
            if input_type == 'refer':
                service_src_key = data_map.get('src')
                src_data_type = self._get_data_type(service_src_key, wf_service_pool, find_type='src')
                data_map['src_type'] = src_data_type
            elif input_type == 'value':
                src_value = data_map.get('src')
                service_tar_key = data_map.get('tar')
                data_map['src_type'] = (str(type(src_value))\
                    .replace('class', '')\
                    .replace('<', '')\
                    .replace('>', '')\
                    .replace("'", '')\
                    .replace(" ", ""))
        return data_mapper

    def cvt_service_edges(self, wf_config: Dict, wf_service_pool: Dict) -> Dict:
        def get_service_info(service_id):
            service_info = wf_service_pool.get(service_id)
            return service_info

        self._logger.critical("-" * 100)
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

        self._print_edges_map(edges_map)
        self._gen_params(edges_map)
        return edges_map


    def _cvt_type_casting(self, cvt_type: str, value: Any) -> Any:
        cvt_type = cvt_type.lower()
        if cvt_type in ['str', 'string']:
            return str(value)
        elif cvt_type in ['dict', 'json']:
            return str(value)
        elif cvt_type in ['int', 'integer']:
            return int(value)
        else:
            return str(value)

    def _gen_params(self, edges_map):
        for edge_id, edge_map in edges_map.items():
            data_mapper = edge_map.get("data_mapper")
            param_map = {}
            for data_map in data_mapper:
                input_type = data_map.get('input_type')
                param_name = data_map.get('tar')
                param_type = data_map.get('tar_type')
                if input_type == 'refer':
                    value_key = data_map.get('src')
                    value = self._result_map.get(value_key)
                    value_type = data_map.get('src_type')
                    param_map[param_name] = self._cvt_type_casting(param_type, value)
                elif input_type == 'value':
                    value = data_map.get('src')
                    param_map[param_name] = self._cvt_type_casting(param_type, value)
            print(edge_id, param_map)

    def _print_edges_map(self, edges_map: Dict) -> None:
        for k, v in edges_map.items():
            print("-", k)
            for vk, vv in v.items():
                if vk == 'data_mapper':
                    print("   ", vk, ":")
                    for vvv in vv:
                        print("        ", vvv)
                elif vk in ['source_info', 'target_info']:
                    print("   ", vk, ":")
                    if not vv:
                        print("        ", vv)
                    else:
                        for kvv, vvv in vv.items():
                            print("        ", kvv, ":", vvv)
                else:
                    print("   ", vk, ":", vv)
            print()

        for k, v in self._result_map.items():
            print(k, ":", v)

