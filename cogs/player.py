import threading
import discord
from youtube_dl import YoutubeDL
from discord.ext import commands
from requests import get as get_requests
from discord.utils import get as get
from discord import FFmpegPCMAudio
import os
from random import choice
from botMain import check_owner, IS_BOT_READY
from globals import g_cover, g_localMediaPlayerFolderPath, g_ffmpeg, g_botid
import asyncio
from typing import Optional
import sys
from enum import Enum, auto
from discord.errors import ClientException


class PlayMusicEnums(Enum):
    """Enums for play_music function"""

    SKIP = auto()
    PREV = auto()


class PlayerAttributes:
    """Class contains flags and a few function, for MediaPlayer"""

    def __init__(self):

        self.play = False  # checks if <play> has been called, to not throw an error
        self.play_er = False
        self.stop_Var = False  # checks if <stop> has been called, to not throw an error

        self.g_context = None  # where the bot plays music
        self.need_update = False  # if <now_playing> has been called, this manages auto_update
        self.playlistMessage = None  # <now_playing> message. this has to be updated

        self.threadMP = threading.Thread()

        self.song_dict = dict()
        self.mediaplayer_path = g_localMediaPlayerFolderPath  # change this if you want to play from somewhere else
        self.song_var = os.listdir(self.mediaplayer_path)
        self.song_to_play_index = 1  # which song to play
        self.load_songs()
        self.shuffle()

    def load_songs(self):

        index = 0
        while len(self.song_var) > 0:
            if not self.song_var[0].endswith('.jpg'):
                self.song_dict[index + 1] = f"{self.song_var[0]}"
                del self.song_var[0]
                index += 1
            else:
                del self.song_var[0]

    def shuffle(self):

        self.song_var = self.song_dict
        self.song_dict = dict()
        self.song_to_play_index = 1

        index = 1
        while len(self.song_var) > 0:
            randomkey = choice(list(self.song_var.keys()))
            if not self.song_var[randomkey].endswith('.jpg'):
                self.song_dict[index] = f"{self.song_var[randomkey]}"
                del self.song_var[randomkey]
                index += 1
            else:
                del self.song_var[randomkey]

    def get_song_dict(self):

        return self.song_dict


class Player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.g_cover = g_cover
        self.mediaBots = {}

        if IS_BOT_READY and not self.mediaBots:
            for guild in self.bot.guilds:
                self.mediaBots[guild.id] = PlayerAttributes()

    def get_song_dict(self, server_id):

        return self.mediaBots[server_id].get_song_dict()

    async def join(self, context, voice):

        channel = context.author.voice.channel
        try:

            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await channel.connect()
            get(self.bot.voice_clients, guild=context.guild)
        except Exception:
            await context.send("Couldn't join to the voice channel!!")

    def search(self, arg):

        with YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
            try:
                get_requests(arg)
            except Exception:
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
            else:
                info = ydl.extract_info(arg, download=False)
        return (info, info['formats'][0]['url'])

    @commands.command()
    async def play(self, context, *, query):

        mediaBot = self.mediaBots[context.guild.id]

        if context.author.voice is not None:

            mediaBot.play = True

            FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                           'options': '-vn'}

            video, source = self.search(query)
            voice = get(self.bot.voice_clients, guild=context.guild)
            await self.join(context, voice)
            voice = get(self.bot.voice_clients, guild=context.guild)
            if voice.is_playing():
                voice.stop()

            try:
                if not mediaBot.threadMP.is_alive():
                    mediaBot.threadMP.join()
            except Exception:
                print("Couldn't close thread in <play>")


            mediaBot.play_er = False
            voice.play(FFmpegPCMAudio(source, **FFMPEG_OPTS), after=lambda e: print('done', e))
            voice.is_playing()
            self.mediaBots[context.guild.id] = mediaBot
        else:
            await context.send("You are not in a voice channel!")

    def play_music(self, vc, context, optional_play_music_enum: PlayMusicEnums = None):

        mediaBot = self.mediaBots[context.guild.id]

        if optional_play_music_enum == PlayMusicEnums.SKIP or mediaBot.play is True:
            vc.stop()
            mediaBot.play = False

        if optional_play_music_enum == PlayMusicEnums.PREV:
            vc.stop()
            mediaBot.song_to_play_index -= 2
            if mediaBot.song_to_play_index < 1:
                mediaBot.song_to_play_index = 1

            mediaBot.play = False

        if mediaBot.stop_Var is False:

            try:
                mediaBot.play_er = True
                vc.play(discord.FFmpegOpusAudio(executable=f"{g_ffmpeg}",
                                               source=f"{mediaBot.mediaplayer_path}/{mediaBot.song_dict[mediaBot.song_to_play_index]}", bitrate=320),
                        after=lambda e: self.play_music(vc, context))
                print(f"{mediaBot.song_to_play_index} - {mediaBot.song_dict[mediaBot.song_to_play_index]}")

                mediaBot.song_to_play_index += 1
                mediaBot.need_update = True

                if mediaBot.song_to_play_index > len(mediaBot.song_dict):
                    mediaBot.song_to_play_index = 1
            except ClientException:
                pass

        self.mediaBots[context.guild.id] = mediaBot

    @commands.command(pass_context=True, aliases=['er', 'ER'])
    async def playmusic(self, context):

        mediaBot = self.mediaBots[context.guild.id]

        voice = get(self.bot.voice_clients, guild=context.guild)
        try:
            await self.join(context, voice)
            voice = get(self.bot.voice_clients, guild=context.guild)
            if voice.is_playing():
                voice.stop()
            mediaBot.threadMP = threading.Thread(target=self.play_music, args=(voice, context,))
            mediaBot.threadMP.start()
        except Exception:
            await context.send("You are not in a voice channel!")

    @commands.command(aliases=['np'])
    async def now_playing(self, context):

        mediaBot = self.mediaBots[context.guild.id]

        if mediaBot.playlistMessage is not None:
            msg = await mediaBot.g_context.fetch_message(mediaBot.playlistMessage.id)
            await msg.delete()

        voice = get(self.bot.voice_clients, guild=context.guild)

        try:
            if voice.is_playing() and voice.is_connected():
                if not mediaBot.play:
                    file = discord.File(self.g_cover, filename="cover.jpg")
                    em = discord.Embed(title='Now playing:',
                                       description=f"{mediaBot.song_dict[mediaBot.song_to_play_index - 1][:-4]}",
                                       color=0x71368a)
                    em.set_thumbnail(url="attachment://cover.jpg")
                    em.set_footer(text=f"Made by:\nTReKeSS#3943")

                    mediaBot.playlistMessage = await context.send(file=file, embed=em)
                    mediaBot.g_context = context
                    await mediaBot.playlistMessage.add_reaction('\U00002B05')
                    await mediaBot.playlistMessage.add_reaction('\U000023F9')
                    await mediaBot.playlistMessage.add_reaction('\U000027A1')
                    await self.check_update(context.guild.id)
                else:
                    await context.send(f"There is no quality music playing.")

        except Exception:
            print(sys.exc_info())
            await context.send("You are either not in a voice channel, or there is no quality music playing.")

        finally:
            self.mediaBots[context.guild.id] = mediaBot

    @commands.command(pass_context=True)
    async def stop(self, context):

        mediaBot = self.mediaBots[context.guild.id]
        voice = get(self.bot.voice_clients, guild=context.guild)

        if voice and voice.is_connected():
            if mediaBot.song_to_play_index > 1:
                mediaBot.song_to_play_index -= 1
            mediaBot.stop_Var = True
            mediaBot.play = False
            voice.stop()
            await voice.disconnect()
            if mediaBot.playlistMessage is not None:
                msg = await mediaBot.g_context.fetch_message(mediaBot.playlistMessage.id)
                await msg.delete()
                mediaBot.playlistMessage = None
            try:
                mediaBot.threadMP.join()
            except Exception:
                print("couldnt close thread")
                print(sys.exc_info())
            finally:
                mediaBot.stop_Var = False
                self.mediaBots[context.guild.id] = mediaBot

        else:
            await context.send("Can't leave.")

    @commands.command(pass_context=True)
    async def skip(self, context, value=0, called_with_command=True):

        mediaBot = self.mediaBots[context.guild.id]

        try:
            if isinstance(value, int):
                if 0 <= value <= len(mediaBot.song_dict):
                    if value != 0:
                        mediaBot.song_to_play_index = value
                    voice = get(self.bot.voice_clients, guild=context.guild)
                    if called_with_command:
                        msg = await context.fetch_message(context.message.id)
                        await msg.delete()
                    self.play_music(voice, context, optional_play_music_enum=PlayMusicEnums.SKIP)

                else:
                    await context.send("Out of index!")
            else:
                await context.send("I can only skip to decimal numbers!")

        except Exception:
            print("There is something wrong with skipping!!")
            print(sys.exc_info())

        finally:
            self.mediaBots[context.guild.id] = mediaBot

    @commands.command(pass_context=True)
    async def prev(self, context):

        try:
            voice = get(self.bot.voice_clients, guild=context.guild)
            self.play_music(voice, context, optional_play_music_enum=PlayMusicEnums.PREV)
        except Exception:
            print("There is something wrong with going back!")
            print(sys.exc_info())

    @commands.command(pass_context=True, aliases=['ers', 'er_Search'])
    async def lp_search(self, context, *, name=""):

        mediaBot = self.mediaBots[context.guild.id]

        if name != "":
            try:
                if mediaBot.play is False and mediaBot.play_er is True:
                    searched_music_values = []

                    for song in mediaBot.song_dict.values():
                        if name.lower() in song.lower():
                            searched_music_values.append(song)

                    if searched_music_values:
                        searched_index = 1

                        while searched_index < len(mediaBot.song_dict):
                            if searched_music_values[0] == mediaBot.song_dict[searched_index]:
                                mediaBot.song_to_play_index = searched_index
                                get(self.bot.voice_clients, guild=context.guild).stop()
                                mediaBot.need_update = True
                                break
                            else:
                                searched_index += 1
                    else:
                        await context.send(f"Could not find it : {name}")
                else:
                    await context.send(
                        "Cannot search, because,you are either not in a voice channel,"
                        " or there is no quality music playing.")
            except Exception:
                print(sys.exc_info())

            finally:
                self.mediaBots[context.guild.id] = mediaBot
        else:
            await context.send("Did not provide what to search for.")

        await asyncio.sleep(8)
        msg = await context.fetch_message(context.message.id)
        await msg.delete()

    @commands.command(pass_context=True, aliases=['ersl'])
    async def lp_searchlist(self, context, *, search=""):

        mediaBot = self.mediaBots[context.guild.id]
        name = ""

        if search != "":
            search = search.split(' ')
            for word in search:
                if word != "-stay":
                    name = ''.join(word)

            try:
                if name == '*':
                    searched_music = list()
                    for key, value in mediaBot.song_dict.items():
                        searched_music.append(f"{key} - {value}")
                else:
                    searched_music = list()
                    for key, value in mediaBot.song_dict.items():
                        if name.lower() in str(value).lower():
                            searched_music.append(f"{key} - {value}")

                if not searched_music:
                    await context.send(f"Couldn't find it.: {name}")

                else:
                    index = 1
                    messages = []

                    if len(searched_music) > 24 * 8:  # max page entry  *  max pages LIMIT
                        max_page = 8
                    else:
                        max_page = (len(searched_music) // 24) + 1

                    while index < len(searched_music) or (index == 1 and len(searched_music) == 1):
                        file = discord.File(self.g_cover, filename="cover.jpg")
                        em = discord.Embed(
                            title=f'Searched results (max: 24 per page.) Max 8 pages.\nPage {(index // 24) + 1}/{max_page}:',
                            description=f"Searched title: {name}\nMatches: {index}-{index + 23 if index + 23 < len(searched_music) else len(searched_music)} out of {len(searched_music)}",
                            color=0x71368a)
                        em.set_thumbnail(url="attachment://cover.jpg")
                        em.set_footer(text=f"Made by:\nTReKeSS#3943")

                        for result in searched_music[index - 1:]:

                            if len(searched_music) > 18:
                                em.add_field(name=f'{index}', value=f'{result[:-4]}', inline=True)
                            else:
                                em.add_field(name=f'{index}', value=f'{result[:-4]}', inline=False)

                            if index % 24 == 0 or index == len(searched_music):
                                msg = await context.send(file=file, embed=em)
                                index += 1
                                await asyncio.sleep(5)
                                messages.append(msg)
                                break

                            index += 1

                        if index > 24 * 8:
                            msg = await context.send(f"I can only show the first {8 * 24} result. (×﹏×)")
                            messages.append(msg)
                            break

                    if search[-1] != "-stay":
                        for msg in messages:
                            await asyncio.sleep(7)
                            await msg.delete()

                msg = await context.fetch_message(context.message.id)
                await msg.delete()
            except Exception:
                print(sys.exc_info())

            finally:
                self.mediaBots[context.guild.id] = mediaBot
        else:
            await context.send("Didn't provide what to search for.")

    @commands.command()
    async def shuffle(self, context):

        mediaBot = self.mediaBots[context.guild.id]
        mediaBot.shuffle()
        self.mediaBots[context.guild.id] = mediaBot

    @commands.command(pass_context=True)
    @commands.check(check_owner)
    async def setpath(self, context, *, path):

        mediaBot = self.mediaBots[context.guild.id]

        path = str(path).replace("\\", "/").lower()
        print(path)

        if "".lower() in path:
            try:
                mediaBot.mediaplayer_path = path
                mediaBot.song_dict = dict()
                mediaBot.song_var = os.listdir(mediaBot.mediaplayer_path)
                mediaBot.song_to_play_index = 1
                mediaBot.load_songs()
                self.mediaBots[context.guild.id] = mediaBot

                try:
                    get(self.bot.voice_clients, guild=context.guild).stop()
                    await self.playmusic(context)
                except Exception:
                    await context.send(
                        "Setpath set, but couldn't query the bot's voice. You are probably not in a voice channel.")
                    print(sys.exc_info())
                msg = await context.fetch_message(context.message.id)
                await msg.delete()

            except Exception:
                await context.send("There is something wrong with setting the path!")
                print(sys.exc_info())

        else:
            await context.send("No!")

    @commands.Cog.listener("on_reaction_add")
    async def listenReactionPlayer(self, reaction, user):

        right_arrow = '\U000027A1'
        left_arrow = '\U00002B05'
        stop_button = '\U000023F9'

        mediaBot = self.mediaBots[reaction.message.guild.id]

        if user.id != g_botid:
            try:
                if reaction.emoji == right_arrow and mediaBot.playlistMessage.id == reaction.message.id:
                    await self.skip(mediaBot.g_context, called_with_command=False)
                    await self.playlist_update(mediaBot.playlistMessage.id,
                                               reaction.message.guild.id, False)
                    msg = await mediaBot.g_context.fetch_message(mediaBot.playlistMessage.id)
                    await msg.remove_reaction(reaction, user)

                elif reaction.emoji == left_arrow and mediaBot.playlistMessage.id == reaction.message.id:
                    await self.prev(mediaBot.g_context)
                    await self.playlist_update(mediaBot.playlistMessage.id,
                                               reaction.message.guild.id, False)
                    msg = await mediaBot.g_context.fetch_message(mediaBot.playlistMessage.id)
                    await msg.remove_reaction(reaction, user)

                elif reaction.emoji == stop_button and mediaBot.playlistMessage.id == reaction.message.id:
                    await self.stop(mediaBot.g_context)
                    msg = await mediaBot.g_context.fetch_message(mediaBot.playlistMessage.id)
                    await msg.delete()

            except AttributeError:
                pass

            except Exception:
                print(sys.exc_info())

            finally:
                self.mediaBots[reaction.message.guild.id] = mediaBot

    async def check_update(self, contextguildid):

        mediaBot = self.mediaBots[contextguildid]

        while mediaBot.playlistMessage is not None:

            if mediaBot.need_update:
                await self.playlist_update(mediaBot.playlistMessage.id, contextguildid, True)
                self.mediaBots[contextguildid] = mediaBot
            await asyncio.sleep(3)

    async def playlist_update(self, update_message_id, contextguildid, auto_update: Optional[bool]):

        mediaBot = self.mediaBots[contextguildid]

        if auto_update == True:
            mediaBot.need_update = False
            self.mediaBots[contextguildid] = mediaBot

        if len(mediaBot.song_dict) != 1:
            song = mediaBot.song_to_play_index - 1
        else:
            song = 1

        em = discord.Embed(title='Now playing:',
                           description=f"{mediaBot.song_dict[song][:-4]}",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.set_footer(text=f"Made by:\nTReKeSS#3943")
        msg = await mediaBot.g_context.fetch_message(update_message_id)
        await msg.edit(embed=em)

    @commands.Cog.listener("on_guild_join")
    async def on_guild_joined(self, guild):

        if guild.id not in self.mediaBots:
            self.mediaBots[guild.id] = PlayerAttributes()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.mediaBots[guild.id] = PlayerAttributes()


def setup(bot):
    bot.add_cog(Player(bot))
