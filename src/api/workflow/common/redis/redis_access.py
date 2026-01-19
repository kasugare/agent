#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
import redis
import json


class RedisAccess:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger):
        self._logger = logger
        # self._redis_client = redis_client
        self._redis_client = redis.Redis(host='127.0.0.1', port='16379', decode_responses=True, dn=0)

    def __del__(self):
        if self._redis_client:
            self._redis_client.close()

    def hset(self, key: str, mapping: Dict) -> None:
        try:
            serializable_mapping = {k: str(v) for k, v in mapping.items()}
            self._redis_client.hset(name=key, mapping=serializable_mapping)
        except Exception as e:
            self._logger.error(f"Redis HSET failed: {e}")

    def hget(self, key: str, field: str):
        try:
            data = self._redis_client.hget(key, field)
            if data is None:
                return []
            return json.loads(data)
        except Exception as e:
            self._logger.error(f"Redis HGET failed: {e}")

    def hgetall(self, key: str):
        try:
            data = self._redis_client.hgetall(key)
            if data is None:
                return []
            return data or {}
        except Exception as e:
            self._logger.error(f"Redis HGETALL failed: {e}")

    def hdel(self, key: str, field: str):
        try:
            self._redis_client.hdel(key, field)
        except Exception as e:
            self._logger.error(f"Redis HDEL failed: {e}")

    def clear(self, key: str):
        try:
            self._redis_client.delete(key)
        except Exception as e:
            self._logger.error(f"Redis DELETE failed: {e}")

    def flush(self):
        pass