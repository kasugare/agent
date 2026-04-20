#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.control.remote_cached_adapter_controller import RemoteCachedAdapterController


class RemoteCachedAdapterService:
    def __init__(self, logger):
        self._logger = logger
        self._adapter_controller = RemoteCachedAdapterController(logger)

    def set_job_info(self, job_id, req_headers, tar_path, state, error_msg=''):
        self._adapter_controller.set_job_info_ctl(job_id, req_headers, tar_path, state, error_msg)

    def get_job_info(self, job_id):
        job_params = self._adapter_controller.get_job_info_ctl(job_id)
        return job_params

    def set_job_state(self, job_id, state, error_msg=""):
        self._adapter_controller.set_job_state_ctl(job_id, state, error_msg)

    def get_job_status(self, job_id):
        job_status = self._adapter_controller.get_job_status_ctl(job_id)
        return job_status
