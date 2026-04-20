#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.conf_system import getRemoteConnInfo
from typing import Dict, Any, Optional, Union, List
import threading
import redis
import json


class RedisConnector:
    def __init__(self, logger, db=0, ttl=0):
        self._logger = logger
        self._db = db
        self._ttl = ttl
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

    def __del__(self):
        if self._redis_client:
            self._redis_client.close()

    def get_db(self):
        return self._db

    # ============ String 타입: SET/GET ============

    def set(self, key: str, value: Union[str, dict, list, int, float], ex: Optional[int] = None) -> bool:
        """
        Redis SET 명령어

        Args:
            key: Redis 키
            value: 저장할 값 (str, dict, list, int, float)
            ex: 만료 시간(초). None이면 self._ttl 사용

        Returns:
            bool: 성공 여부

        Example:
            redis.set("user:name", "Alice")
            redis.set("user:data", {"name": "Alice", "age": 30})
            redis.set("session:token", "abc123", ex=3600)  # 1시간 후 만료
        """
        try:
            # dict/list는 JSON 문자열로 변환
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            # 만료 시간 설정
            ttl_seconds = ex if ex is not None else self._ttl

            if ttl_seconds > 0:
                self._redis_client.setex(key, ttl_seconds, serialized_value)
            else:
                self._redis_client.set(key, serialized_value)

            self._logger.debug(f"Redis SET: key={key}, ttl={ttl_seconds}")
            return True

        except Exception as e:
            self._logger.error(f"Redis SET failed: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Redis GET 명령어

        Args:
            key: Redis 키

        Returns:
            저장된 값 (자동으로 JSON 파싱 시도)
            존재하지 않으면 None

        Example:
            name = redis.get("user:name")  # "Alice"
            data = redis.get("user:data")  # {"name": "Alice", "age": 30}
        """
        try:
            data = self._redis_client.get(key)

            if data is None:
                return None

            # JSON 파싱 시도
            try:
                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                # JSON이 아니면 원본 문자열 반환
                return data

        except Exception as e:
            self._logger.error(f"Redis GET failed: {e}")
            return None

    def mset(self, mapping: Dict[str, Any]) -> bool:
        """
        여러 키를 한 번에 설정 (MSET)

        Args:
            mapping: {key: value} 딕셔너리

        Returns:
            bool: 성공 여부

        Example:
            redis.mset({
                "user:1:name": "Alice",
                "user:2:name": "Bob",
                "config:version": "1.0"
            })
        """
        try:
            # dict/list는 JSON으로 변환
            serializable_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serializable_mapping[k] = json.dumps(v)
                else:
                    serializable_mapping[k] = str(v)

            self._redis_client.mset(serializable_mapping)
            self._logger.debug(f"Redis MSET: {len(mapping)} keys")
            return True

        except Exception as e:
            self._logger.error(f"Redis MSET failed: {e}")
            return False

    def mget(self, keys: list) -> Dict[str, Any]:
        """
        여러 키를 한 번에 조회 (MGET)

        Args:
            keys: 조회할 키 리스트

        Returns:
            {key: value} 딕셔너리

        Example:
            data = redis.mget(["user:1:name", "user:2:name"])
            # {"user:1:name": "Alice", "user:2:name": "Bob"}
        """
        try:
            values = self._redis_client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value is None:
                    result[key] = None
                    continue

                # JSON 파싱 시도
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    result[key] = value

            return result

        except Exception as e:
            self._logger.error(f"Redis MGET failed: {e}")
            return {}

    # ============ Hash 타입: HSET/HGET ============

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

    # ============ 유틸리티 메서드 ============

    def clear(self, key: str):
        """키 삭제 (delete의 별칭)"""
        try:
            self._redis_client.delete(key)
        except Exception as e:
            self._logger.error(f"Redis DELETE failed: {e}")

    def switch_db(self, db):
        """DB 전환"""
        self._redis_client = redis.Redis(
            host=self._host,
            port=self._port,
            password=self._passwd,
            decode_responses=True,
            db=db
        )
        self._db = db

    def flush(self):
        """현재 DB의 모든 키 삭제"""
        self._logger.critical(f"Redis flushed DB: {self._db}")
        self._redis_client.flushdb()

    def delete(self, *keys: str) -> int:
        """
        키 삭제 (DEL)

        Args:
            *keys: 삭제할 키들

        Returns:
            int: 삭제된 키 개수

        Example:
            redis.delete("user:1")
            redis.delete("user:1", "user:2", "user:3")
        """
        try:
            deleted_count = self._redis_client.delete(*keys)
            self._logger.debug(f"Redis DELETE: {deleted_count} keys deleted")
            return deleted_count
        except Exception as e:
            self._logger.error(f"Redis DELETE failed: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        키 존재 여부 확인 (EXISTS)

        Args:
            *keys: 확인할 키들

        Returns:
            int: 존재하는 키 개수

        Example:
            if redis.exists("user:1"):
                print("존재함")
        """
        try:
            return self._redis_client.exists(*keys)
        except Exception as e:
            self._logger.error(f"Redis EXISTS failed: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        키에 만료 시간 설정 (EXPIRE)

        Args:
            key: 키
            seconds: 만료 시간(초)

        Returns:
            bool: 성공 여부

        Example:
            redis.expire("session:abc", 3600)  # 1시간 후 만료
        """
        try:
            result = self._redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            self._logger.error(f"Redis EXPIRE failed: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        키의 남은 만료 시간 조회 (TTL)

        Args:
            key: 키

        Returns:
            int: 남은 시간(초)
                 -1: 만료 시간 없음
                 -2: 키가 존재하지 않음

        Example:
            remaining = redis.ttl("session:abc")
            print(f"남은 시간: {remaining}초")
        """
        try:
            return self._redis_client.ttl(key)
        except Exception as e:
            self._logger.error(f"Redis TTL failed: {e}")
            return -2


    # ============ 키 검색 및 조회 ============

    def keys(self, pattern: str = "*", sort: bool = True, reverse: bool = False) -> List[str]:
        """
        패턴에 매칭되는 키 목록 조회 (정렬 지원)

        Args:
            pattern: 검색 패턴 (기본값: "*")
                    - "*": 모든 키
                    - "user:*": user로 시작하는 모든 키
                    - "*:session": session으로 끝나는 모든 키
                    - "user:?": user: 뒤에 한 글자
            sort: 정렬 여부 (기본값: True)
            reverse: 역순 정렬 여부 (기본값: False)

        Returns:
            List[str]: 키 목록 (정렬됨)

        Warning:
            프로덕션 환경에서는 SCAN 사용 권장 (KEYS는 블로킹)

        Example:
            # 모든 키 조회 (정렬)
            all_keys = redis.keys()

            # user로 시작하는 키만 조회
            user_keys = redis.keys("user:*")

            # 역순 정렬
            keys = redis.keys("session:*", reverse=True)

            # 정렬 안 함
            keys = redis.keys("*", sort=False)
        """
        try:
            # Redis KEYS 명령어 실행
            keys_list = self._redis_client.keys(pattern)

            # bytes를 str로 변환 (decode_responses=False인 경우 대비)
            if keys_list and isinstance(keys_list[0], bytes):
                keys_list = [key.decode('utf-8') for key in keys_list]

            # 정렬
            if sort:
                keys_list = sorted(keys_list, reverse=reverse)

            self._logger.debug(
                f"Redis KEYS: pattern={pattern}, "
                f"count={len(keys_list)}, "
                f"sorted={sort}, "
                f"reverse={reverse}"
            )

            return keys_list

        except Exception as e:
            self._logger.error(f"Redis KEYS failed: {e}")
            return []

    def scan_keys(
        self,
        pattern: str = "*",
        count: int = 100,
        sort: bool = True,
        reverse: bool = False
    ) -> List[str]:
        """
        SCAN을 사용한 안전한 키 조회 (프로덕션 권장)

        Args:
            pattern: 검색 패턴
            count: 한 번에 가져올 개수 (힌트)
            sort: 정렬 여부
            reverse: 역순 정렬 여부

        Returns:
            List[str]: 키 목록 (정렬됨)

        Example:
            # SCAN으로 안전하게 조회 (KEYS 대신 권장)
            keys = redis.scan_keys("user:*")

            # 많은 양 조회
            keys = redis.scan_keys("*", count=1000)
        """
        try:
            keys_list = []
            cursor = 0

            # SCAN 반복
            while True:
                cursor, partial_keys = self._redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=count
                )

                # bytes를 str로 변환
                if partial_keys:
                    if isinstance(partial_keys[0], bytes):
                        partial_keys = [key.decode('utf-8') for key in partial_keys]
                    keys_list.extend(partial_keys)

                # 커서가 0이면 완료
                if cursor == 0:
                    break

            # 정렬
            if sort:
                keys_list = sorted(keys_list, reverse=reverse)

            self._logger.debug(
                f"Redis SCAN: pattern={pattern}, "
                f"count={len(keys_list)}, "
                f"sorted={sort}"
            )

            return keys_list

        except Exception as e:
            self._logger.error(f"Redis SCAN failed: {e}")
            return []

    def search_keys(
        self,
        pattern: str = "*",
        use_scan: bool = True,
        sort: bool = True,
        reverse: bool = False,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        키 검색 (SCAN 또는 KEYS 사용)

        Args:
            pattern: 검색 패턴
            use_scan: True면 SCAN, False면 KEYS 사용
            sort: 정렬 여부
            reverse: 역순 정렬 여부
            limit: 최대 반환 개수 (None이면 전체)

        Returns:
            List[str]: 키 목록

        Example:
            # 상위 10개만
            top_keys = redis.search_keys("user:*", limit=10)

            # KEYS 명령어로 빠르게 조회 (개발 환경)
            keys = redis.search_keys("*", use_scan=False)
        """
        try:
            # SCAN 또는 KEYS 선택
            if use_scan:
                keys_list = self.scan_keys(pattern, sort=sort, reverse=reverse)
            else:
                keys_list = self.keys(pattern, sort=sort, reverse=reverse)

            # 개수 제한
            if limit is not None and limit > 0:
                keys_list = keys_list[:limit]

            return keys_list

        except Exception as e:
            self._logger.error(f"Redis search_keys failed: {e}")
            return []

    def count_keys(self, pattern: str = "*") -> int:
        """
        패턴에 매칭되는 키 개수 조회

        Args:
            pattern: 검색 패턴

        Returns:
            int: 키 개수

        Example:
            total = redis.count_keys()
            user_count = redis.count_keys("user:*")
        """
        try:
            keys_list = self._redis_client.keys(pattern)
            count = len(keys_list)
            self._logger.debug(f"Redis count_keys: pattern={pattern}, count={count}")
            return count
        except Exception as e:
            self._logger.error(f"Redis count_keys failed: {e}")
            return 0

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