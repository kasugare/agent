#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRemoteConnInfo
from typing import Dict, Any, Callable, Optional
import threading
import redis
import json


class RedisConnector:
    """DB별 Pub/Sub 격리를 지원하는 Redis Connector"""

    def __init__(self, logger, db=0, ttl=0, reload=False, isolate_pubsub=True):
        self._logger = logger
        self._db = db
        self._ttl = ttl
        self._reload = reload
        self._isolate_pubsub = isolate_pubsub  # DB별 격리 여부

        redis_conn = getRemoteConnInfo()
        self._host = redis_conn.get('host')
        self._port = redis_conn.get('port')
        self._passwd = redis_conn.get('passwd')

        self._redis_client = redis.Redis(
            host=self._host,
            port=self._port,
            password=self._passwd,
            decode_responses=True,
            db=db
        )

        # Pub/Sub 관련
        self._pubsub = None
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._subscriptions: Dict[str, Callable] = {}

        if self._reload:
            mode = "DB-isolated" if self._isolate_pubsub else "global"
            self._logger.info(f"Redis Pub/Sub enabled (mode: {mode}, db: {db})")

    def __del__(self):
        if self._reload:
            self.stop_listening()
        if self._redis_client:
            self._redis_client.close()

    # ============ 기존 기능들 ============

    def get_db(self):
        return self._db

    def is_reload_enabled(self) -> bool:
        return self._reload

    def _get_namespaced_channel(self, channel: str) -> str:
        """DB별 격리가 활성화된 경우 채널 이름에 DB prefix 추가"""
        if self._isolate_pubsub:
            return f"db{self._db}:{channel}"
        return channel

    def _strip_namespace(self, namespaced_channel: str) -> str:
        """DB prefix 제거"""
        if self._isolate_pubsub:
            prefix = f"db{self._db}:"
            if namespaced_channel.startswith(prefix):
                return namespaced_channel[len(prefix):]
        return namespaced_channel

    def hset(self, key: str, mapping: Dict) -> None:
        try:
            ttl_seconds = self._ttl
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

    def hset_replace(self, key: str, mapping: Dict) -> None:
        try:
            self._redis_client.delete(key)
            self.hset(key, mapping)
        except Exception as e:
            self._logger.error(f"Redis HSET_REPLACE failed: {e}")

    def hsetall_from_dict(self, key: str, data_map: Dict):
        try:
            mapping = {}
            for field, value in data_map.items():
                if isinstance(value, (dict, list)):
                    mapping[field] = json.dumps(value)
                else:
                    mapping[field] = str(value)

            self._redis_client.hset(name=key, mapping=mapping)
            if self._ttl > 0:
                self._redis_client.expire(key, self._ttl)

            self._logger.debug(f"Redis HSET_FROM_JSON key: {key}, fields: {list(mapping.keys())}")
        except Exception as e:
            self._logger.error(f"Redis HSET_FROM_JSON failed: {e}")

    def hget(self, key: str, field: str):
        try:
            data = self._redis_client.hget(key, field)
            if data is None:
                return None

            try:
                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                return data
        except Exception as e:
            self._logger.error(f"Redis HGET failed: {e}")
            return None

    def hgetall(self, key: str) -> Dict[str, Any]:
        try:
            data = self._redis_client.hgetall(key)
            if not data:
                return {}

            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, ValueError):
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
        if self._reload and self._pubsub:
            self._logger.warning(f"Switching DB from {self._db} to {db} - stopping subscriptions")
            self.stop_listening()

        self._redis_client = redis.Redis(
            host=self._host,
            port=self._port,
            password=self._passwd,
            decode_responses=True,
            db=db
        )
        self._db = db

    def flush(self):
        self._logger.critical(f"Redis flushed DB: {self._db}")
        self._redis_client.flushdb()

    # ============ Pub/Sub 기능 (DB별 격리 지원) ============

    def _check_reload_enabled(self, method_name: str) -> bool:
        if not self._reload:
            self._logger.warning(
                f"{method_name} is only available when reload=True. "
                f"Initialize RedisConnector with reload=True to use Pub/Sub features."
            )
            return False
        return True

    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """메시지 발행 (DB별 격리 지원)"""
        if not self._check_reload_enabled("publish"):
            return 0

        try:
            # DB별 격리가 활성화된 경우 채널 이름 변환
            actual_channel = self._get_namespaced_channel(channel)
            json_message = json.dumps(message)
            result = self._redis_client.publish(actual_channel, json_message)

            if self._isolate_pubsub:
                self._logger.info(
                    f"Published to '{channel}' (actual: '{actual_channel}', "
                    f"DB: {self._db}, subscribers: {result})"
                )
            else:
                self._logger.info(
                    f"Published to '{channel}' (global, subscribers: {result})"
                )

            return result
        except Exception as e:
            self._logger.error(f"Redis PUBLISH failed: {e}")
            return 0

    def subscribe(self, channel: str, callback: Callable[[Dict], None]) -> None:
        """채널 구독 (DB별 격리 지원)"""
        if not self._check_reload_enabled("subscribe"):
            return

        try:
            if self._pubsub is None:
                self._pubsub = self._redis_client.pubsub()

            # DB별 격리가 활성화된 경우 채널 이름 변환
            actual_channel = self._get_namespaced_channel(channel)
            self._pubsub.subscribe(actual_channel)

            # 원본 채널 이름으로 저장 (사용자 편의)
            self._subscriptions[channel] = {
                'callback': callback,
                'actual_channel': actual_channel
            }

            if self._isolate_pubsub:
                self._logger.info(
                    f"Subscribed to '{channel}' (actual: '{actual_channel}', DB: {self._db})"
                )
            else:
                self._logger.info(f"Subscribed to '{channel}' (global)")

            if self._listener_thread is None or not self._listener_thread.is_alive():
                self._start_listener()

        except Exception as e:
            self._logger.error(f"Redis SUBSCRIBE failed: {e}")

    def unsubscribe(self, channel: str) -> None:
        """채널 구독 해제"""
        if not self._check_reload_enabled("unsubscribe"):
            return

        try:
            if self._pubsub and channel in self._subscriptions:
                actual_channel = self._subscriptions[channel]['actual_channel']
                self._pubsub.unsubscribe(actual_channel)
                del self._subscriptions[channel]
                self._logger.info(f"Unsubscribed from '{channel}'")

                if not self._subscriptions:
                    self.stop_listening()
        except Exception as e:
            self._logger.error(f"Redis UNSUBSCRIBE failed: {e}")

    def _start_listener(self) -> None:
        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_messages,
            daemon=True
        )
        self._listener_thread.start()
        self._logger.info("Redis Pub/Sub listener started")

    def _listen_messages(self) -> None:
        self._logger.info("Listening for Redis Pub/Sub messages...")

        try:
            for message in self._pubsub.listen():
                if not self._running:
                    break

                if message['type'] == 'message':
                    actual_channel = message['channel']

                    try:
                        data = json.loads(message['data'])

                        # actual_channel을 원본 채널로 역변환
                        original_channel = None
                        for ch, info in self._subscriptions.items():
                            if info['actual_channel'] == actual_channel:
                                original_channel = ch
                                break

                        if original_channel:
                            self._logger.debug(
                                f"Received from '{original_channel}' "
                                f"(DB: {self._db}): {data}"
                            )
                            callback = self._subscriptions[original_channel]['callback']
                            callback(data)

                    except json.JSONDecodeError:
                        self._logger.warning(
                            f"Failed to decode message from '{actual_channel}': {message['data']}"
                        )
                    except Exception as e:
                        self._logger.error(f"Callback error for '{actual_channel}': {e}")

        except Exception as e:
            self._logger.error(f"Listener error: {e}")
        finally:
            self._logger.info("Redis Pub/Sub listener stopped")

    def stop_listening(self) -> None:
        if not self._reload:
            return

        self._running = False

        if self._pubsub:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
                self._pubsub = None
            except Exception as e:
                self._logger.error(f"Error closing pubsub: {e}")

        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2)

        self._subscriptions.clear()
        self._logger.info("All subscriptions stopped")

    def get_subscriptions(self) -> list:
        """현재 구독 중인 채널 목록 (원본 채널명)"""
        if not self._reload:
            return []
        return list(self._subscriptions.keys())