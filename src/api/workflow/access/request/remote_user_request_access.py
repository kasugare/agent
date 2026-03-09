#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess
import datetime
import pytz
import time


class RemoteCachedUserRequestAccess(RedisAccess):
    def __init__(self, logger, cache_key=None):
        super().__init__(logger, db=10, ttl=2592000)
        self._logger = logger
        self._cache_key = cache_key

    def set_cache_key_access(self, cache_key):
        self._cache_key = f"{cache_key}"

    def get_data(self, field):
        return self.hget(key=self._cache_key, field=field)

    def get_all(self, job_id=None):
        if not job_id:
            job_id = self._cache_key
        result = self.hgetall(key=job_id)
        return result

    def set_data(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})
        ts = int(time.time())
        try:
            date_time = datetime.datetime.fromtimestamp(ts, pytz.utc).strftime('%Y-%m-%d_%H:%M:%S')
            time_key = f"{date_time}-{self._cache_key}"
            self.hset(key=time_key, mapping={field: data})
        except:
            pass

    def delete(self, field):
        self.hdel(key=self._cache_key, field=field)

    def clear_access(self):
        self.clear(key=self._cache_key)
