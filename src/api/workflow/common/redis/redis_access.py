#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRemoteConnInfo
from typing import Dict, Any
import redis
import json


class RedisAccess:
    def __init__(self, logger, db=0, ttl=0):
        self._logger = self._db = self._ttl = ttl
        redis_conn = getRemoteConnInfo()
        self._host = redis_conn.get('host')
        self._port = redis_conn.get('port')
        self._passwd = redis_conn.get('passwd')
        self._redis_client = redis.Redis(host=self._host,
        		port=self._port,
        		password=self._passwd,
        		decode_responses=True,
        		db=db)

    def __del__(self):
        if self._redis_client:
            self._redis_client.close()

    def get_db(self):
        return self._db

    def hset(self, key: str, mapping: Dict) -> None:
        try:
            ttl_seconds = self._ttl
            # dict/list는 JSON으로, 나머지는 str로 변환
            serializable_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serializable_mapping[k] = json.dumps(v)
                else:
                    serializable_mapping[k] = str(v)

            self._redis_client.hset(name=key, mapping=serializable_mapping)
            if ttl_seconds > 0:
                self._redis_client.expire(key, ttl_seconds)
        except Exception as e:
            self._logger.error(f"Redis HSET failed: {e}")

    def hget(self, key: str, field: str):
        try:
            data = self._redis_client.hget(key, field)
            if data is None:
                return None

            # JSON 파싱 시도
            try:
                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                # JSON이 아니면 원본 문자열 반환
                return data
        except Exception as e:
            self._logger.error(f"Redis HGET failed: {e}")
            return None

    def hgetall(self, key: str) -> Dict[str, Any]:
        try:
            data = self._redis_client.hgetall(key)
            if not data:
                return {}

            # 모든 값을 역직렬화 (JSON 파싱 시도)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    # JSON이 아니면 원본 문자열
                    result[k] = v

            return result
        except Exception as e:
            self._logger.error(f"Redis HGETALL failed: {e}")
            return {}

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