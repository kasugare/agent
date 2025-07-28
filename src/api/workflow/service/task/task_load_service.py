#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.task.task_load_controller import TaskLoadController


class TaskLoadService:
    def __init__(self, logger, datastore):
        self._logger = logger
        self._task_controller = TaskLoadController(logger, datastore)

    def gen_init_tasks_service(self):
        task_map = self._task_controller.make_task_map()
        return task_map

    def gen_active_tasks_service(self, act_service_ids=[]):
        task_map = self._task_controller.make_task_map(act_service_ids)
        return task_map
