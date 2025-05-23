#!/usr/bin/env python
# -*- coding: utf-8 -*-

class TaskIOAccess:
    def __init__(self, logger):
        self._logger = logger
        self._io_pool = {}

    def clear(self):
        try:
            self._io_pool.clear()
        except Exception as e:
            self._logger.error(e)

    def set_input_params(self):
        pass

    def set_output_params(self):
        pass

    def get_input_params(self):
        pass

    def get_output_params(self):
        pass
