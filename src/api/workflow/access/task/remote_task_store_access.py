#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess
from functools import wraps


class RemoteTaskStoreAccess(RedisAccess):
    def __init__(self, logger, cache_key=None):
        super().__init__(logger, db=3, ttl=2592000)
        self._cache_key = cache_key

    def with_generated_key(func):
        @wraps(func)
        def wrapper(self, service_id, *args, **kwargs):
            key = f"{self._cache_key}-{service_id}"
            return func(self, key, *args, **kwargs)
        return wrapper

    def set_cache_key_access(self, cache_key):
        self._cache_key = cache_key

    def set_data_access(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})

    def set_field_data_access(self, service_id, field, data):
        key = self._gen_key(service_id)
        self.hset(key=key, mapping={field: data})

    def set_mapping_data_access(self, service_id, data_map: dict):
        key = self._gen_key(service_id)
        self.hset(key=key, mapping=data_map)

    @with_generated_key
    def set_env_param_access(self, key, env_params):
        self.hset(key=key, mapping={"env_params": env_params})

    @with_generated_key
    def set_asset_param_access(self, key, asset_params):
        self.hset(key=key, mapping={"asset_params": asset_params})

    @with_generated_key
    def set_param_access(self, key, params):
        self.hset(key=key, mapping={"params": params})

    @with_generated_key
    def set_result_access(self, key, result):
        self.hset(key=key, mapping={"result": result})

    @with_generated_key
    def set_error_msg_access(self, key, error_msg):
        self.hset(key=key, mapping={"error_msg": error_msg})

    @with_generated_key
    def set_state_access(self, key, state):
        self.hset(key=key, mapping={"state": state})

    @with_generated_key
    def set_handler_access(self, key, handler):
        self.hset(key=key, mapping={"handler": handler})

