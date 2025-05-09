#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.serving.control.task_io_controller import TaskIOController

class TaskIOService:
    def __init__(self, logger):
        self._logger = logger
        self._io_handler = TaskIOController(logger)

    def set_init_meta(self, task_id, edge_nodes):
        self._io_handler.set_input_meta(task_id, edge_nodes)

    def set_input_data(self):
        pass

    def set_output_data(self):
        pass

    def get_input_data(self):
        pass

    def get_output_data(self):
        pass