#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Input:
    def __init__(self, logger, asset_info={}):
        self._logger = logger
        self._set_asset(**asset_info)

    def _set_asset(self):
        None

    def input(self, tar_path: list, call_back_url: str, call_back_error_url: str, user_id: str):
        self._logger.debug(f" # START NODE: {tar_path}")
        return tar_path, call_back_url, call_back_error_url, user_id