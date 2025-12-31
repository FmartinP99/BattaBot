from dataclasses import dataclass
import uuid
from dataclasses_json import dataclass_json
from typing import Union

from fastapi import WebSocket

@dataclass_json
@dataclass
class WebSocketMessage:
    msgtype: str
    message: Union[object, str]

class WebSocketManager:
    def __init__(self):
        # ws_id -> WebSocket
        self.connected_clients: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        ws_id = str(uuid.uuid4())
        self.connected_clients[ws_id] = ws
        return ws_id

    def disconnect(self, ws_id: str):
        self.connected_clients.pop(ws_id, None)

    async def broadcast(self, message: WebSocketMessage):
        for ws_id, ws in list(self.connected_clients.items()):
            try:
                await ws.send_text(message.to_json())
                print(f"Broadcast successful for {ws_id}: {message.msgtype}")
            except Exception as e:
                print(f"Broadcast failed for {ws_id}: {e}")
                self.disconnect(ws_id)

    async def send_to_client(self, ws_id: str, message: WebSocketMessage):
        ws = self.connected_clients.get(ws_id)
        if not ws:
            print(f"Client {ws_id} not connected")
            return

        try:
            await ws.send_text(message.to_json())
            print(f"Send successful for {ws_id}: {message.msgtype}")
        except Exception as e:
            print(f"Send failed for {ws_id}: {e}")
            self.disconnect(ws_id)

ws_manager = WebSocketManager()