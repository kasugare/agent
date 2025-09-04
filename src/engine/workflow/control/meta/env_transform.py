#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class EnvironmentsTransformer:
    def __init__(self, logger):
        self._logger = logger

    def cvt_node_env_value_map_ctl(self, wf_service_pool) -> dict:
        nodes_env_value_map = {}
        for service_id, service_info in wf_service_pool.items():
            node_type = service_info.get('node_type')
            class_info = service_info.get('class_info')
            if node_type == 'class':
                env_info = class_info.get('environments')
                if not env_info:
                    continue
                env_map_list = env_info.get('input')
                if not env_map_list:
                    continue
                for env_map in env_map_list:
                    env_name = env_map.get('key')
                    env_id = f"{service_id}.{env_name}"
                    env_value = env_map.get('value')
                    nodes_env_value_map[env_id] = env_value
            else:
                continue
        return nodes_env_value_map

