#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.adapter.access.connector.adapter_redis_access import AdapterRedisAccess


class RemoteCachedAdapterResultAccess(AdapterRedisAccess):
    def __init__(self, logger):
        super().__init__(logger, db=11, ttl=2592000)

    def set_job_info_access(self, job_id, context):
        self.hset(key=job_id, mapping=context)

    def get_job_info_access(self, job_id):
        job_info = self.hgetall(key=job_id)
        return job_info

    def set_job_state_access(self, job_id, state, error_msg=None):
        self.hset(key=job_id, mapping={"state": state, 'error_msg': error_msg})

    def get_job_status_access(self, job_id):
        job_status = self.hgetall(key=job_id)
        return job_status

    def clear_access(self):
        self.flush()
