#!/usr/bin/env python
# -*- coding: utf-8 -*-

from redis import Redis
from fastapi import Depends
from common.dependancy import get_redis_client
from api.workflow.common.redis.redis_access import RedisAccess


class RemoteCachedIODataAccess(RedisAccess):
    def __init__(self, logger):
        super().__init__(logger)
        self._logger = logger
        # self._project_id = redis_client_info.project_id
        # self._workflow_id = redis_client_info.workflow_id
        # self._redis_key = f"{self._project_id}-{self._workflow_id}.IOpool"
        self._redis_key = 'project1-workflow1.IOpool'


    # def set_redis_clint_info(self, clint_info):
    #     self._redis_client_info = clint_info
    #     self._project_id = clint_info.project_id
    #     self._workflow_id = clint_info.workflow_id
    #     self._redis_key = f"{self._project_id}-{self._workflow_id}.IOpool"

    def get_data(self, field):
        print("==========================")
        print(self._redis_client_info)
        print("==========================")
        return self.hget(key=self._redis_key, field=field)

    def get_all(self):
        self.hgetall(key=self._redis_key)

    def set_data(self, field, data):
        self.hset(key=self._redis_key, mapping={field: data})

    def delete(self, field):
        self.hdel(key=self._redis_key, field=field)

    def clear(self):
        self.clear(key=self._redis_key)
