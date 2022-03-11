import discord
import asyncio
import json
import time
from discord.ext import commands
from discord.ext.commands import Bot

class CountCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.content == 'The wheels on the subwoofers go?':
            await message.reply("ZOOM DOKO DOMB")


def setup(client):
    client.add_cog(CountCog(client))
