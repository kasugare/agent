#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess


class RemoteCachedIODataAccess(RedisAccess):
    def __init__(self, logger, cache_key=None):
        super().__init__(logger, db=1, ttl=2592000)
        self._logger = logger
        self._cache_key = cache_key

    def set_cache_key_access(self, cache_key):
        self._cache_key = f"{cache_key}"

    def get_data(self, field):
        return self.hget(key=self._cache_key, field=field)

    def get_all(self):
        result = self.hgetall(key=self._cache_key)
        return result

    def set_data(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})

    def delete(self, field):
        self.hdel(key=self._cache_key, field=field)

    def clear_access(self):
        self.clear(key=self._cache_key)
