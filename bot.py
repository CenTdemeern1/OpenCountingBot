# Started with this boilerplate:
# https://github.com/N0XIRE/discord.py-boilerplate
# Thanks, N0XIRE!

bot_owner_id = 280756504674566144


# Works with Python 3.6+
import discord
import asyncio
from discord import Game
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import get
from configparser import ConfigParser
import sys

tokens = ConfigParser()
tokens.read("tokens.ini")

TOKEN = tokens["tokens"]["bottoken"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="c#", intents=intents)
startup_extensions = ["cogs.count"]#,"cogs.voice"
# client.remove_command('help')


async def on_ready():
    pass


@client.event
async def on_ready():
    # sets Playing message on discord
    await client.change_presence(activity=Game(name="on a calculator | c#help"))
    # prints succesful launch in console
    print('---\nLogged in as\nUser: ' + client.user.name + '\nID: ' + str(client.user.id) + '\n---')

# load cogs


@client.command()
async def load(ctx, string):
    if ctx.author.id != bot_owner_id: return
    string = 'cogs.' + string
    try:
        await client.load_extension(string)
        print('Loaded extension \"{}\"'.format(string))
        await ctx.message.channel.send('Loaded extension \"{}\"'.format(string))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension \"{}\"\n{}'.format(string, exc))
        await ctx.message.channel.send('Failed to load extension \"{}\"'.format(string))

# unload cogs


@client.command()
async def unload(ctx, string):
    if ctx.author.id != bot_owner_id: return
    string = 'cogs.' + string
    try:
        await client.unload_extension(string)
        print('Unloaded extension \"{}\"'.format(string))
        await ctx.message.channel.send('Unloaded extension \"{}\"'.format(string))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to unload extension \"{}\"\n{}'.format(string, exc))

# reload cogs


@client.command()
async def reload(ctx, string):
    if ctx.author.id != bot_owner_id: return
    string = 'cogs.' + string
    try:
        await client.unload_extension(string)
        print('Unloaded extension \"{}\"'.format(string))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to unload extension \"{}\"\n{}'.format(string, exc))
    try:
        await client.load_extension(string)
        print('Loaded extension \"{}\"'.format(string))
        await ctx.message.channel.send('Reloaded extension \"{}\"'.format(string))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension \"{}\"\n{}'.format(string, exc))
        await ctx.message.channel.send('Failed to load extension \"{}\"'.format(string))

# IMPORT EXTENSIONS/COGS
async def load_extensions():
    for extension in startup_extensions:
        try:
            await client.load_extension(extension)
            print('Loaded extension \"{}\"'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension \"{}\"\n{}'.format(extension, exc))
# DONE IMPORT EXTENSIONS/COGS


async def main():
    print('\n')
    async with client:
        await load_extensions()
        await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
