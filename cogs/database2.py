from discord.ext import commands
from database_mongo import connect
from database_mongo.plot import plotMessages, plotPoints
from database_mongo.db_con__with_other_battabot.db_con_other_battabot import get_user
import discord
import sys
from botMain import prefix


class DatabaseHandler2(commands.Cog):

    @commands.command()
    async def db_points(self, context):
        server_id = context.message.guild.id

        plotPoints.getPoints(server_id)
        await context.send(file=discord.File("Files/points.png"))

    @commands.command()
    async def db_test(self, context):
        server_id = context.message.guild.id
        user_id = context.message.author.id

        user = get_user(server_id, user_id)
        for u in user:
            await context.send(u)


async def setup(bot):
    await bot.add_cog(DatabaseHandler2(bot))
