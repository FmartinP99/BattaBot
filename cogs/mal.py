import difflib
from jikanpy import AioJikan
from discord.ext import commands
import discord
import tracemoepy
from tracemoepy.errors import TooManyRequests
import sys
from botMain import prefix, IS_BOT_READY
from global_config import GLOBAL_CONFIGS
from dataclasses import dataclass


class MalSearchAttributes:

    def __init__(self, similarity=0.8):

        self.traceMoeMessage = None
        self.traceMoeMessageReactions = {}
        self.titles = []
        self.context = None
        self.similarity = similarity

class MalSearch(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.malSearchAttributes = {}

        if IS_BOT_READY and not self.malSearchAttributes:
            for guild in self.bot.guilds:
                self.malSearchAttributes[guild.id] = MalSearchAttributes()

    @commands.command()
    async def mal(self, context, *, name=""):

        name_splitted = name.split(" ")
        searched_name = ""

        if name_splitted[0] == '-manga':
            name_splitted = name_splitted[1:]

        for i in name_splitted:
            searched_name = searched_name + i + " "
        searched_name = searched_name.strip()

        if searched_name != "":
            async with AioJikan() as aio_jikan:
                if not name.startswith("-manga"):
                    art = "anime"
                    results = await aio_jikan.search(search_type='anime', query=f'{searched_name}')
                    results2 = await aio_jikan.anime(1535)

                else:
                    art = "manga"
                    results = await aio_jikan.search(search_type='manga', query=f'{searched_name}')
                if results["data"]:
                    result = results["data"][0]

                    em = discord.Embed(title=f"{result['title']}\n{result['url']}",
                                          description=result['synopsis'],
                                          color=0x71368a)
                    em.add_field(name='Type', value=result['type'])
                    if art == "anime":
                        em.add_field(name='Year', value=result['aired']['from'][:4])
                        em.add_field(name='Episodes', value=result['episodes'])
                        em.add_field(name='Score', value=result['score'])
                        em.add_field(name='Airing', value=result['airing'])
                    else:
                        em.add_field(name='Year', value=result['published']['from'][:4])
                        em.add_field(name='Volume', value=f"{result['volumes']}")
                        em.add_field(name='Chapters', value=f"{result['chapters']}")
                        em.add_field(name='Members', value=f"{result['members']}")
                    em.add_field(name='Rating', value=result['score'])
                    em.set_thumbnail(url=result['images']['jpg']['image_url'])
                    em.set_footer(text=f"Made by:\nTReKeSS")
                    await context.send(embed=em)
                else:
                    await context.send("Could not find anything!!")
        else:
            await context.send("You did not provide any name to search for!")


    @commands.command(aliases=['setsimilarity'])
    async def set_similarity(self, context, *, similarity=None):

        try:
            similarity = float(similarity)
            if similarity > 0 and not similarity > 1:
                self.malSearchAttributes[context.guild.id].similarity = similarity
                await context.send(f"Similarity is set to: {similarity}")

            else:
                await context.send("Similarity value must be between 0 and 1!")

        except Exception:
            await context.send("Similarity value must be between 0 and 1!")




    @commands.command()
    async def tracemoe(self, context):

        malSearchAttributes = self.malSearchAttributes[context.guild.id]
        malSearchAttributes.titles = []

        try:
            url = context.message.attachments[0].url
        except IndexError:
            url = str(context.message.content).split(" ")[1]
        try:
            async with tracemoepy.AsyncTrace() as tracemoe:

                resp = await tracemoe.search(url, is_url=True)
                searched = resp.result

                results = []

                for result in searched:
                    results.append(Result(result.anilist.title.romaji, result.similarity))

                results.sort(reverse=True)

                for i in range(0, min(10, len(results))):
                    if results[i].similarity > self.malSearchAttributes[context.guild.id].similarity:
                        malSearchAttributes.titles.append(results[i].title)

                if len(malSearchAttributes.titles) > 0:
                    print(f'Searched with: {malSearchAttributes.similarity}')
                    malSearchAttributes.titles = list(set(malSearchAttributes.titles))
                    em = discord.Embed(title='Results',
                                       description=f"Try not to click on the reactions too fast, "
                                                   f"because it will broke the MAL API."
                                                   f" (if the reaction removal didn't occur) "
                                                   f"If it happens, just use the command again.",
                                       color=0x71368a)
                    for i in range(0, len(malSearchAttributes.titles)):
                        em.add_field(name=f"{i}", value=f"{malSearchAttributes.titles[i]}")
                    em.set_thumbnail(url=context.guild.me.avatar)
                    em.set_footer(text=f"Made by:\nTReKeSS")
                    malSearchAttributes.traceMoeMessage = await context.send(embed=em)
                    malSearchAttributes.context = context

                    for i in range(0, len(malSearchAttributes.titles)):
                        await malSearchAttributes.traceMoeMessage.add_reaction(f'{i}\u20e3')
                        malSearchAttributes.traceMoeMessageReactions[i] = False

                    self.malSearchAttributes[context.guild.id] = malSearchAttributes

                else:
                    await context.send("Could not find a close enough match!\n"
                                       f"Current similarity is : {malSearchAttributes.similarity}.\n"
                                       f"Maybe try searching with a lover value.\n"
                                       f"Use the {prefix}setsimilarity <value> command!")

        except TooManyRequests:
            await context.send("Too many requests.\n 5/min, 15/5min, 120/hour.")
        except Exception:
            await context.send(f"Something went wrong with the search.\n You searched: {url}")
            print(sys.exc_info())

    @commands.Cog.listener("on_reaction_add")
    async def listenTraceMoe(self, reaction, user):

        malSearchAttributes = self.malSearchAttributes[reaction.message.guild.id]
        reactions = {f'{i}\u20e3': i for i in range(len(malSearchAttributes.titles))}
        if user.id != GLOBAL_CONFIGS.bot_id:
            try:
                malSearchAttributesMessageId = malSearchAttributes.traceMoeMessage.id
                if malSearchAttributesMessageId == reaction.message.id:
                    reactedNumber = reactions.get(reaction.emoji, None)
                    if reactedNumber is not None:
                        if malSearchAttributes.traceMoeMessageReactions[reactedNumber] is False:
                            malSearchAttributes.traceMoeMessageReactions[reactedNumber] = True
                            await self.mal(malSearchAttributes.context, name=malSearchAttributes.titles[reactedNumber])
                            await malSearchAttributes.traceMoeMessage.clear_reaction(reaction)

            except AttributeError:
                pass

            except Exception:
                print(sys.exc_info())

            finally:
                self.malSearchAttributes[reaction.message.guild.id] = malSearchAttributes

    @commands.Cog.listener("on_guild_join")
    async def mal_on_guild_joined(self, guild):
        if guild.id not in self.malSearchAttributes:
            self.malSearchAttributes[guild.id] = MalSearchAttributes()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.malSearchAttributes[guild.id] = MalSearchAttributes()

async def setup(bot):
    await bot.add_cog(MalSearch(bot))


@dataclass
class Result:

    title: str
    similarity: float

    def __gt__(self, other):
        if isinstance(other, Result):
            return self.similarity > other.similarity

    def __lt__(self, other):
        if isinstance(other, Result):
            return self.similarity < other.similarity

    def __eq__(self, other):
        if isinstance(other, Result):
            return self.similarity == other.similarity

    def __ne__(self, other):
        if isinstance(other, Result):
            return self.similarity != other.similarity

    def __ge__(self, other):
        if isinstance(other, Result):
            return self.similarity >= other.similarity

    def __le__(self, other):
        if isinstance(other, Result):
            return self.similarity <= other.similarity
