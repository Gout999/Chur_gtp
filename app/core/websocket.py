"""Minimal WebSocket connection manager."""
from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str) -> None:
        self.active_connections.pop(connection_id, None)

    async def send_json(self, connection_id: str, payload: dict) -> None:
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await websocket.send_json(payload)
