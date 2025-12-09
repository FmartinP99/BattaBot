import sys
from discord.ext import commands
from botMain import prefix
import discord
from globals import GLOBAL_CONFIGS
from botMain import IS_BOT_READY

class HelpCommandAttributes():

    def __init__(self):
        self.g_context = None
        self.helpMessage = None  # embed help message sent by bot
        self.helpListaIndex = 0
        self.embedList = []
        self.helpMessageWritten = None #  {prefix}help   - message
        self.makeEmbedMessages()



    def makeEmbedMessages(self):
        em = discord.Embed(title='0 - Help',
                           description=f'Use {prefix}help <command> or {prefix}help <module>_<command> (if the <module> and the <command> has the same name) for extended information!',
                           color=0x71368a)
        em.add_field(name='1 - Modules', value='load, unload, reload', inline=False)
        em.add_field(name='2 - Mal', value='mal\n tracemoe\n setsimilarity')
        em.add_field(name='3 - Remindme', value='remindme')
        em.add_field(name='4 - Player',
                     value='playmusic\n lp_searchlist \n now_playing \n skip, prev, stop, resume \n setpath, shuffle')
        em.add_field(name='Others', value='ping, status')
        em.set_footer(text=f"Made by:\nTReKeSS")

        self.embedList.append(em)

        em = discord.Embed(title='1 - Modules', description="Module control commands.", color=0x71368a)
        em.add_field(name="Commands:", value=f'{prefix}load <module_name>\n'
                                             f'{prefix}unload <module_name>\n'
                                             f'{prefix}reload <module_name>\n')
        em.set_footer(text=f"Made by:\nTReKeSS")

        self.embedList.append(em)

        em = discord.Embed(title='2 - Mal',
                           description="This module contains commands to search for an anime or a manga on MAL, or search on Tracemoe with a picture",
                           color=0x71368a)
        em.add_field(name="Commands:", value=f'{prefix}mal <anime_name>\n'
                                             f'{prefix}mal -manga <manga_name>\n'
                                             f'{prefix}tracemoe <attached_picture or picture_url>\n'
                                             f'{prefix}setsimilarity <value between 0 and 1, default is 0.8>')
        em.set_footer(text=f"Made by:\nTReKeSS")

        self.embedList.append(em)

        em = discord.Embed(title='3 - Remindme',
                           description="You can set a specific time, to get reminded.",
                           color=0x71368a)
        em.add_field(name="Syntax",
                     value=f'{prefix}remindme <hh:mm> <message>\n {prefix}remindme <mm> +<message> '
                           f'\n{prefix}remindme <mm-dd hh:mm> <message>'
                           f'\n{prefix}remindme <yyyy-mm-dd hh:mm> <message>'
                           f'\n{prefix}deleterm <remindme_id>'
                           f'\n{prefix}getmyrms'
                           f'\n{prefix}clearmyrms'
                           )
        em.set_footer(text=f"Made by:\nTReKeSS")

        self.embedList.append(em)

        em = discord.Embed(title='4 - Player',
                           description="You can listen to music from the host's computer or from youtube. Doesn't support playlists tho.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Commands:",
                     value=f'{prefix}localplayer\n{prefix}lp_searchlist <song_name> - lists songs with the <song_name>\n'
                           f'{prefix}now_playing\n{prefix}skip <song_index or nothing>\n{prefix}next\n {prefix}prev\n {prefix}shuffle')
        em.set_footer(text=f"Made by:\nTReKeSS")

        self.embedList.append(em)


class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g_cover = GLOBAL_CONFIGS.cover
        self.helpBots = {}

        if IS_BOT_READY and not self.helpBots:
            for guild in self.bot.guilds:
                self.helpBots[guild.id] = HelpCommandAttributes()

    @commands.group(invoke_without_command=True)
    async def help(self, context, *args):

        if len(args) == 0:

            helpBot = self.helpBots[context.guild.id]

            if helpBot.helpMessage is not None:
                helpBot.helpListaIndex = 0
                await helpBot.helpMessage.delete()

            if helpBot.helpMessageWritten is not None:
                await helpBot.helpMessageWritten.delete()

            helpMsg = helpBot.embedList[helpBot.helpListaIndex]
            helpMsg.set_thumbnail(url=context.guild.me.avatar)
            helpBot.helpMessageWritten = await context.fetch_message(context.message.id)
            helpBot.helpMessage = await context.send(embed=helpMsg)
            for i in range(0, min(len(helpBot.embedList), 10)):
                await helpBot.helpMessage.add_reaction(f'{i}\u20e3')
            if len(helpBot.embedList) > 10:
                await context.send("I can only make the first 10 module interactive!")
            helpBot.g_context = context
            self.helpBots[context.guild.id] = helpBot
        else:
            await context.send("This help command doesn't exist.")

    async def messageChange(self, context, helpMessageID):

        helpBot = self.helpBots[context.guild.id]

        helpMsg = helpBot.embedList[helpBot.helpListaIndex]

        helpMsg.set_thumbnail(url=context.guild.me.avatar)
        msg = await helpBot.g_context.fetch_message(helpMessageID)
        await msg.edit(embed=helpMsg)

        self.helpBots[context.guild.id] = helpBot

    @commands.Cog.listener("on_reaction_add")
    async def listenReactionHelp(self, reaction, user):

        helpBot = self.helpBots[reaction.message.guild.id]

        reactions = {f'{i}\u20e3': i for i in range(len(helpBot.embedList))}

        if user.id != GLOBAL_CONFIGS.bot_id:
            try:
                if helpBot.helpMessage.id == reaction.message.id:
                    helpBot.helpListaIndex = reactions.get(reaction.emoji, None)
                    await self.messageChange(helpBot.g_context, helpBot.helpMessage.id)
                    await helpBot.helpMessage.remove_reaction(reaction, user)

            except AttributeError:
                pass

            except Exception:
                print(sys.exc_info())

            finally:
                self.helpBots[reaction.message.guild.id] = helpBot

    @help.command()
    async def modules(self, context):
        em = self.helpBots[context.guild.id].embedList[1]
        await context.send(embed=em)

    @help.command()
    async def mal(self, context):
        em = self.helpBots[context.guild.id].embedList[2]
        await context.send(embed=em)

    @help.command()
    async def remindme(self, context):
        em = self.helpBots[context.guild.id].embedList[3]
        await context.send(embed=em)

    @help.command()
    async def player(self, context):
        em = self.helpBots[context.guild.id].embedList[4]
        await context.send(embed=em)

    @help.command()
    async def load(self, context):
        em = discord.Embed(title='Load', description="Loads a module and it's commands.", color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}load <modulename>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def unload(self, context):
        em = discord.Embed(title='Unload', description="Unloads a module and it's commands.",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}unload <modulename>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def reload(self, context):
        em = discord.Embed(title='Reload', description="Reloads a module and it's commands.",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}reload <modulename>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def mal_mal(self, context):
        em = discord.Embed(title='Mal',
                           description="Searches for an anime via it's name.",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}mal <anime name>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def tracemoe(self, context):
        em = discord.Embed(title='Tracemoe',
                           description="Searches for an anime via it's picture.",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}tracemoe <attached_picture or picture_url>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def setsimilarity(self, context):
        em = discord.Embed(title='Setsimilarity',
                           description="Sets the similarity for the tracemoe command. Higher similarity means more accurate search. Default is 0.80",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}setsimilarity <value between 0 and 1, default is 0.8>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def deleterm(self, context):
        em = discord.Embed(title='Delete Remindme',
                           description="Deletes the remindme with the given Id if it belongs to the user.",
                           color=0x71368a)
        em.add_field(name="Syntax",
                     value=f'{prefix}deleterm <remindme_id>')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def getmyrms(self, context):
        em = discord.Embed(title='Get my Remindmes',
                           description="Gets all the remindmes from the database for the user.",
                           color=0x71368a)
        em.add_field(name="Syntax",
                     value=f'{prefix}clearmyrms')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def clearmyrms(self, context):
        
        em = discord.Embed(title='Clear my Remindmes',
                           description="Clears all the remindmes from the database for the user that has a past mention date but was not mentioned due to some error.",
                           color=0x71368a)
        em.add_field(name="Syntax",
                     value=f'{prefix}clearmyrms')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def play(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Play',
                           description="Plays a video from youtube.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}play <video_name_or_link_URL>')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def playmusic(self, context):
        em = discord.Embed(title='Mal',
                           description="Searches for an anime via it's picture.",
                           color=0x71368a)
        em.add_field(name="Syntax", value=f'{prefix}playmusic')
        em.add_field(name="Alisases",
                     value=f'{prefix}er')
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def lp_searchlist(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Now playing',
                           description="Lists the musics via the name (max:24 per page) .\n'*' lists everything. (up to 192)\n\n"
                                       "Sent messages will be deleted automatically after a few seconds.\nUse '-stay' at the end of the message to make it stay.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}er_searchlist')
        em.add_field(name="Alisases",
                     value=f'{prefix}ersl')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def now_playing(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Now playing',
                           description="Displays the current music.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}now_playing')
        em.add_field(name="Alisases",
                     value=f'{prefix}np')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file= file,embed=em)

    @help.command()
    async def setpath(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Setpath',
                           description="Set the path to play the musics (OWNER ONLY)",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}setpath <path>')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def skip(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Skip',
                           description="Skips the playlist to an exact index if a number is given, if not, it skips forward one.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}skip\n{prefix}skip <number>')
        em.add_field(name="Tip",
                     value=f"To know a song's index, use {prefix}ersl <song_name>")
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def prev(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Prev',
                           description="Goes to the previous song",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}prev')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def stop(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Stop',
                           description="Disconnects battabot from the voicechat.",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}stop')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def shuffle(self, context):
        file = discord.File(GLOBAL_CONFIGS.cover, filename="cover.jpg")
        em = discord.Embed(title='Shuffle',
                           description="Shuffles the playlist",
                           color=0x71368a)
        em.set_thumbnail(url="attachment://cover.jpg")
        em.add_field(name="Syntax",
                     value=f'{prefix}shuffle')
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(file=file, embed=em)

    @help.command()
    async def ping(self, context):
        em = discord.Embed(title='Ping', description='Pings the bot!', color=0x71368a)
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @help.command()
    async def status(self, context):
        em = discord.Embed(title='Status', description='Changes the status of the bot. Only the owner can do it!', color=0x71368a)
        em.set_thumbnail(url=context.guild.me.avatar)
        em.set_footer(text=f"Made by:\nTReKeSS")
        await context.send(embed=em)

    @commands.Cog.listener("on_guild_join")
    async def on_guild_joined(self, guild):
        if guild.id not in self.helpBots:
            self.helpBots[guild.id] = HelpCommandAttributes()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.helpBots[guild.id] = HelpCommandAttributes()

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
