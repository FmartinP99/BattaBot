from discord.ext import commands
from database_mongo import connect
from database_mongo.plot import plotMessages, plotPoints
import discord
import sys
from botMain import prefix


class DatabaseHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ignored_startswiths = [prefix, "!", "-"]

    @commands.command()
    async def db_insert(self, context):
        server_id = context.message.guild.id
        name = context.message.author.name
        discriminator = context.message.author.discriminator
        person_id = context.message.author.id

        return_value = connect.insert(server_id, name, discriminator, person_id)
        await context.send(return_value)

    @commands.Cog.listener("on_message")
    async def message_exp_count(self, message):
        user_id = message.author.id
        server_id = message.guild.id

        if connect.find(server_id, user_id) is True and not str(message.content).startswith(tuple(self.ignored_startswiths)):
            exp = min(len(message.content), 100)

            connect.update(server_id, user_id, exp)
            connect.message_query(server_id, user_id)

    @commands.command()
    async def db_getme(self, context):
        server_id = context.message.guild.id
        person_id = context.message.author.id
        name, xp, level = connect.get_me(server_id, person_id)

        if name is not None:
            em = discord.Embed(title=f'{name}',
                               description=f"Level: {level}\nExp: {xp} out of {level * 1000}",
                               color=context.author.color)
            em.set_thumbnail(url=context.author.avatar_url)
            em.set_footer(text=f"Made by:\nTReKeSS#3943")
            await context.send(embed=em)
        else:
            await context.send("You are not in the database!")

    @commands.command()
    async def db_get(self, context, *, user="", discriminator=None):

        try:

            if user[-5] == "#":
                discriminator = int(user[-4:])
                user = user[0:len(user) - 5]

            server_id = context.message.guild.id
            name = ''.join(user)
            if discriminator is not None:
                user = connect.get_user(server_id, name, discriminator=discriminator)
            else:
                user = connect.get_user(server_id, name)

            if user is not None:
                username = user['Name']
                xp = int(user['Exp'])
                level = int(user['Level'])
                user_id = int(user['userID'])

                guild = self.bot.get_guild(server_id)
                member = await guild.fetch_member(user_id)
                em = discord.Embed(title=f'{username}',
                                   description=f"Level: {level}\nExp: {xp} out of {level * 1000}",
                                   color=member.color)
                em.set_thumbnail(url=member.avatar_url)
                em.set_footer(text=f"Made by:\nTReKeSS#3943")
                await context.send(embed=em)
        except Exception:
            print(sys.exc_info())

    @commands.command()
    async def db_activity(self, context, *, queryDate=None):
        server_id = context.message.guild.id
        iserror = plotMessages.get_data(server_id, queryDate)

        if not iserror:
            await context.send(file=discord.File("Files/diagram.png"))
        else:
            if iserror == "Empty":
                await context.send("Don't have the necessary data..")
            elif iserror == "Error":
                await context.send("Wrong keyword!")


    @commands.command()
    async def db_points(self, context):
        server_id = context.message.guild.id
        try:
            plotPoints.getPoints(server_id)

            await context.send(file=discord.File("Files/points.png"))
        except Exception:
            print(sys.exc_info())


    @commands.command()
    async def db_updateme(self, context):
        server_id = context.message.guild.id
        person_id = context.message.author.id
        newName = context.message.author.name
        discriminator = int(context.message.author.discriminator)

        if connect.find(server_id, person_id) is True:
            oldName, oldDiscriminator = connect.update_me(server_id, person_id, newName, discriminator)

            if oldName is not None:
                await context.send(
                    f"{newName}#{discriminator} updated in the database! Old name: {oldName}#{oldDiscriminator}")
            else:
                await context.send("There is no need to update you!")
        else:
            await context.send(f"You are not in the database!\n Use `{prefix}db_insert>`")


    @commands.Cog.listener()
    async def on_ready(self):
        connect.replace()



def setup(bot):
    bot.add_cog(DatabaseHandler(bot))
