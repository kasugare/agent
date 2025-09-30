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
        self._cache_key = None

    def set_cache_key_access(self, wf_key):
        self._cache_key = f"{wf_key}.IOpool"

    def get_data(self, field):
        return self.hget(key=self._cache_key, field=field)

    def get_all(self):
        self.hgetall(key=self._cache_key)

    def set_data(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})

    def delete(self, field):
        self.hdel(key=self._cache_key, field=field)

    def clear(self):
        self.clear(key=self._cache_key)

    def clear_access(self):
        pass
