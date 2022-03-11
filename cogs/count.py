import discord
import asyncio
import json
import time
from discord.ext import commands
from discord.ext.commands import Bot
from discord import Embed
from configparser import ConfigParser
import ast
import wolframalpha
import os

class CountCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.tokens = ConfigParser()
        self.tokens.read("tokens.ini")
        self.client = wolframalpha.Client(self.tokens.get("tokens","wolframalphatoken"))
        self.channels = os.listdir("channels")
        
    def is_channel_registered(self,channelid):
        return str(channelid) in self.channels

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.isnumeric():
            if self.is_channel_registered(message.channel.id):
                with open("channels/"+str(message.channel.id),"r") as file:
                    goal_number = int(file.read())+1
                if int(message.content) == goal_number:
                    with open("channels/"+str(message.channel.id),"w") as file:
                        file.write(str(goal_number))
                    await message.add_reaction("✅")
                else:
                    with open("channels/"+str(message.channel.id),"w") as file:
                        file.write("0")
                    await message.reply(f"Oof, you failed! The next number was {goal_number}. If you feel this was unjustified, contact the mods.")

    async def solve_wolframalpha(self, expression):
        res = self.client.query(expression)
        for idmatch in (
            "IntegerSolution", "Solution", "SymbolicSolution",
            "Result",
            "RealAlternateForm", "AlternateForm"
            ):
            for pod in res.pods:
                if pod.id == idmatch:
                    answers = []
                    for subpod in pod.subpods:
                        answers.append(subpod.plaintext)
                    return answers

    @commands.command()
    async def wolframalpha(self, ctx, *expression):
        message = str(await self.solve_wolframalpha(" ".join(expression)))
        if message in ("", "None"):
            message = "[Empty output]"
        await ctx.reply(message)

    async def parse_and_evaluate_expression(self, expression):
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError:
            return
        if not all(isinstance(node, (ast.Expression,
                ast.UnaryOp, ast.unaryop,
                ast.BinOp, ast.operator,
                ast.Num)) for node in ast.walk(tree)):
            raise ArithmeticError(expression+" is not a valid or safe expression.")
        result = eval(compile(tree, filename='', mode='eval'))
        return result

    @commands.command()
    async def expr(self, ctx, *expression):
        try:
            message = str(await self.parse_and_evaluate_expression(" ".join(expression)))
        except ArithmeticError:
            ctx.reply("ArithmeticError: "+expression+" is not a valid or safe expression.")
        if message in ("", "None"):
            message = "[Empty output]"
        await ctx.reply(message)

    @commands.command(aliases=["channels"])
    async def channel(self, ctx, operator, value=0):
        if not ctx.message.author.guild_permissions.administrator:
            await ctx.reply("You're not an administrator, sorry!")
            return
        if operator == "add":
            with open("channels/"+str(ctx.channel.id),"w") as file:
                file.write("0")
            self.channels.append(str(ctx.channel.id))
            await ctx.reply("Channel has been added!")
        if operator == "remove":
            os.remove("channels/"+str(ctx.channel.id))
            self.channels.remove(str(ctx.channel.id))
            await ctx.reply("Channel has been removed!")
        if operator == "set":
            with open("channels/"+str(ctx.channel.id),"w") as file:
                file.write(str(value))
            await ctx.reply(f"The counter has been set to {value}! The next number is {value+1}!")
        if operator == "list":
            channels = ""
            for channel in ctx.guild.text_channels:
                if self.is_channel_registered(channel.id):
                    channels+=f"\n<#{channel.id}>"
            channels+=""
            await ctx.reply(embed=Embed(description=channels))




def setup(client):
    client.add_cog(CountCog(client))
