#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.workflow.common.redis.redis_manager import RedisManager
from fastapi import Request, HTTPException, status
from redis.client import Redis

# -------------------------
# 앱 시작 시 호출 (startup)
# -------------------------
def create_redis_client(
    sentinel_hosts_str=None,
    redis_master_name=None,
    redis_password=None,
    redis_databases=0,
):
    factory = RedisManager(
        sentinel_hosts_str=sentinel_hosts_str,
        redis_master_name=redis_master_name,
        redis_password=redis_password,
        redis_databases=redis_databases,
    )
    client = factory.create_redis_client()
    if client is None:
        raise RuntimeError("Redis client creation failed")
    return client

# -------------------------
# 요청 시 주입
# -------------------------
def get_redis_client(name: str = "meta"):
    print(name)
    def _get_client(request: Request) -> Redis:
        clients = getattr(request.app.state, "redis_clients", None)
        if not clients or name not in clients:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Redis client '{name}' is not available."
            )
        return clients[name]
    return _get_client
