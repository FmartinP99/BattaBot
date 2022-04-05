import difflib
from jikanpy import AioJikan
from botMain import *
import tracemoepy
from tracemoepy.errors import TooManyRequests
import sys
from globals import g_botid
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

    @commands.command()
    async def mal(self, context, *, name=""):

        name_splitted = name.split(" ")
        searched_name = ""

        if name_splitted[0] == '-manga':
            name_splitted = name_splitted[1:]

        for i in name_splitted:
            searched_name = searched_name + i + " "
        searched_name = searched_name.strip().lower()

        if searched_name != "":
            async with AioJikan() as aio_jikan:
                if not name.startswith("-manga"):
                    art = "anime"
                    results = await aio_jikan.search(search_type='anime', query=f'{searched_name}')
                else:
                    art = "manga"
                    results = await aio_jikan.search(search_type='manga', query=f'{searched_name}')
                result_list = results['results']
                if result_list:
                    titles = list()

                    for index in range(0, len(result_list)):
                        titles.append(result_list[index]['title'].lower())
                    searched_title = difflib.get_close_matches(f'{searched_name}', titles, n=1, cutoff=0.90)
                    try:
                        index = 0
                        while index < len(result_list):
                            if titles[index] == searched_title[0].lower():
                                # mal_id, url, image_url, title, airing, synopsis,
                                # type, episodes
                                #score, end_date, members, rated
                                em = discord.Embed(title=f"{result_list[index]['title']}\n{result_list[index]['url']}",
                                                      description=result_list[index]['synopsis'],
                                                      color=0x71368a)
                                em.add_field(name='Type', value=result_list[index]['type'])
                                em.add_field(name='Year', value=result_list[index]['start_date'][0:4])
                                if art == "anime":
                                    em.add_field(name='Episodes', value=result_list[index]['episodes'])
                                    em.add_field(name='Rated', value=result_list[index]['rated'])
                                    em.add_field(name='Airing', value=result_list[index]['airing'])
                                else:
                                    em.add_field(name='Volume', value=f"{result_list[index]['volumes']}")
                                    em.add_field(name='Chapters', value=f"{result_list[index]['chapters']}")
                                    em.add_field(name='Members', value=f"{result_list[index]['members']}")
                                em.add_field(name='Rating', value=result_list[index]['score'])
                                em.set_thumbnail(url=result_list[index]['image_url'])
                                em.set_footer(text=f"Made by:\nTReKeSS#3943")
                                await context.send(embed=em)
                                break
                            index += 1
                    except Exception:
                        em = discord.Embed(title=f"{result_list[0]['title']}\n{result_list[0]['url']}",
                                           description=result_list[0]['synopsis'],
                                           color=0x71368a)
                        em.add_field(name='Type', value=result_list[0]['type'])
                        em.add_field(name='Episodes', value=result_list[0]['episodes'])
                        em.add_field(name='Year', value=result_list[0]['start_date'][0:4])
                        em.add_field(name='Rating', value=result_list[0]['score'])
                        em.add_field(name='Rated', value=result_list[0]['rated'])
                        em.add_field(name='Airing', value=result_list[0]['airing'])
                        em.set_thumbnail(url=result_list[0]['image_url'])
                        em.set_footer(text=f"Made by:\nTReKeSS#3943")
                        await context.send(
                            f"Could not find a{'n' if art == 'anime' else ''} {art} with a similar enough title, so here's"
                            f" the first searched result:")
                        await context.send(embed=em)
                        print(sys.exc_info())
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
                    messageToSend = ""

                    for i in range(0, len(malSearchAttributes.titles)):
                        messageToSend = messageToSend + str(i) + ' - ' + malSearchAttributes.titles[i] + '\n'
                    messageToSend = messageToSend + "\nTry not to click on the reactions too fast, because it will broke the MAL API." \
                                                    " (if the reaction removal didn't occur)\n" \
                                                    "If it happens, just use the command again."
                    malSearchAttributes.traceMoeMessage = await context.send(f"```{messageToSend}```")
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
        reactions = {}
        for i in range(0, len(malSearchAttributes.titles)):
            reactions[f'{i}\u20e3'] = i

        if user.id != g_botid:

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

def setup(bot):
    bot.add_cog(MalSearch(bot))


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
