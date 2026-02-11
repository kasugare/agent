#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
import redis
import json


class RedisAccess:
    def __init__(self, logger, db=0, ttl=0):
        self._logger = logger
        self._db = db
        self._ttl = ttl
        self._host = '127.0.0.1'
        self._port = 6379
        self._redis_client = redis.Redis(host=self._host, port=self._port, decode_responses=True, db=db)

    def __del__(self):
        if self._redis_client:
            self._redis_client.close()

    def get_db(self):
        return self._db

    def hset(self, key: str, mapping: Dict) -> None:
        try:
            ttl_seconds = self._ttl
            serializable_mapping = {k: str(v) for k, v in mapping.items()}
            self._redis_client.hset(name=key, mapping=serializable_mapping)
            if ttl_seconds > 0:
                self._redis_client.expire(key, ttl_seconds)
            # pipe = self._redis_client.pipeline()
            # pipe.hset(name=key, mapping=serializable_mapping)
            # pipe.expire(key, ttl_seconds)
            # pipe.execute()
        except Exception as e:
            self._logger.error(f"Redis HSET failed: {e}")

    def hget(self, key: str, field: str):
        try:
            data = self._redis_client.hget(key, field)
            if data is None:
                return None
            result = None
            try:
                result = json.loads(data)
            except Exception as e:
                if isinstance(data, str) and len(data) > 0:
                    result = data
            return result
        except Exception as e:
            self._logger.error(f"Redis HGET failed: {e}")

    def hgetall(self, key: str):
        try:
            data = self._redis_client.hgetall(key)
            if data is None:
                return None
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

    def switch_db(self, db):
        """DB 변경"""
        self._redis_client = redis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=True,
            db=db
        )
        self._db = db

    def flush(self):
        self._logger.critical(f"Redis flushed DB: {self._db}")
        self._redis_client.flushdb()
