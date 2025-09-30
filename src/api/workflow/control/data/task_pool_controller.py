#!/usr/bin/env python
# -*- coding: utf-8 -*-
from api.workflow.control.task.task_pool_access_controller import TaskPoolAccessController


class TaskPoolController:
    def __init__(self, logger):
        self._task_pool_access_controller = TaskPoolAccessController(logger)
        self._task_pool_access = self._task_pool_access_controller.get_task_access_instance()

    def set_task_map_control(self, task_map):
        self._task_pool_access.set_task_map_access(task_map)

    def get_task_map_control(self):
        task_map = self._task_pool_access.get_task_map_access()
        return task_map