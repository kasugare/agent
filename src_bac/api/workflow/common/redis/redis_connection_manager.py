#!/usr/bin/env python
# -*- coding: utf-8 -*-

from redis.sentinel import Sentinel
from common.conf_system import getAccessPoolType
import redis


class RedisConnectionManager:
    def __init__(self, logger, sentinel_hosts_str: str, redis_master_name: str, redis_databases: int = 0, redis_password: str | None = None):
        self._logger = logger
        self._sentinel_hosts_str = sentinel_hosts_str
        self._redis_master_name = redis_master_name
        self._redis_password = redis_password
        self._redis_databases = redis_databases
        self._access_type = str(getAccessPoolType()).lower()

    def create_redis_client(self):
        try:
            # Sentinel이 설정된 경우
            if self._sentinel_hosts_str:
                endpoints = []
                for host_port in self._sentinel_hosts_str.split(","):
                    host, port = host_port.strip().split(":")
                    endpoints.append((host, int(port)))

                sentinel = Sentinel(
                    endpoints,
                    socket_timeout=5,
                    password=self._redis_password,
                    decode_responses=True,
                )
                redis_client = sentinel.master_for(
                    self._redis_master_name,
                    db=self._redis_databases,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    max_connections=10,
                )
                self._logger.info(
                    f"Connected to Redis via Sentinel master '{self._redis_master_name}' (DB {self._redis_databases})"
                )
            else:
                # Sentinel이 없으면 로컬 Redis 직접 연결
                redis_client = redis.Redis(
                    host="ailand.ai",
                    port=30379,
                    password='mypassword',
                    db=self._redis_databases,
                    decode_responses=True,
                )
                self._logger.info(
                    f"Connected directly to local Redis (DB {self._redis_databases})"
                )

            # 공통 PING 체크
            if redis_client.ping():
                return redis_client
            else:
                self._logger.error("PING failed after connecting to Redis.")
                return None

        except Exception as e:
            self._logger.error(f"Error while connecting to Redis: {e}", exc_info=True)
            return None


