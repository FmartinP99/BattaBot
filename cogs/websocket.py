from discord import Member
from discord.ext import commands
from datetime import datetime, timezone
import botMain
import asyncio
from Websocket.websocketManager import ws_manager, WebSocketMessage
from discord.utils import get as get

class Websocket(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.check(botMain.check_owner)
    async def wst(self, context):
        payload = WebSocketMessage(
            msgtype="test",
            message="test",
        )
        await ws_manager.broadcast(payload)
        await context.send("Test message sent to frontend.")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def get_all_server_information(self):
        await self.bot.wait_until_ready()

        all_data = []

        for guild in self.bot.guilds:

            guild_info = {
                "guildId": str(guild.id),
                "guildName": guild.name,
                "iconUrl": guild.icon.url if guild.icon else None,
                "channels": [],
                "members": []
            }

            for channel in guild.channels:

                connected_members = []

                if str(channel.type) in ["voice", "stage"]:
                    connected_members = [str(m.id) for m in channel.members]

                guild_info["channels"].append({
                    "channelId": str(channel.id),
                    "name": channel.name,
                    "type": channel.type.value,
                    "connectedMemberIds": connected_members,
                })

                if str(channel.type) in ["voice", "stage"]:
                    guild_info["members"] = [m.id for m in channel.members]

            
            for member in guild.members:
                guild_info["members"].append({
                    "memberId": str(member.id),
                    "name": member.name,
                    "displayName": member.display_name,
                    "avatarUrl" : member.avatar.url if member.avatar else member.default_avatar.url,
                    "bot": member.bot,
                    "status": str(member.status)
                })

            all_data.append(guild_info)
           
        return all_data
    
    async def sendMessage(self, serverId, channelId, text):
        
        guild = self.bot.get_guild(serverId)
        if not guild:
            print(f"Guild {serverId} not found")
            return

        channel = guild.get_channel(channelId) 
        if not channel:
            print(f"Channel {channelId} not found")
            return

        await channel.send(text)

        return None
    
    async def handle_set_reminder(self, serverid, channelId, memberId, date, text):
        guild = self.bot.get_guild(serverid)
        if not guild:
            print(f"Guild {serverid} not found")
            return

        channel = guild.get_channel(channelId) 
        if not channel:
            print(f"Channel {channelId} not found")
            return
        
        remindme_cog = self.bot.get_cog("RemindMe");
        if remindme_cog is None:
            print("RemindMe cog was none in handleSetRemidner.")
            return
        date = date.astimezone()  
        date = date.replace(tzinfo=None)

        await remindme_cog.add_remindme_from_outside(serverid, channelId, memberId, date, text)
        await channel.send(f"Timer set to: {date.strftime('%Y-%m-%d  %H:%M')} <@{memberId}> \n{text}")
        
    async def _sleep_and_ping(self, serverId, channelId, text, memberId, sleepTimer):
        await asyncio.sleep(sleepTimer)
        remindme_cog = self.bot.get_cog("RemindMe")
        await remindme_cog.ping_bot(serverId, channelId, text, memberId)

    async def voice_channel_update(self, serverId, channelId, is_disconnect):

        guild = self.bot.get_guild(serverId)
        if guild is None:
            print(f"Guild with ID {serverId} not found.")
            return

        channel = guild.get_channel(channelId)
        if channel is None:
            print(f"Channel with ID {channelId} not found in guild {serverId}.")
            return

        voice = get(self.bot.voice_clients, guild=guild)

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        try:
            if is_disconnect:
                await player_cog._stop(serverId)
                print(f"Disconnected from {channel.name}")
            else:
                await player_cog.join(channelId, serverId)
        except Exception as e:
            print("Error while connecting/moving voice channel:")
            print(e)

    
    async def get_music_playlist(self, serverId):
        guild = self.bot.get_guild(serverId)
        if guild is None:
            print(f"Guild with ID {serverId} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        song_dict = player_cog.get_song_dict(serverId)
        current_state = player_cog.get_current_state(serverId)

        # filename might not be needed in the frontend
        if song_dict is not None:
                ws_songs = [
                    {
                        "index": s.index,
                        "title": s.title,
                        "artist": s.artist,
                        "lengthStr": s.lengthStr,
                        "length": s.length,
                        "filename": "" 
                    }
                    for s in song_dict.values()
                ]
        else:
            ws_songs = None

        return {
            "serverId": str(serverId),
            "songs": ws_songs,
            "playlistState": current_state.to_dict() if current_state else None
        }
    
    async def skip_song_to(self, serverId: int, songIndex: int):
        guild = self.bot.get_guild(serverId)
        if guild is None:
            print(f"Guild with ID {serverId} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return
        
        player_cog.skip_to(serverId, songIndex)

    async def play_pause(self, serverId: int, isPausing: bool):
        guild = self.bot.get_guild(serverId)
        if guild is None:
            print(f"Guild with ID {serverId} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            print(f"PlayPause player cog was none.")
            return
        
        player_cog.play_pause(serverId, isPausing)

        
    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        user_id = message.author.id
        server_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.id

        epoch = datetime.now(timezone.utc).timestamp()

        payload = WebSocketMessage(
        msgtype="incomingMessage",
        message={
            "serverId": str(server_id),
            "channelId": str(channel_id),
            "messageId": str(message_id),
            "userId": str(user_id),
            "text": message.content,
            "epoch": epoch
            }
        )   
        
        await ws_manager.broadcast(payload)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        epoch = datetime.now(timezone.utc).timestamp()
        before_channel = before.channel.id if before.channel else None
        after_channel = after.channel.id if after.channel else None

        payload = WebSocketMessage(
            msgtype="voiceStateUpdate",
            message={
                "memberId": str(member.id),
                "serverId": str(member.guild.id),
                "beforeChannel": str(before_channel),
                "afterChannel": str(after_channel),
                "epoch": epoch,
            }
        )

        await ws_manager.broadcast(payload)

    def get_voice_state(self, serverId: int):
        guild = self.bot.get_guild(serverId)
        if guild is None:
            print(f"Guild with ID {serverId} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        current_state = player_cog.get_current_state(serverId)
        return  {
                "serverId": str(serverId),
                "playlistState": current_state.to_dict()
            }
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if(before.status != after.status):
            await self._handle_member_change(before, after)


    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        await self._handle_member_change(before, after) 
    
    async def _handle_member_change(self, before: Member, after: Member):
        
        payload = WebSocketMessage(
        msgtype="presenceUpdate",
        message={
            "memberId": str(before.id),
            "serverId": str(before.guild.id),
            "newStatus": str(after.status),
            "newDisplayName": str(after.display_name),
            }
        )

        await ws_manager.broadcast(payload)
        

async def setup(bot):
    await bot.add_cog(Websocket(bot))