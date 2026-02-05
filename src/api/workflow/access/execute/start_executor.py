#!/usr/bin/env python
# -*- coding: utf-8 -*-

class StartExecutor:
    def __init__(self, logger):
        self._logger = logger
        self._env_params = {}
        self._asset_params = {}
        self._params = None

    def set_env(self, env_params):
        self._env_params = env_params

    def set_asset(self, asset_params):
        self._asset_params = asset_params

    def get_env(self):
        return self._env_params

    def get_asset(self):
        return self._asset_params

    def run(self, params):
        return params