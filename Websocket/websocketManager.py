from dataclasses import dataclass
from dataclasses_json import dataclass_json
import json
from typing import Union

@dataclass_json
@dataclass
class WebSocketMessage:
    msgtype: str
    message: Union[object, str]

class WebSocketManager:
    def __init__(self):
        self.connected_clients = set()

    async def connect(self, ws):
        await ws.accept()
        self.connected_clients.add(ws)

    def disconnect(self, ws):
        self.connected_clients.remove(ws)

    async def broadcast(self, message: WebSocketMessage):
        for ws in list(self.connected_clients):
            try:
                await ws.send_text(message.to_json())
                print("Broadcast successful!")
            except Exception as e:
                print("Broadcast failed!")
                print(e)
                #self.disconnect(ws)

ws_manager = WebSocketManager()