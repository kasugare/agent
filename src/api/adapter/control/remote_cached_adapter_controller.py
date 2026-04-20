#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.access.connector.adapter_redis_access import AdapterRedisAccess
from api.adapter.access.remote_cached_adapter_result_access import RemoteCachedAdapterResultAccess


class RemoteCachedAdapterController:
    def __init__(self, logger):
        self._logger = logger
        self._adapter_access = RemoteCachedAdapterResultAccess(logger)

    def set_job_info_ctl(self, job_id, req_headers, tar_path, state, error_msg):
        context = {
            'state': state,
            'error_msg': error_msg,
            'header': req_headers,
            'tar_path': tar_path
        }
        self._adapter_access.set_job_info_access(job_id, context)

    def get_job_info_ctl(self, job_id):
        remote_store = AdapterRedisAccess(self._logger, db=10)
        key_pattern = f"*@{job_id}*"
        keys = remote_store.scan_keys(pattern=key_pattern, count=1, sort=True, reverse=True)
        if keys and keys[0].split("@")[-1] == job_id:
            key = keys[0]
            job_info = remote_store.hgetall(key)
        else:
            return {}
        return job_info

    def set_job_state_ctl(self, job_id, state, error_msg):
        self._adapter_access.set_job_state_access(job_id, state, error_msg)

    def get_job_status_ctl(self, job_id):
        job_status = self._adapter_access.get_job_status_access(job_id)
        return job_status

