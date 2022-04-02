import discord
import asyncio
import json
import time
from discord.ext import tasks, commands
from discord.ext.commands import Bot
from discord import Embed
import gtts
import random

class VoiceCog(commands.Cog):
	def __init__(self, client):
		self.client = client
	
	@commands.command(hidden=True)
	async def aprilfoolsspeakthingdoitnow(self, ctx):
		if ctx.guild.voice_client:
			vc = ctx.guild.voice_client
		else:
			vc = await ctx.author.voice.channel.connect()
		count = 0
		while True:
			count += 1
			lang = "en"
			if random.random()>0.8:
				lang = random.choice(["nl","ja","fr","de","id","it","ko","pt-PT","ru","es","cy","cs","zh-CN"])
			tts = gtts.gTTS(str(count), lang=lang)
			with open(f"vc/{ctx.guild.id}.mp3", "wb") as file:
				tts.write_to_fp(file)
			vc.play(discord.FFmpegPCMAudio(source=f"vc/{ctx.guild.id}.mp3"))
			await asyncio.sleep(5)


def setup(client):
	client.add_cog(VoiceCog(client))
