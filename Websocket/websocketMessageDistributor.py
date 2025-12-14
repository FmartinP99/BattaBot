from datetime import datetime
from enum import Enum
import json
from Websocket.websocketManager import WebSocketMessage, ws_manager

class WebsocketMessageType(Enum):
    NULL = ""
    INIT = "init"
    SEND_MESSAGE = "sendMessage"
    INCOMING_MESSAGE = "incomingMessage"
    SET_REMINDER = "setReminder"
    VOICE_STATE_UPDATE = "voiceStateUpdate"
    GET_MUSIC_PLAYLIST = "getMusicPlaylist"
    PLAYLIST_STATE_UPDATE = "playlistStateUpdate"
    PLAYLIST_SONG_SKIP = "playlistSongSkip"
    PLAYLIST_PAUSE = "playlistPause"
    PLAYLIST_RESUME = "playlistResume"
    PRESENCE_UPDATE = "presenceUpdate"

class WebsocketMessageDistributor:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, bot):
        if self._initialized:
            return
        self.bot = bot
        self._initialized = True

    def parse_ws_message_type(self, value: str) -> WebsocketMessageType:
        try:
            return WebsocketMessageType(value)
        except ValueError:
            return WebsocketMessageType.NULL
    
    async def handle_incoming_ws_message(self, data):

        json_data = json.loads(data)
        if "type" not in json_data or "message" not in json_data:
            print("Incoming websocket message format error.")
            print(json_data)
            return

        msg_type = self.parse_ws_message_type(json_data["type"])
        if(msg_type == WebsocketMessageType.NULL):
            print("Incoming websocket message type error.")
            return
        
        message = json_data.get("message", "")
        print(json_data)
        
        response = WebSocketMessage(
            msgtype=msg_type,
            message=await self.distribute_incoming_ws_message(msg_type, message)
        )

        if response.message is not None:
            await ws_manager.broadcast(response)
    
    async def distribute_incoming_ws_message(self, msgtype: WebsocketMessageType, message: str = ""):

        websocket_cog = self.bot.get_cog("Websocket");
        if not websocket_cog:
            raise ValueError("Websocket cog is not found!")

        response = ""
        if msgtype == WebsocketMessageType.INIT:
            response = await websocket_cog.get_all_server_information()
        elif msgtype == WebsocketMessageType.SEND_MESSAGE:
            try:
                server_id = int(message["serverId"])
                channel_id = int(message["channelId"])
                response = await websocket_cog.sendMessage(server_id, channel_id, message["text"]) 
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
        elif msgtype == WebsocketMessageType.SET_REMINDER:
            try:
                server_id = int(message["serverId"])
                channel_id = int(message["channelId"])
                member_id = int(message["memberId"])
                text = message["text"]

                date_str = message["date"]
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                response = await websocket_cog.handle_set_reminder(server_id, channel_id, member_id, date, text)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype == WebsocketMessageType.VOICE_STATE_UPDATE:
            try:
                server_id = int(message["serverId"])
                channel_id = int(message["channelId"])
                is_disconnect = bool(message["isDisconnect"])

                response = await websocket_cog.voice_channel_update(server_id, channel_id, is_disconnect)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype == WebsocketMessageType.GET_MUSIC_PLAYLIST:
            try:
                server_id = int(message["serverId"])
                response = await websocket_cog.get_music_playlist(server_id)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None

        elif msgtype == WebsocketMessageType.PLAYLIST_SONG_SKIP:
            try:
                server_id = int(message["serverId"])
                song_index = int(message["songIndex"])

                response = await websocket_cog.skip_song_to(server_id, song_index)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype == WebsocketMessageType.PLAYLIST_PAUSE or msgtype == WebsocketMessageType.PLAYLIST_RESUME:
            try:
                is_pausing = msgtype == WebsocketMessageType.PLAYLIST_PAUSE
                server_id = int(message["serverId"])

                response = await websocket_cog.play_pause(server_id, is_pausing)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None

        elif msgtype == WebsocketMessageType.PLAYLIST_STATE_UPDATE:
            try:
                server_id = int(message["serverId"])
                response = websocket_cog.get_voice_state(server_id)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None        
        return response
