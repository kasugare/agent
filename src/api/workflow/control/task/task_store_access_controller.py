#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getAccessPoolType
from api.workflow.access.task.cached_task_store_access import CachedTaskPoolAccess
from api.workflow.access.task.remote_task_store_access import RemoteTaskStoreAccess


class TaskStoreAccessController:
    def __init__(self, logger, cache_key):
        self._logger = logger
        self._cache_key = cache_key
        self._access_type = str(getAccessPoolType()).lower()

    def get_task_access_instance(self):
        if self._access_type == 'local':
            return CachedTaskPoolAccess(self._logger)
        elif self._access_type == 'remote':
            return RemoteTaskStoreAccess(self._logger, self._cache_key)
        else:
            self._logger.error(f"Access type is None")
            return None

