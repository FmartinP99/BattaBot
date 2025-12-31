from datetime import datetime
from enum import Enum
import json
from Services.WebsocektService import WebsocketService
from Websocket.websocket_manager import WebSocketMessage, ws_manager
from Websocket.websocket_message_classes import WebsocketGetMusicPlaylistQuery, WebsocketGetRemindersQuery, WebsocketMessageType, WebsocketPlaylistPauseQuery, WebsocketPlaylistResumeQuery, WebsocketPlaylistSongSkipQuery, WebsocketPlaylistStateUpdateQuery, WebsocketSendMessageQuery, WebsocketSetReminderQuery, WebsocketToggleRoleQuery, WebsocketVoiceStateUpdateQuery

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
        self.websocketService: WebsocketService = WebsocketService()
        self._initialized = True

    def parse_ws_message_type(self, value: str) -> WebsocketMessageType:
        try:
            for member in WebsocketMessageType:
                if value == member.value:
                    return member
        except ValueError:
            return WebsocketMessageType.NULL
    
    async def handle_incoming_ws_message(self, ws_id:str, data):

        json_data = json.loads(data)
        print(json_data)
        if "type" not in json_data or "message" not in json_data:
            print("Incoming websocket message format error.")
            print(json_data)
            return

        msg_type = self.parse_ws_message_type(json_data["type"])

        if(msg_type is WebsocketMessageType.NULL):
            print(json_data)
            print("Incoming websocket message type error.")
            return
       
        message = json_data.get("message", "")
        
        response = WebSocketMessage(
            msgtype=msg_type.value,
            message=await self.distribute_incoming_ws_message(msg_type, message)
        )

        # if we get back a direct response from distribute_incoming_ws_message, it is a client specific response.
        if response.message is not None:
            await ws_manager.send_to_client(ws_id, response)
    
    async def distribute_incoming_ws_message(self, msgtype: WebsocketMessageType, message: str = ""):
        
        websocket_cog = self.bot.get_cog("Websocket");
        if not websocket_cog:
            raise ValueError("Websocket cog is not found!")

        response = ""
        if msgtype is WebsocketMessageType.INIT:
            try:
                response = await websocket_cog.get_all_server_information()
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
        elif msgtype is WebsocketMessageType.SEND_MESSAGE:
            try:
                obj: WebsocketSendMessageQuery = WebsocketSendMessageQuery(**message)
                server_id = int(obj.serverId)
                channel_id = int(obj.channelId)
                response = await websocket_cog.sendMessage(server_id, channel_id, obj.text) 
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
        elif msgtype is WebsocketMessageType.SET_REMINDER:
            try:
                obj: WebsocketSetReminderQuery = WebsocketSetReminderQuery(**message)
                server_id = int(obj.serverId)
                channel_id = int(obj.channelId)
                member_id = int(obj.memberId)
                text = obj.text
                date_str = obj.date
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                response = await websocket_cog.handle_set_reminder(server_id, channel_id, member_id, date, text)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype is WebsocketMessageType.VOICE_STATE_UPDATE:
            try:
                obj: WebsocketVoiceStateUpdateQuery = WebsocketVoiceStateUpdateQuery(**message)
                server_id = int(obj.serverId)
                channel_id = int(obj.channelId)
                response = await websocket_cog.voice_channel_update(server_id, channel_id, obj.isDisconnect)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype is WebsocketMessageType.GET_MUSIC_PLAYLIST:
            try:
                obj: WebsocketGetMusicPlaylistQuery = WebsocketGetMusicPlaylistQuery(**message)
                server_id =  server_id = int(obj.serverId)
                response = await websocket_cog.get_music_playlist(server_id)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
        
        elif msgtype is WebsocketMessageType.PLAYLIST_STATE_UPDATE:
            try:
                obj: WebsocketPlaylistStateUpdateQuery = WebsocketPlaylistStateUpdateQuery(**message)
                server_id =  server_id = int(obj.serverId)
                response = websocket_cog.get_voice_state(server_id)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None    

        elif msgtype is WebsocketMessageType.PLAYLIST_SONG_SKIP:
            try:
                obj: WebsocketPlaylistSongSkipQuery = WebsocketPlaylistSongSkipQuery(**message)
                server_id = int(obj.serverId)
                response = await websocket_cog.skip_song_to(server_id, obj.songIndex)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype is WebsocketMessageType.PLAYLIST_PAUSE or msgtype is WebsocketMessageType.PLAYLIST_RESUME:
            try:
                is_pausing = msgtype is WebsocketMessageType.PLAYLIST_PAUSE
                obj: WebsocketPlaylistPauseQuery | WebsocketPlaylistResumeQuery = WebsocketPlaylistPauseQuery(**message) if is_pausing else WebsocketPlaylistResumeQuery(**message) 
                server_id = int(obj.serverId)
                response = await websocket_cog.play_pause(server_id, is_pausing)
            except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
            
        elif msgtype is WebsocketMessageType.TOGGLE_ROLE:
              try:
                  obj: WebsocketToggleRoleQuery = WebsocketToggleRoleQuery(**message)
                  server_id = int(obj.serverId)
                  member_id = int(obj.memberId)
                  role_id = int(obj.roleId)
                  response = await websocket_cog.toggle_role(server_id, member_id, role_id)
              except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None
              
        elif msgtype is WebsocketMessageType.GET_REMINDERS:
              try:
                  obj: WebsocketGetRemindersQuery = WebsocketGetRemindersQuery(**message)
                  server_id = int(obj.serverId)
                  member_id = int(obj.memberId)
                  response = await self.websocketService.get_reminders_for_user_for_server(server_id, member_id)
              except Exception as e:
                print("Error message was: " + str(message))
                print(e)
                return None 

        return response
