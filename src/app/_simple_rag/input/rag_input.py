#!/usr/bin/env python
# -*- coding: utf-8 -*-

class RagInput:
    def __init__(self, logger):
        self._logger = logger

    def query_input(self, query: str) -> str:
        return query