#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools

class TaskIOController:
    def __init__(self, logger):
        self._logger = logger

    def _trans_type_casting(self, value, key_type, value_type):
        key_type = key_type.lower()
        value_type = value_type.lower()

        if key_type in ['str', 'string']:
            value = str(value)
        elif key_type in ['int', 'integer']:
            pass
        elif key_type in ['list']:
            if value_type in ['list']:
                value = value
            elif value_type in ['str', 'string', 'int']:
                value = [value]
            elif value_type in ['set']:
                value = list(value)
        elif key_type in ['bytes']:
            if value_type in ['str', 'string']:
                value = bytes(value, 'utf-8')
        elif key_type in ['dict', 'map']:
            value = dict(value)
        elif key_type in ['json']:
            pass
        return value

    def set_input_meta(self, task_id, edge_nodes):
        data_mapper_list = list(itertools.chain(*[edge_meta.get('data_mapper') \
                          for k, edge_meta in edge_nodes.items() if edge_meta.get('data_mapper')]))
        for data_map in data_mapper_list:
            call_method = data_map.get('call_method')
            if call_method.lower() == 'value':
                key = data_map.get('key')
                value = data_map.get('value')
                key_type = data_map.get('key_type')
                value_type = data_map.get('value_type')

                value = self._trans_type_casting(value, key_type, value_type)
                # print(f" - {key}({key_type}) = {value}({type(value)}-{value_type})")
