#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from copy import deepcopy
import threading


class CachedTaskPoolAccess:
    def __init__(self, logger):
        self._logger = logger
        self._thread_lock = threading.Lock()
        self._task_pool = {}

    def set_task_map_access(self, task_map: Dict[str, Any]) -> None:
        self._task_pool = task_map

    def get_task_map_access(self):
        return self._task_pool

    def clear_access(self):
        try:
            self._thread_lock.acquire()
            self._task_pool.clear()
        except Exception as e:
            self._data_pool = {}
        finally:
            self._thread_lock.release()

