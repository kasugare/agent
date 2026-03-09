#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.control.request.user_request_controller import UserRequestStoreController
from typing import Dict, Any


class UserRequestStoreService:
    def __init__(self, logger, cache_key):
        self._logger = logger
        self._request_controller = UserRequestStoreController(logger, cache_key)

    def clear(self):
        self._request_controller.clear_ctl()

    def clear_data(self):
        self._request_controller.clear_ctl()

    def set_cache_key_service(self, job_id):
        self._request_controller.set_cache_key_ctl(job_id)

    def set_user_params(self, params_map: Dict):
        self._request_controller.set_user_params_ctl(params_map)

    def get_user_params(self, job_id=None):
        user_parmas = self._request_controller.get_user_params_ctl(job_id)
        return user_parmas


