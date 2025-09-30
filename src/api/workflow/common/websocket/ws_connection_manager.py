from typing import Dict,Set
from fastapi import WebSocket
import time
import json

def now_ms() -> int:
    return int(time.time() * 1000)

class WSConnectionManager:

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, connect_id: str):
        await ws.accept()
        self.active_connections[connect_id] = ws

    def disconnect(self, connect_id: str):
        self.active_connections.pop(connect_id, None)

    async def send_to_user(self, user_id: str, response: json):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(response.model_dump_json())

    async def broadcast(self, sender: str, message: str):
        payload = {
            "type": "msg",
            "user": sender,
            "text": message,
        }
        for ws in self.active_connections.values():
            await ws.send_text(json.dumps(payload))

    async def broadcast_json(self, payload: dict):
        import json
        for ws in self.active_connections.values():
            await ws.send_text(json.dumps(payload))

