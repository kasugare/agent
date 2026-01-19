#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess


class RemoteCachedTaskPoolAccess(RedisAccess):
    def __init__(self, logger):
        super().__init__(logger)
        self._redis_key = 'project1-workflow1.taskpool'

    def set_task_map_access(self, task_map) -> None:
        self.hset(key=self._redis_key, mapping=task_map)

    def get_task_map_access(self):
        self.hgetall(key=self._redis_key)
