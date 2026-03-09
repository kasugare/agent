#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getAccessPoolType
from api.workflow.control.request.user_request_access_controller import UserRequestAccessController
from typing import Dict, Any


class UserRequestStoreController:
    def __init__(self, logger, cache_key=None):
        self._logger = logger
        self._access_type = str(getAccessPoolType()).lower()

        self._user_request_access_controller = UserRequestAccessController(logger)
        self._user_request_access = self._user_request_access_controller.get_data_access_instance()
        if cache_key:
            self.set_cache_key_ctl(cache_key)

    def set_cache_key_ctl(self, cache_key):
        self._user_request_access.set_cache_key_access(cache_key)

    def clear_ctl(self):
        self._user_request_access.clear_access()

    def set_user_params_ctl(self, params_map: Dict):
        for key, values in params_map.items():
            self._user_request_access.set_data(key, values)

    def get_user_params_ctl(self, job_id=None):
        user_parmas = self._user_request_access.get_all(job_id)
        return user_parmas

