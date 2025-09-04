#!/usr/bin/env python
# -*- coding: utf-8 -*-


class DataTypeTransfer:
    def __init__(self, logger):
        self._logger = logger

    def trans_data_type(self, value, key_type, value_type):
        key_type = key_type.lower()
        value_type = value_type.lower()

        if key_type in ['str', 'string']:
            if value_type in ['integer', 'int']:
                value = int(value)
            elif value_type in ['double', 'float']:
                value = float(value)
            else:
                value = str(value)
        elif key_type in ['int', 'integer']:
            if value_type in ['integer', 'int']:
                value = int(value)
            elif value_type in ['double', 'float']:
                value = float(value)
            else:
                value = str(value)
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
        elif key_type in ['double', 'float']:
            value = float(value)
        elif key_type in ['dict', 'map', 'json']:
            value = dict(value)

        return value
