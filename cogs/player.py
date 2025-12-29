import asyncio
from discord.ext import tasks
from dataclasses import dataclass, field
import random
from typing import Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import os
from Websocket.websocketMessageClasses import WebsocketMessageType
from global_config import GLOBAL_CONFIGS
from discord.ext import commands
from botMain import check_owner, IS_BOT_READY
import discord
from discord.utils import get as get
import uuid
import time
from Websocket.websocketManager import ws_manager, WebSocketMessage
#import logging
#logging.basicConfig(level=logging.DEBUG)

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                           'options': '-vn'}

@dataclass(frozen=False)
class Music:
    index: int
    title: str
    artist: str
    lengthStr: str
    length: int
    filename: str

class Playing:

    def __init__(self, isPlaying: bool, loop: asyncio.AbstractEventLoop):
        self._initializing = True

        self.loop = loop
        self._debounce_task: asyncio.Task | None = None

        self._debounce_timer = None
        self.isPlaying: bool = isPlaying
        self.music: Music | None = None
        self.modifiedAt: float = time.time()
        self.playedDuration: int = 0
        self._increment_loop.start()

        self._initializing = False

    def __setattr__(self, name, value):
        # normal field update
        super().__setattr__(name, value)
        # whenever we update the music, the modifiedAt also changes.
        if name == "music":
            super().__setattr__("modifiedAt", time.time())
            super().__setattr__("playedDuration", 0)

        if name == "isPlaying" and not self._initializing:
            self._debounce_update_loop_state()

    def _debounce_update_loop_state(self, delay=0.15):
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = self.loop.create_task(
            self._debounced_update(delay)
        )

    async def _debounced_update(self, delay):
        try:
            await asyncio.sleep(delay)
            self._update_loop_state()
        except asyncio.CancelledError:
            pass

    def _update_loop_state(self):
        if self.isPlaying:
            if not self._increment_loop.is_running():
                self._increment_loop.start()
        else:
            if self._increment_loop.is_running():
                self._increment_loop.stop()

    @tasks.loop(seconds=1)
    async def _increment_loop(self):
        if self.isPlaying:
            self.playedDuration += 1
            print(f"{self.music.title} -> {self.playedDuration} / {self.music.length}")

    @_increment_loop.before_loop
    async def before_loop(self):
        await asyncio.sleep(0)

    def to_dict(self):
         return {
            "isPlaying": self.isPlaying,
            "music": self.music,
            "modifiedAt": self.modifiedAt,
            "playedDuration": self.playedDuration,
        }

class PlayerAttributes:

    def __init__(self, loop: asyncio.AbstractEventLoop):

        self.mediaplayer_path: str = GLOBAL_CONFIGS.local_media_path
  
        self.current: Playing = Playing(isPlaying=False, loop=loop)
        self.musics: dict[int, Music] = {}
        self.load_songs(True)

        self.now_playing_guid: uuid.UUID | None = None # so that only the correct play_music callback loop is executed, the other(s) terminate
        self.playlistMessage: discord.Message | None = None


    def load_songs(self, shuffle:bool=False ):
        index = 0

        self.musics = {}

        songpaths = os.listdir(self.mediaplayer_path)
        if shuffle:
            random.shuffle(songpaths)

        while len(songpaths) > 0:
            file_path = songpaths.pop(0)

            if not isinstance(file_path, str):
                print("Skipping invalid file:", file_path)
                continue

            if file_path.lower().endswith(".jpg"):
                print("Skipping image:", file_path)
                continue

            if not file_path.lower().endswith(".mp3"):
                print("Not mp3 audio. Skipping.")
                continue


            try:
                audio = MP3(os.path.join(self.mediaplayer_path, file_path), ID3=ID3)
                artist_tag = audio.tags.get("TPE1") if audio.tags else None
                title_tag = audio.tags.get("TIT2") if audio.tags else None

                artist = artist_tag.text[0] if artist_tag else ""
                title = title_tag.text[0] if title_tag else ""

                # if metadata is wrong we try to guess it 
                if title == "":
                    splitted = file_path[:-4].split(" - ", 1)
                    if len(splitted) == 1:
                        title = splitted[0]
                        artist = ""
                    else:
                        artist = splitted[0]
                        title = splitted[1] 

                length_seconds = int(audio.info.length) if audio.info.length else 0
                minutes = length_seconds // 60
                seconds = length_seconds % 60
                length_str = f"{minutes:02d}:{seconds:02d}"
            

            except Exception as e:
                # if metadata is wrong we try to guess it
                splitted = file_path[:-4].split(" - ", 1)
                if len(splitted) == 1:
                        title = splitted[0]
                        artist = ""
                else:
                    artist = splitted[0]
                    title = splitted[1] 
                length_str = "00:00"
          
            music_obj = Music(
                index = index + 1,
                title=title,
                artist=artist,
                lengthStr=length_str,
                length=length_seconds,
                filename=file_path
            )

            self.musics[index + 1] = music_obj
            index += 1            

        self.current.music = self.musics[1]
        print("Songs shuffled") if shuffle else print("Songs loaded.")

    def shuffle(self):
        self.load_songs(True)

    def get_song_dict(self) -> dict[int, Music]:
        return self.musics
    
    def get_song(self, index: int) -> Music | None:
        return self.musics.get(index)
    
    def get_current_song_inferred_title(self) -> str:
        return self.get_song_inferred_title(self.current.music)
    
    def get_song_inferred_title(self, music: Music) -> str:
        title = music.artist + " - " + music.title if len(music.artist) > 0 else music.title 
        return title


class Player(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cover = GLOBAL_CONFIGS.cover
        self.mediaBots: dict[int, PlayerAttributes] = {}

        if IS_BOT_READY and len(self.mediaBots) == 0:
            for guild in self.bot.guilds:
                self.mediaBots[guild.id] = PlayerAttributes(loop=self.bot.loop)
    
    def get_song_dict(self, serverId: int) -> dict[int, Music] | None:
        return self.mediaBots.get(serverId).get_song_dict() if serverId in self.mediaBots else None
    
    def get_current_state(self, serverId: int) -> Playing | None:
         return self.mediaBots.get(serverId).current if serverId in self.mediaBots else None
    
    async def join(self, channelId: int, guildId: int):

        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(channelId)
        if channel is None:
            print("Channel is not found while trying to join.")
            return
        
        guild = self.bot.get_guild(guildId)
        if guild is None:
            print("Server is not found while trying to join.")
            return
        
        voice = self.get_voice_client(guild)

        try:
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await channel.connect(timeout=10, reconnect=True)
        except Exception as e:
            print(e)
            print(type(e))
            print("Couldn't join to the voice channel!! "  + channel.name)


    # yt functions
    # search function will not be implemented right now
    # same for play functionality


    def play_music(self, guildId: int, newIndex: int, uuid: uuid.UUID):

        guild = self.get_guild_by_id(guildId)

        if guild is None:
            print("Play Music guild was none")
            return

        mediaBot = self.mediaBots.get(guildId)

        if uuid != mediaBot.now_playing_guid:
            return

        if mediaBot is None:
            print("Play Music media bot does not exists.")
            return

        voice = self.get_voice_client(guild)

        if voice is None:
            print("Play Music voice does not exists.")
            return
        
        if not voice.is_connected():
            print("Play music voice is not connected")
            return
        
        
        maxIndex = len(mediaBot.get_song_dict())
        newIndex = maxIndex if newIndex < 1 else 1 if newIndex > maxIndex else newIndex
        newSong = mediaBot.get_song(newIndex)
        if newSong is None:
            print("Play Music The new song does not exists. Index: " + str(newIndex))
            return
        
        mediaBot.current.music = newSong
        mediaBot.current.isPlaying = True

        def after_play(error):
            if error:
                print("Error playing:", error)
                return
            if voice and voice.is_connected():
                next_index = newIndex + 1
                if next_index > maxIndex:
                    next_index = 1 

                self.play_music(guildId, next_index, uuid)
        
        try:
            if mediaBot.playlistMessage:
                self.bot.loop.create_task(
                    self.playlist_update(
                        mediaBot.playlistMessage.id, 
                        guildId, 
                        mediaBot.playlistMessage.channel.id
                    )
                )

            self._send_ws_notification_on_paylist_state_change(guildId)
         

            voice.play(discord.FFmpegOpusAudio(executable=f"{GLOBAL_CONFIGS.ffmpeg}",
                                                source=f"{mediaBot.mediaplayer_path}/{mediaBot.musics[mediaBot.current.music.index].filename}", bitrate=320),
                        after=after_play)
            
        except Exception as e:
            print(e)
            print("Now Playing Error while FFMPEG playing in channel.")
        

    @commands.command(aliases=['er', 'ER'])
    async def playmusic(self, context: commands.Context):
        mediaBot = self.mediaBots.get(context.guild.id)
        try:
            await self.join(context.author.voice.channel.id, context.guild.id)
            new_guid = uuid.uuid4()
            mediaBot.now_playing_guid = new_guid
            self.play_music(context.guild.id, mediaBot.current.music.index, new_guid)
        except Exception as e:
            print(e)
            mediaBot.current.isPlaying = False
            await context.send("You are not in a voice channel!")


    @commands.command()
    async def stop(self, context: commands.Context):
        mediaBot = self.mediaBots.get(context.guild.id)
        await self._stop(context.guild.id)

        if mediaBot.playlistMessage is not None:
                msg = await mediaBot.playlistMessage.channel.fetch_message(mediaBot.playlistMessage.id)
                await msg.delete()
                mediaBot.playlistMessage = None

    @commands.command()
    async def pause(self, context: commands.Context):
        self.play_pause(context.guild.id, True)

    @commands.command()
    async def resume(self, context: commands.Context):
        self.play_pause(context.guild.id)

    
    def play_pause(self, guildId: int, isPausing:bool = False):
        mediaBot = self.mediaBots.get(guildId)
        if mediaBot is None:
            print("PlayPause MediaBot was None.")
            return
        
        guild = self.get_guild_by_id(guildId)
        if guild is None:
            print("PlayPause guild is None ")
            return

        voice = self.get_voice_client(guild)
        if voice is None:
            print("PlayPause voice is None ")
            return

        # voice is connected but there are no now_playing, then we try to start one
        if not isPausing and voice and voice.is_connected() and mediaBot.now_playing_guid is None:
            new_guid = uuid.uuid4()
            mediaBot.now_playing_guid = new_guid
            self.skip_to(guildId, mediaBot.current.music.index)
        
        if not voice.is_connected():
            print("PlayPause voice is not connected.")
            return
        
        # on resume
        if not isPausing:
            if not voice.is_paused():
                return
            mediaBot.current.isPlaying = True
            voice.resume()
            self._send_ws_notification_on_paylist_state_change(guildId)
            return
        
        # on pause
        if voice.is_paused():
            return
        mediaBot.current.isPlaying = False
        voice.pause()
        self._send_ws_notification_on_paylist_state_change(guildId)
        
    @commands.command()
    async def skip(self, context: commands.Context, value: int=0):

        if not isinstance(value, int):
            await context.send("The index must be an integer value.")
            return
        
        #default, we skip forwards 1 
        if value == 0:
            mediaBot = self.mediaBots.get(context.guild.id)
            if mediaBot is None:
                print("Skip mediabot was None")
                return
            value = mediaBot.current.music.index + 1
        
        self.skip_to(context.guild.id, value)

    
    def skip_to(self, guildId: int,  newIndex: int):

        guild = self.get_guild_by_id(guildId)
        if guild is None:
            print("Skip To guild is None " + guildId)
            return
        
        mediaBot = self.mediaBots.get(guildId)
        voice = self.get_voice_client(guild)

        self.stop_sound(mediaBot, voice)

        new_guid = uuid.uuid4()
        mediaBot.now_playing_guid = new_guid

        self.play_music(guildId, newIndex, new_guid)


    @commands.command()
    async def prev(self, context: commands.Context):
        mediaBot = self.mediaBots.get(context.guild.id)

        prevIdx = mediaBot.current.music.index - 1
        self.skip_to(context.guild.id, prevIdx)


    @commands.command()
    async def shuffle(self, context: commands.Context):

        mediaBot = self.mediaBots.get(context.guild.id)
        if mediaBot is None:
            print("Shuffle mediabot was None")
            return
        mediaBot.shuffle()
        voice = self.get_voice_client(context.guild)
        self.stop_sound(mediaBot, voice)

        new_guid = uuid.uuid4()
        mediaBot.now_playing_guid = new_guid
        self.play_music(context.guild.id, 1, new_guid)

    # MSG things


    @commands.command(aliases=['np'])
    async def now_playing(self, context: commands.Context):

        mediaBot = self.mediaBots.get(context.guild.id)

        if mediaBot.playlistMessage is not None:
            msg = await context.channel.fetch_message(mediaBot.playlistMessage.id)
            if msg:
                await msg.delete()

        voice = self.get_voice_client(context.guild)

        try:
            if voice and  voice.is_playing() and voice.is_connected():
                if mediaBot.current.isPlaying:

                    song_name = mediaBot.get_current_song_inferred_title()

                    file = discord.File(self.cover, filename="cover.jpg")
                    em = discord.Embed(title='Now playing:',
                                       description=song_name,
                                       color=0x71368a)
                    em.set_thumbnail(url="attachment://cover.jpg")
                    

                    mediaBot.playlistMessage = await context.send(file=file, embed=em)
                    await mediaBot.playlistMessage.add_reaction('\U00002B05')
                    await mediaBot.playlistMessage.add_reaction('\U000023F9')
                    await mediaBot.playlistMessage.add_reaction('\U000027A1')
                else:
                    await context.send(f"There is no music playing.")

        except Exception as e:
            print(e)
            await context.send("You are either not in a voice channel, or there is no music playing.")


    @commands.Cog.listener("on_reaction_add")
    async def listenReactionPlayer(self, reaction: discord.Reaction, user: discord.User):

        right_arrow = '\U000027A1'
        left_arrow = '\U00002B05'
        stop_button = '\U000023F9'

        mediaBot = self.mediaBots.get(reaction.message.guild.id)

        if mediaBot.playlistMessage.id != reaction.message.id:
            return
        
        if user.id != GLOBAL_CONFIGS.bot_id:
            try:
                context = await self.bot.get_context(reaction.message)

                if reaction.emoji == right_arrow:
                    await self.skip(context)
                    await self.playlist_update(mediaBot.playlistMessage.id,
                                               reaction.message.guild.id,
                                               reaction.message.channel.id)
                    await reaction.message.remove_reaction(reaction.emoji, user)

                elif reaction.emoji == left_arrow:
                    await self.prev(context)
                    await self.playlist_update(mediaBot.playlistMessage.id,
                                               reaction.message.guild.id,
                                               reaction.message.channel.id)
                    await reaction.message.remove_reaction(reaction.emoji, user)

                elif reaction.emoji == stop_button:
                    await self.stop(context)
                    await reaction.message.delete()

            except AttributeError:
                pass

            except Exception as e:
                print(e)



    async def playlist_update(self, messageId: int, guildId: int, channelId: int):

        channel = self.bot.get_channel(channelId)
        if channel is None:
            print("Channel is not found in playlist update.")
            return
        
        guild = self.bot.get_guild(guildId)
        if guild is None:
            print("Server is not found in playlist update.")
            return

        mediaBot = self.mediaBots.get(guildId)
        songTitle = mediaBot.get_current_song_inferred_title()
        em = discord.Embed(title='Now playing:',
                           description=songTitle,
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        
        msg = await channel.fetch_message(messageId)
        if msg:
            await msg.edit(embed=em)


    @commands.command(aliases=['ersl'])
    async def lp_searchlist(self, context: commands.Context, *, searchTerm=""):

        mediaBot = self.mediaBots.get(context.guild.id)
        searchedTitle = ""

        if searchTerm != "":
            searchTerm = searchTerm.split(' ')
            for word in searchTerm:
                if word != "-stay":
                    searchedTitle = ''.join(word)

            try:
                songs = mediaBot.get_song_dict()
                if searchedTitle == '*':
                    searched_musics: list[str] = list()
                    for idx, music in songs.items():
                        searched_musics.append(f"{idx} - {music.title}")
                else:
                    searched_musics = list()
                    for idx, music in songs.items():
                        song_title = mediaBot.get_song_inferred_title(music)
                        if searchedTitle.lower() in str(song_title).lower():
                            searched_musics.append(f"{idx} - {song_title}")

                if len(searched_musics) == 0:
                    await context.send(f"Couldn't find it.: {searchedTitle}")
                    return

                else:
                    index = 1
                    messages = []
                    max_page_entry = 24
                    max_page_limit = 8
                    inline_limit = 18

                    if len(searched_musics) > max_page_entry * max_page_limit:  # max page entry  *  max pages LIMIT
                        max_page = max_page_limit
                    else:
                        max_page = (len(searched_musics) // max_page_entry) + 1

                    while index < len(searched_musics) or (index == 1 and len(searched_musics) == 1):
                        file = discord.File(self.cover, filename="cover.jpg")
                        em = discord.Embed(
                            title=f'Searched results (max: {max_page_entry} per page.) Max {max_page_limit} pages.\nPage {(index // max_page_entry) + 1}/{max_page}:',
                            description=f"Searched title: {searchedTitle}\nMatches: {index}-{index + (max_page_entry - 1) if index + (max_page_entry - 1) < len(searched_musics) else len(searched_musics)} out of {len(searched_musics)}",
                            color=0x71368a)
                        em.set_thumbnail(url="attachment://cover.jpg")
                        

                        for result in searched_musics[index - 1:]:

                            if len(searched_musics) > inline_limit:
                                em.add_field(name=f'{index}', value=f'{result}', inline=True)
                            else:
                                em.add_field(name=f'{index}', value=f'{result}', inline=False)

                            if index % max_page_entry == 0 or index == len(searched_musics):
                                msg = await context.send(file=file, embed=em)
                                index += 1
                                await asyncio.sleep(5)
                                messages.append(msg)
                                break

                            index += 1

                        if index > max_page_entry * max_page_limit:
                            msg = await context.send(f"I can only show the first {max_page_entry * max_page_limit} result. (×﹏×)")
                            messages.append(msg)
                            break

                    if searchTerm[-1] != "-stay":
                        for msg in messages:
                            await asyncio.sleep(7)
                            await msg.delete()

                msg = await context.fetch_message(context.message.id)
                await msg.delete()
            except Exception as e:
                print(e)

        else:
            await context.send("Didn't provide what to search for.")

    
    @commands.check(check_owner)
    @commands.command()
    async def setpath(self, context: commands.Context, *, path):

        mediaBot = self.mediaBots.get(context.guild.id)
        path = str(path).replace("\\", "/").lower()
        mediaBot.mediaplayer_path = path
        await self.shuffle(context)


    # HELPERS
        
    def stop_sound(self, mediaBot: PlayerAttributes, voice: discord.VoiceClient):
        mediaBot.current.isPlaying = False
        mediaBot.now_playing_guid = None

        if voice and voice.is_playing():
            voice.stop()

    def get_channel_by_id(self, channel_id: int) -> discord.abc.GuildChannel | None:
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel
        
            """ 
       try:
            return await self.bot.fetch_channel(channel_id)  # API call
        except discord.NotFound:
            return None
            """
        
    def get_guild_by_id(self, guild_id: int) -> discord.Guild | None:
        guild = self.bot.get_guild(guild_id)
        if guild is not None:
            return guild
        return None
        
        """
        try:
            return await self.bot.fetch_guild(guild_id)
        except discord.NotFound:
            return None
        """
        
    def get_voice_client(self, guild) -> discord.VoiceClient | None:
        voice = get(self.bot.voice_clients, guild=guild)
        if isinstance(voice, discord.VoiceClient):
            return voice
        return None

        
        
    @commands.Cog.listener("on_guild_join")
    async def on_guild_joined(self, guild: discord.Guild):

        if guild.id not in self.mediaBots:
            self.mediaBots[guild.id] = PlayerAttributes(loop=self.bot.loop)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.mediaBots[guild.id] = PlayerAttributes(loop=self.bot.loop)

    
    async def _stop(self, guildId: int):
        guild = self.get_guild_by_id(guildId)
        if guild is None:
            print("Guild was None in the 'stop' command.")
            return
        
        mediaBot = self.mediaBots.get(guildId)
        if mediaBot is None:
            print("Mediabot was None in the 'stop' command.")
            return
        
        voice = self.get_voice_client(guild)
        self.stop_sound(mediaBot, voice)
        if voice is None:
            print("Voice was None so the 'stop' command did not do anything.")
            return

        if voice and voice.is_connected():
            if mediaBot.current.music.index > 1:
                newSong = mediaBot.get_song(mediaBot.current.music.index - 1)
                mediaBot.current.music = newSong

        await voice.disconnect()

    ## websocket communication
    def _send_ws_notification_on_paylist_state_change(self, serverId: int):

        try:
            current_state = self.get_current_state(serverId)

            msgPayload = {
                "serverId": str(serverId),
                "playlistState": current_state.to_dict()
            }

            payload = WebSocketMessage(
            msgtype=WebsocketMessageType.PLAYLIST_STATE_UPDATE.value,
            message=msgPayload,
        )
            
            self.bot.loop.create_task(ws_manager.broadcast(payload))
        except Exception as e:
            print("Exception happened!")
            print(e)



async def setup(bot):
    await bot.add_cog(Player(bot))