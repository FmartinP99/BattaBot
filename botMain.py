import discord
from discord.ext import commands
from globals import  g_prefix, g_ownerid, g_ffmpeg, g_websocket_enabled
import os
import traceback

PROTECTED_MODULES = ["module_control"]  # can't unload these

# can't load <remindme> because the async control will be duplicated each time it is loaded since it works with asyncio.sleep
PROTECTED_MODULES_FROM_LOADING = ["remindme"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=f'{g_prefix}', help_command=None, intents=intents)
prefix = g_prefix

IS_BOT_READY = False

with open("token.0", "r", encoding="utf-8") as tf:
    token = tf.read()

def check_owner(context):
    return context.author.id == g_ownerid


@bot.event
async def on_ready():
    global IS_BOT_READY
    print("Bot is ready!")
    await status_to_change("New tracemoe command available")


@bot.command()
@commands.check(check_owner)
async def status(context, *msg):
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
async def on_command_error(context, error):   # triggers at every error

    if isinstance(error, commands.MissingRequiredArgument):
        await context.send(f"Missing argument!")
    else:
        print(error)
        traceback.print_exc()

if len(g_ffmpeg) == 0:
    PROTECTED_MODULES_FROM_LOADING.append('player')
    print("There is no FFMPEG path in globalsDefaultValueImport.txt")


async def load_extensions():
    print("Modules are lodaing...")
    # loads the cogs at start
    for filename in os.listdir('./cogs/'):
        if filename.endswith('.py') and not filename.endswith("database2.py"):
            if filename == "websocket.py":
                if g_websocket_enabled is True:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f" <{filename[:-3]}> module loaded!")
                else:
                    print("The websocket is turned off!!")
            else:
                if filename != "player.py" or (filename == "player.py" and len(g_ffmpeg) > 0):
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f" <{filename[:-3]}> module loaded!")
    print("Modules are loaded!")