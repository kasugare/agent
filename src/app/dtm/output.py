#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Output:
    def __init__(self, logger, asset_info):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    def output(self, result):
        self._logger.info("Output Node")
        self._logger.info(f" - {result}")

        return result
