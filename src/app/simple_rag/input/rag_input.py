#!/usr/bin/env python
# -*- coding: utf-8 -*-

class RagInput:
    def __init__(self, logger, asset_info={}):
        self._logger = logger

    def query_input(self, query: str) -> str:
        return query

    def _set_asset(self):
        None