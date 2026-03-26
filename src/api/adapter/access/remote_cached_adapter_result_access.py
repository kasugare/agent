#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from typing import Dict, List
from api.adapter.access.adapter_redis_access import AdapterRedisAccess


class RemoteCachedAdapterResultAccess(AdapterRedisAccess):
    def __init__(self, logger):
        super().__init__(logger, db=4, ttl=2592000)

    def set_job_info_access(self, job_id, context):
        self.hset(key=job_id, mapping=context)

    def set_job_state_access(self, job_id, state, error_msg=None):
        self.hset(key=job_id, mapping={"state": state, 'error_msg': error_msg})

    def get_job_status_ctl(self, job_id):
        return self.hgetall(key=job_id)

    def clear_access(self):
        self.flush()
