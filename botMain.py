import discord
from discord.ext import commands
from globals import g_database, g_prefix, g_ownerid, g_api, g_ffmpeg
import os
from database_mongo import connect

PROTECTED_MODULES = ["help", "module_control"]  # can't unload these
PROTECTED_MODULES_FROM_LOADING = []  # can't load these

bot = commands.Bot(command_prefix=f'{g_prefix}', help_command=None)
prefix = g_prefix

with open("token.0", "r", encoding="utf-8") as tf:
    token = tf.read()


def check_owner(context):
    return context.author.id == g_ownerid


@bot.event
async def on_ready():
    print("Bot is ready!")
    await status_to_change("New tracemoe command available")
    if g_database is True:
        connect.start()
    else:
        print("You didn't provide a database!")



@bot.command()
@commands.check(check_owner)
async def status(context, *msg):
    print(bot.id)
    msg = ' '.join(msg)
    await status_to_change(msg)


async def status_to_change(status):
    print(status)
    await bot.change_presence(activity=discord.Game(f"{status}"))


# alias adding
@bot.command(aliases=['piing'])
async def ping(context):
    await context.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.event
async def on_command_error(context, error):   # összes hibánál triggerelődik

    if isinstance(error, commands.MissingRequiredArgument): # összes MissingRequiredArgumentre nézi
        await context.send(f"Missing argument!")


print("Modules are lodaing...")
# loads the cogs at start
for filename in os.listdir('./cogs/'):
    if filename.endswith('.py'):
        if filename == "database.py" or filename == "group.py":
            if g_database is True:
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f" <{filename[:-3]}> module loaded!")
            else:
                print("The database is turned off!!")
        else:
            if filename != "player.py" or (filename == "player.py" and len(g_ffmpeg) > 0):
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f" <{filename[:-3]}> module loaded!")
print("Modules are loaded!")

if g_api is False:
    print(f"The bot's API is disabled!")

if len(g_ffmpeg) == 0:
    PROTECTED_MODULES_FROM_LOADING.append('player')
    print("There is no FFMPEG path in globalsDefaultValueImport.txt")

if g_database == False:
    PROTECTED_MODULES_FROM_LOADING.append('database')
    PROTECTED_MODULES_FROM_LOADING.append('group')

