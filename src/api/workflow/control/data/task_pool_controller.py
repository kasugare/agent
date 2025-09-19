#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.access.data.cached_taskpool_access import CachedTaskPoolAccess
from typing import Dict
import threading


class TaskPoolController:
    def __init__(self, logger):
        self._cached_taskpool_access = CachedTaskPoolAccess(logger)

    def set_task_map_control(self, task_map): # #--
        self._cached_taskpool_access.set_task_map_access(task_map)

    def get_task_map_control(self): # <--
        task_map = self._cached_taskpool_access.get_task_map_access()
        return task_map