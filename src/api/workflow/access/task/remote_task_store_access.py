#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_access import RedisAccess
from functools import wraps
import time


class RemoteTaskStoreAccess(RedisAccess):
    def __init__(self, logger, cache_key=None):
        super().__init__(logger, db=3, ttl=2592000)
        self._cache_key = cache_key

    def set_cache_key_access(self, cache_key):
        self._cache_key = cache_key

    def set_data_access(self, field, data):
        self.hset(key=self._cache_key, mapping={field: data})

    def set_field_data_access(self, key, field, data):
        self.hset(key=key, mapping={field: data})

    def set_mapping_data_access(self, key, data_map: dict):
        self.hset(key=key, mapping=data_map)

    def set_start_ts_access(self, key):
        self.hset(key=key, mapping={"start_ts": time.time()})

    def set_end_ts_access(self, key):
        self.hset(key=key, mapping={"end_ts": time.time()})

    def set_duration_ts_access(self, key, duration_ts):
        self.hset(key=key, mapping={"duration_ts": duration_ts})

    def set_env_param_access(self, key, env_params):
        self.hset(key=key, mapping={"env_params": env_params})

    def set_asset_param_access(self, key, asset_params):
        self.hset(key=key, mapping={"asset_params": asset_params})

    def set_param_access(self, key, params):
        self.hset(key=key, mapping={"params": params})

    def set_result_access(self, key, result):
        self.hset(key=key, mapping={"result": result})

    def set_error_msg_access(self, key, error_msg):
        self.hset(key=key, mapping={"error_msg": error_msg})

    def set_state_access(self, key, state):
        self.hset(key=key, mapping={"state": state})

    def set_handler_access(self, key, handler):
        self.hset(key=key, mapping={"handler": handler})

    def get_assigned_ts_access(self, key):
        return self.hget(key=key, field='assigned_ts')

    def get_start_ts_access(self, key):
        return self.hget(key=key, field='start_ts')

    def get_end_ts_access(self, key):
        return self.hget(key=key, field='end_ts')

    def get_env_params_access(self, key):
        return self.hget(key=key, field='env_params')

    def get_asset_params_access(self, key):
        return self.hget(key=key, field='asset_params')

    def get_params_access(self, key):
        return self.hget(key=key, field='params')

    def get_result_access(self, key):
        return self.hget(key=key, field='result')

    def get_error_msg_access(self, key):
        return self.hget(key=key, field='error_msg')

    def get_state_access(self, key):
        return self.hget(key=key, field='state')

    def get_handler_access(self, key):
        return self.hget(key=key, field='handler')