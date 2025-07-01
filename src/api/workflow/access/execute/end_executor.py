#!/usr/bin/env python
# -*- coding: utf-8 -*-

class EndExecutor:
    def __init__(self, logger):
        self._logger = logger
        self._params = None

    def set_params(self, params):
        self._params = params

    def run(self, params):
        return params