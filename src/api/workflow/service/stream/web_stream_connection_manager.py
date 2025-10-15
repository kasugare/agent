#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
from fastapi import WebSocket


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