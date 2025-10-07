#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
from fastapi import WebSocket
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json


class WSConnectionManager:
    def __init__(self, logger):
        self._logger = logger
        self._conn_pool: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self._conn_pool[connection_id] = websocket

    async def receive_message(self, connection_id):
        try:
            websocket = self._conn_pool.get(connection_id)
            client_message = await websocket.receive_text() # ASGI Protocol - raw message
            return client_message
        except Exception as e:
            self._logger.error(e)
            raise

    async def send_message(self, connection_id, message):
        try:
            websocket = self._conn_pool.get(connection_id)
            await websocket.send_json(message)
        except Exception as e:
            self._logger.error(e)

    def disconnect(self, connect_id: str):
        try:
            ws_socket = self._conn_pool.pop(connect_id, None)
            ws_socket.close()
        except Exception as e:
            self._logger.error(e)

    # def _execute_async(self, async_function):
    #     try:
    #         # 현재 실행 중인 루프 가져오기 시도
    #         loop = asyncio.get_event_loop()
    #     except RuntimeError:
    #         # 루프가 없으면 새로 생성
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #
    #     if loop.is_running():
    #         # 루프가 이미 실행 중이면 새 스레드에서 실행
    #         with ThreadPoolExecutor() as executor:
    #             future = executor.submit(asyncio.run, async_function)
    #             return future.result()
    #     else:
    #         # 루프가 실행 중이 아니면 직접 실행
    #         return loop.run_until_complete(async_function)

    # def send_message_sync(self, connect_id, message):
    #     client_message = self._execute_async(self.send_message(connect_id, message))
    #     return client_message

    # def receive_message_sync(self, connection_id):
    #     self._logger.info(f"REQ RUN: {connection_id}")
    #     client_message = self._execute_async(self.receive_message(connection_id))
    #     return client_message

