#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess


class RemoteTaskServiceAccess(RedisAccess):
    def __init__(self, logger, cache_key=None):
        super().__init__(logger, db=2, ttl=2592000)
        self._cache_key = cache_key

    def set_cache_key_access(self, cache_key):
        self._cache_key = cache_key

    def set_task_map_access(self, task_map) -> None:
        self.hset(key=self._cache_key, mapping=task_map)

    def get_task_map_access(self):
        self.hgetall(key=self._cache_key)

    def set_data_access(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})

    def set_mapping_data(self, data_map: dict):
        self.hset(key=self._cache_key, mapping=data_map)

    def get_data(self, field):
        return self.hget(key=self._cache_key, field=field)