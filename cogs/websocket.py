from typing import List
from discord import Member
import discord
from discord.ext import commands
from datetime import datetime, timezone
from Services.RemindmeService import RemindmeService
from Websocket.websocket_message_classes import WebsocketMessageType
import botMain
import asyncio
from Websocket.websocket_manager import ws_manager, WebSocketMessage
from discord.utils import get as get

from utils.remindme_helper import make_naive

class Websocket(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminderService: RemindmeService = RemindmeService()

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

        server_datas = []

        for guild in self.bot.guilds:

            guild_info = {
                "guildId": str(guild.id),
                "guildName": guild.name,
                "iconUrl": guild.icon.url if guild.icon else None,
                "channels": [],
                "members": [],
                "roles": [],
                "emotes": []
            }

            for channel in guild.channels:

                connected_members = []

                if str(channel.type) in ["voice", "stage"]:
                    connected_members = [str(m.id) for m in channel.members]

                guild_info["channels"].append({
                    "channelId": str(channel.id),
                    "name": channel.name,
                    "type": str(channel.type.value),
                    "connectedMemberIds": connected_members,
                })

                if str(channel.type) in ["voice", "stage"]:
                    guild_info["members"] = [m.id for m in channel.members]

            
            for member in guild.members:
                roles = sorted(member.roles, key=lambda r: r.position, reverse=True)
                roleIds: List[int] = [str(r.id) for r in roles]
                activity = self.get_highest_priority_activity(member)

                guild_info["members"].append({
                    "memberId": str(member.id),
                    "name": member.name,
                    "displayName": member.display_name,
                    "avatarUrl" : member.avatar.url if member.avatar else member.default_avatar.url,
                    "bot": member.bot,
                    "status": str(member.status),
                    "roleIds": roleIds,
                    "activityName": activity.name if activity else None
                })

            role_priorities = {
                str(role.id): role.position
                for role in guild.roles
            }

            guild_info["members"].sort(
                key=lambda m: (
                    role_priorities.get(m["roleIds"][0], -1)
                    if isinstance(m, dict)
                    and isinstance(m.get("roleIds"), list)
                    and m["roleIds"]
                    else -1
                ),
                reverse=True
            )
       
            roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
            for role in roles:
                guild_info["roles"].append({
                    "id": str(role.id),
                    "name": role.name,
                    "priority": role.position,
                    "color": F"#{role.color.value:06x}",
                    "displaySeparately": role.hoist,
                })

            for emoji in guild.emojis:
                guild_info["emotes"].append({
                    "id": str(emoji.id),
                    "name": emoji.name,
                    "rawStr": f"<:{emoji.name}:{str(emoji.id)}>",
                    "animated": emoji.animated,
                    "available": emoji.available,
                    "url": str(emoji.url)
                })

            server_datas.append(guild_info)

        all_data = {
            "serverDatas": server_datas
        }
           
        return all_data
    
    async def sendMessage(self, server_id, channel_id, text):
        
        guild = self.bot.get_guild(server_id)
        if not guild:
            print(f"Guild {server_id} not found")
            return

        channel = guild.get_channel(channel_id) 
        if not channel:
            print(f"Channel {channel_id} not found")
            return

        await channel.send(text)

        return None
    
    async def handle_set_reminder(self, server_id, channel_id, member_id, date, text):
        guild = self.bot.get_guild(server_id)
        if not guild:
            print(f"Guild {server_id} not found")
            return

        channel = guild.get_channel(channel_id) 
        if not channel:
            print(f"Channel {channel_id} not found")
            return
        
        remindme_cog = self.bot.get_cog("RemindMe");
        if remindme_cog is None:
            print("RemindMe cog was none in handleSetRemidner.")
            return
        date = date.astimezone()  
        date = date.replace(tzinfo=None)

        await remindme_cog.add_remindme_from_outside(server_id, channel_id, member_id, date, text)
        await channel.send(f"Timer set to: {date.strftime('%Y-%m-%d  %H:%M')} <@{member_id}> \n{text}")
        
    async def _sleep_and_ping(self, server_id, channel_id, text, member_id, sleep_timer):
        await asyncio.sleep(sleep_timer)
        remindme_cog = self.bot.get_cog("RemindMe")
        await remindme_cog.ping_bot(server_id, channel_id, text, member_id)

    async def voice_channel_update(self, server_id, channel_id, is_disconnect):

        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            print(f"Channel with ID {channel_id} not found in guild {server_id}.")
            return

        voice = get(self.bot.voice_clients, guild=guild)

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        try:
            if is_disconnect:
                await player_cog._stop(server_id)
                print(f"Disconnected from {channel.name}")
            else:
                await player_cog.join(channel_id, server_id)
        except Exception as e:
            print("Error while connecting/moving voice channel:")
            print(e)

    
    async def get_music_playlist(self, server_id):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        song_dict = player_cog.get_song_dict(server_id)
        current_state = player_cog.get_current_state(server_id)

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
            "serverId": str(server_id),
            "songs": ws_songs,
            "playlistState": current_state.to_dict() if current_state else None
        }
    
    async def skip_song_to(self, server_id: int, song_index: int):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return
        
        player_cog.skip_to(server_id, song_index)

    async def play_pause(self, server_id: int, is_pausing: bool):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            print(f"PlayPause player cog was none.")
            return
        
        player_cog.play_pause(server_id, is_pausing)

        
    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        user_id = message.author.id
        server_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.id

        epoch = make_naive(datetime.now(timezone.utc))
        payload = WebSocketMessage(
        msgtype=WebsocketMessageType.INCOMING_MESSAGE.value,
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
            msgtype=WebsocketMessageType.VOICE_STATE_UPDATE.value,
            message={
                "memberId": str(member.id),
                "serverId": str(member.guild.id),
                "beforeChannel": str(before_channel),
                "afterChannel": str(after_channel),
                "epoch": epoch,
            }
        )

        await ws_manager.broadcast(payload)

    def get_voice_state(self, server_id: int):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        player_cog = self.bot.get_cog("Player")
        if player_cog is None:
            return

        current_state = player_cog.get_current_state(server_id)
        return  {
                "serverId": str(server_id),
                "playlistState": current_state.to_dict()
            }

    @commands.has_permissions(manage_roles=True)
    async def toggle_role(self, server_id: int, member_id: int, role_id: int):
        guild = self.bot.get_guild(server_id)
        if guild is None:
            print(f"Guild with ID {server_id} not found.")
            return

        member = guild.get_member(member_id)
        if member is None:
            member = await guild.fetch_member(member_id)
        if member is None:
            print(f"Member with the id {member_id} was not found in guild {guild.name}")
            return
        
        role = guild.get_role(role_id)
        if role is None:
            print(f"Role with the id {role_id} was not found in guild {guild.name}")
            return
        
        if role in member.roles:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)
        
    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if before.status != after.status or  before.activities != after.activities :
            await self._handle_presence_change(before, after)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):

        # if roles change
        old_roles = set(before.roles)
        new_roles = set(after.roles)
        if old_roles != new_roles:
            await self._handle_roles_update(after.guild.id, after.id, old_roles, new_roles)
            return

        # else
        await self._handle_presence_change(before, after) 
    
    async def _handle_presence_change(self, before: Member, after: Member):
        new_activity = self.get_highest_priority_activity(after)
        payload = WebSocketMessage(
        msgtype=WebsocketMessageType.PRESENCE_UPDATE.value,
        message={
            "memberId": str(before.id),
            "serverId": str(before.guild.id),
            "newStatus": str(after.status),
            "newDisplayName": str(after.display_name),
            "newActivityName": new_activity.name if new_activity else None
            }
        )

        await ws_manager.broadcast(payload)

    async def _handle_roles_update(self, server_id: int, member_id: int, old_roles: set, new_roles: set):
           
        added_roles = new_roles - old_roles
        removed_roles = old_roles - new_roles
        role_is_added = False

        if added_roles:
            changed_role = added_roles.pop()
            role_is_added = True
        elif removed_roles:
            changed_role = removed_roles.pop()
            role_is_added = False
        else:
             return

        payload = WebSocketMessage(
        msgtype=WebsocketMessageType.TOGGLE_ROLE.value,
        message={
            "serverId": str(server_id),
            "roleId": str(changed_role.id),
            "memberId": str(member_id),
            "roleIsAdded": role_is_added
            }
        )
           
        await ws_manager.broadcast(payload)

    def get_highest_priority_activity(self, member: discord.Member) -> discord.Activity | None:

        activities = member.activities or []

        for activity in activities:
            if isinstance(activity, discord.Streaming):
                return activity

        for activity in activities:
            if (
                isinstance(activity, discord.Game)
                or isinstance(activity, discord.Spotify)
                or (
                    isinstance(activity, discord.Activity)
                    and activity.type in {
                        discord.ActivityType.playing,
                        discord.ActivityType.watching,
                        discord.ActivityType.listening,
                        discord.ActivityType.competing,
                    }
                )
            ):
                return activity

        for activity in activities:
            if isinstance(activity, discord.CustomActivity):
                return activity

        return None

async def setup(bot):
    await bot.add_cog(Websocket(bot))