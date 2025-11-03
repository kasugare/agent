#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class DocumentsAggregator:
    def __init__(self, logger, asset_info):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    async def aggregate(self, inputs):
        data_context = []
        if isinstance(inputs, list):
            for input_param in inputs:
                for service_id, values in input_param.items():
                    data_context.extend(values)
        elif isinstance(inputs, dict):
            for service_id, values in inputs.items():
                data_context.extend(values)
        return data_context