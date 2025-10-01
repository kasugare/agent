#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict
from fastapi import WebSocket
import json


class WSConnectionManager:
    def __init__(self, logger):
        self._logger = logger
        self._conn_pool: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connect_id: str):
        await websocket.accept()
        self._conn_pool[connect_id] = websocket

    def disconnect(self, connect_id: str):
        self._conn_pool.pop(connect_id, None)

    async def send_to_user(self, user_id: str, response: json):
        ws = self._conn_pool.get(user_id)
        if ws:
            await ws.send_text(response.model_dump_json())

    async def broadcast(self, sender: str, message: str):
        payload = {
            "type": "msg",
            "user": sender,
            "text": message,
        }
        for ws in self._conn_pool.values():
            await ws.send_text(json.dumps(payload))

    async def broadcast_json(self, payload: dict):
        import json
        for ws in self._conn_pool.values():
            await ws.send_text(json.dumps(payload))