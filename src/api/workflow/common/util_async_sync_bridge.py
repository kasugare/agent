#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from functools import wraps
from typing import Callable, Any
import threading
from concurrent.futures import ThreadPoolExecutor


class AsyncSyncBridge:
    """Sync와 Async 함수 간 호출을 위한 브릿지 (개선 버전)"""

    _loop = None
    _loop_thread = None
    _executor = ThreadPoolExecutor(max_workers=10)

    @classmethod
    def set_loop(cls, loop=None):
        if loop:
            cls._loop = loop
        else:
            try:
                cls._loop = asyncio.get_running_loop()
            except RuntimeError:
                cls._loop = asyncio.get_event_loop()

        cls._loop_thread = threading.current_thread()

    @classmethod
    def get_loop(cls):
        # 1. 이미 설정된 루프가 있으면 사용
        if cls._loop and cls._loop.is_running():
            return cls._loop

        # 2. 현재 스레드에 running loop가 있으면 사용
        try:
            loop = asyncio.get_running_loop()
            cls._loop = loop
            return loop
        except RuntimeError:
            pass

        # 3. 기본 이벤트 루프 사용
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            cls._loop = loop
            return loop
        except RuntimeError:
            # 4. 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cls._loop = loop
            return loop

    @classmethod
    def ensure_loop(cls):
        """이벤트 루프가 없으면 생성"""
        if cls._loop is None or cls._loop.is_closed():
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
        return cls._loop

    @staticmethod
    def sync_to_async(async_func: Callable, timeout: float = 30) -> Callable:
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            # 현재 스레드에서 이미 이벤트 루프가 실행 중인지 확인
            try:
                current_loop = asyncio.get_running_loop()
                # 이미 async 컨텍스트 안에 있음
                raise RuntimeError(
                    "Cannot use sync_to_async inside async context. "
                    "Use 'await async_func()' directly."
                )
            except RuntimeError:
                pass  # 이벤트 루프 없음 - 정상

            loop = AsyncSyncBridge.get_loop()
            coro = async_func(*args, **kwargs)

            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result(timeout=timeout)
            else:
                return loop.run_until_complete(coro)
        return wrapper

    @staticmethod
    def async_to_sync(sync_func: Callable) -> Callable:
        @wraps(sync_func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()

            # ThreadPoolExecutor를 사용하여 블로킹 방지
            return await loop.run_in_executor(
                AsyncSyncBridge._executor,
                lambda: sync_func(*args, **kwargs)
            )

        return wrapper

    @staticmethod
    def safe_sync_call(async_func: Callable, *args, timeout: float = 30, **kwargs):
        """
        Sync 컨텍스트에서 async 함수를 안전하게 호출

        사용법:
            result = AsyncSyncBridge.safe_sync_call(my_async_func, arg1, arg2, timeout=10)
        """
        try:
            # 현재 이벤트 루프 확인
            try:
                asyncio.get_running_loop()
                raise RuntimeError("Already in async context. Use 'await' instead.")
            except RuntimeError:
                pass

            # 이벤트 루프 가져오기
            loop = AsyncSyncBridge.get_loop()

            # 코루틴 생성
            coro = async_func(*args, **kwargs)

            # 실행
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result(timeout=timeout)
            else:
                return loop.run_until_complete(coro)

        except Exception as e:
            print(f"Error in safe_sync_call: {e}")
            raise

    @staticmethod
    async def safe_async_call(sync_func: Callable, *args, **kwargs):
        """
        Async 컨텍스트에서 sync 함수를 안전하게 호출

        사용법:
            result = await AsyncSyncBridge.safe_async_call(my_sync_func, arg1, arg2)
        """
        try:
            loop = asyncio.get_running_loop()

            return await loop.run_in_executor(
                AsyncSyncBridge._executor,
                lambda: sync_func(*args, **kwargs)
            )
        except Exception as e:
            print(f"Error in safe_async_call: {e}")
            raise
