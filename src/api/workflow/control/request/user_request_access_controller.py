#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getAccessPoolType
from api.workflow.access.request.remote_user_request_access import RemoteCachedUserRequestAccess


class UserRequestAccessController:
    def __init__(self, logger):
        self._logger = logger
        self._access_type = str(getAccessPoolType()).lower()

    def get_data_access_instance(self):
        if self._access_type == 'remote':
            return RemoteCachedUserRequestAccess(self._logger)
        else:
            self._logger.error(f"Access type is None")
            return None
