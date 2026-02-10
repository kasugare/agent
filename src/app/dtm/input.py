#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Input:
    def __init__(self, logger, asset_info={}):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    def input(self, tar_path: str) -> str:
        self._logger.debug(f" # START NODE: {tar_path}")
        return tar_path