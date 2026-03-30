#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.launcher.route_meta.access.connector.redis_connector import RedisConnector
from typing import Dict, Any, Callable, Optional
import asyncio
import json


class AsyncRedisConnector(RedisConnector):
    """비동기 Pub/Sub 지원 (DB별 격리)"""

    def __init__(self, logger, db=0, ttl=0, reload=False, isolate_pubsub=True):
        super().__init__(logger, db, ttl, reload, isolate_pubsub)
        self._async_running = False

    async def publish_async(self, channel: str, message: Dict[str, Any]) -> int:
        """비동기 메시지 발행"""
        if not self._check_reload_enabled("publish_async"):
            return 0

        return self.publish(channel, message)

    async def subscribe_async(self, channel: str, callback: Callable[[Dict], None]) -> None:
        """비동기 채널 구독"""
        if not self._check_reload_enabled("subscribe_async"):
            return

        try:
            if self._pubsub is None:
                self._pubsub = self._redis_client.pubsub()

            actual_channel = self._get_namespaced_channel(channel)
            self._pubsub.subscribe(actual_channel)

            self._subscriptions[channel] = {
                'callback': callback,
                'actual_channel': actual_channel
            }

            self._logger.info(f"Async subscribed to '{channel}' (DB: {self._db})")

            if not self._async_running:
                asyncio.create_task(self._listen_messages_async())

        except Exception as e:
            self._logger.error(f"Async subscribe failed: {e}")

    async def _listen_messages_async(self) -> None:
        self._async_running = True
        self._logger.info("Async listening started...")

        try:
            while self._async_running:
                message = self._pubsub.get_message(ignore_subscribe_messages=True)

                if message and message['type'] == 'message':
                    actual_channel = message['channel']

                    try:
                        data = json.loads(message['data'])

                        # 원본 채널 찾기
                        original_channel = None
                        for ch, info in self._subscriptions.items():
                            if info['actual_channel'] == actual_channel:
                                original_channel = ch
                                break

                        if original_channel:
                            self._logger.debug(f"Async received from '{original_channel}': {data}")
                            callback = self._subscriptions[original_channel]['callback']

                            if asyncio.iscoroutinefunction(callback):
                                await callback(data)
                            else:
                                callback(data)

                    except Exception as e:
                        self._logger.error(f"Async callback error: {e}")

                await asyncio.sleep(0.01)

        except Exception as e:
            self._logger.error(f"Async listener error: {e}")
        finally:
            self._async_running = False
            self._logger.info("Async listening stopped")

    async def stop_listening_async(self) -> None:
        if not self._reload:
            return

        self._async_running = False
        await asyncio.sleep(0.1)
        self.stop_listening()