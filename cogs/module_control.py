from discord.ext import commands
from botMain import check_owner, bot, PROTECTED_MODULES, PROTECTED_MODULES_FROM_LOADING
import os


class ModuleControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(check_owner)  # if TRUE it runs if FALSE it won't
    async def load(self, context, extension):
        if extension not in PROTECTED_MODULES_FROM_LOADING and extension not in PROTECTED_MODULES:
            bot.load_extension(f'cogs.{extension}')
            print(f"{extension} LOADED!")
            await context.send(f"{extension} loaded!")
        else:
            await context.send("This module is protected from loading!")

    @commands.command()
    @commands.check(check_owner)
    async def unload(self, context, extension):
        if extension not in PROTECTED_MODULES and extension not in PROTECTED_MODULES_FROM_LOADING:
            bot.unload_extension(f'cogs.{extension}')
            print(f"{extension} DELETED!")
            await context.send(f"{extension} unloaded!")
        else:
            await context.send(f"This module is protected from unloading!")

    @commands.command()
    @commands.check(check_owner)
    async def reload(self, context, extension):
        if extension not in PROTECTED_MODULES_FROM_LOADING:
            bot.unload_extension(f'cogs.{extension}')
            bot.load_extension(f'cogs.{extension}')
            await context.send(f"{extension} reloaded!")
        else:
            await context.send("This module is protected from reloading!")

    @load.error  # triggers at only the <load> command
    async def load_error(self, context, error):
        if error not in os.listdir('./cogs/') and check_owner(context):
            await context.send("Can't load this module. (Probably not exists.)")
        else:
            await context.send("You are not authorized to do this!")

    @unload.error
    async def unload_error(self, context, error):
        if error not in os.listdir('./cogs/') and check_owner(context):
            await context.send("Can't unload this module. (Probably not exists.)")
        else:
            await context.send("You are not authorized to do this!")

    @reload.error
    async def reload_error(self, context, error):
        if error not in os.listdir('./cogs/') and check_owner(context):
            await context.send("Can't reload this module. (Probably not exists.)")
        else:
            await context.send("You are not authorized to do this!")



def setup(bot):
    bot.add_cog(ModuleControl(bot))
