#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getAccessPoolType
from api.workflow.access.data.cached_taskpool_access import CachedTaskPoolAccess
from api.workflow.access.data.remote_cached_taskpool_access import RemoteCachedTaskPoolAccess


class TaskPoolAccessController:
    def __init__(self, logger):
        self._logger = logger
        self._access_type = str(getAccessPoolType()).lower()

    def get_task_access_instance(self):
        if self._access_type == 'local':
            return CachedTaskPoolAccess(self._logger)
        elif self._access_type == 'remote':
            return RemoteCachedTaskPoolAccess(self._logger)
        else:
            self._logger.error(f"Access type is None")
            return None

