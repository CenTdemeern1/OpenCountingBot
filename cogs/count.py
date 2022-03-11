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
        
    def is_channel_registered(self, channelid):
        return str(channelid) in self.channels

    def get_channel_data(self, channelid):
        with open("channels/"+str(channelid),"r") as file:
            data=file.read().split("|")
            return int(data[0]),int(data[1])
    
    def set_channel_data(self, channelid, counter, userid):
        with open("channels/"+str(channelid),"w") as file:
            file.write(f"{counter}|{userid}")
    
    def get_channel_highscore(self, channelid):
        with open("highscores/"+str(channelid),"r") as file:
            data=file.read().split("|")
            return int(data[0])
    
    def set_channel_highscore(self, channelid, counter):
        with open("highscores/"+str(channelid),"w") as file:
            file.write(f"{counter}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith("|"):
            query = message.content[1:]
            res = await self.solve_wolframalpha(query)
            await message.add_reaction("<:WolframAlpha:951901576103096330>")
            if res==None or res==[] or res==[""]:
                await message.add_reaction("<:Blunder:887422389040844810>")
                await message.reply('Wolfram|Alpha did not return an answer for that query.')
                return
            if type(res)==list:
                res=res[0]
            try:
                res = float("".join(list(filter(lambda x: x.isnumeric() or x == ".",res))))
            except Exception as e:
                await message.add_reaction("<:Blunder:887422389040844810>")
                await message.reply(f'The answer to that does not seem to convert nicely into a number. ({e})')
                raise ArithmeticError(f"Could not convert answer {res} into a number")
            await self.attempt_count(message, res)
        else:
            firstword = message.content.split(" ")[0]
            contains_digit = False
            digits = "0123456789"
            if "0x" in firstword:
                digits+="abcdefABCDEF"
            for digit in digits:
                if digit in firstword:
                    contains_digit=True
            if not contains_digit: return
            if "<@" in firstword: return
            if "<#" in firstword: return
            if "<t:" in firstword: return
            if "<a:" in firstword: return
            if "<:" in firstword: return
            try:
                ex = await self.parse_and_evaluate_expression(firstword)
            except Exception as e:
                pass
                # await message.reply(str(e))
            else:
                if not type(ex) in (int, float): return
                await self.attempt_count(message, ex)
    
    async def attempt_count(self, message, guess):
            if self.is_channel_registered(message.channel.id):
                goal_number, previous_author = self.get_channel_data(message.channel.id)
                goal_number+=1
                highscore = self.get_channel_highscore(message.channel.id)
                died = False
                if message.author.id==previous_author:
                    self.set_channel_data(message.channel.id,0,0)
                    await message.reply(f"Oof, you failed! You counted twice in a row. If you feel this was unjustified, contact the mods. The next number is 1.")
                    died = True
                elif guess == goal_number:
                    self.set_channel_data(message.channel.id,goal_number,message.author.id)
                    if goal_number>highscore:
                        await message.add_reaction("☑️")
                    else:
                        await message.add_reaction("✅")
                else:
                    self.set_channel_data(message.channel.id,0,0)
                    await message.reply(f"Oof, you failed! The next number was {goal_number}, but you said {guess}. If you feel this was unjustified, contact the mods. The next number is 1.")
                    died = True
                if died:
                    await message.add_reaction("⚠")
                    if goal_number>=highscore:
                        await message.channel.send(f"You set a new high score! ({goal_number-1})")
                        self.set_channel_highscore(message.channel.id,goal_number-1)

    async def solve_wolframalpha(self, expression):
        res = self.client.query(expression)
        if not res.success:
            return
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
        """Possible operators are:
        Add
        Remove
        Set {number}
        List"""
        try:
            if not ctx.message.author.guild_permissions.administrator:
                await ctx.reply("You're not an administrator, sorry!")
                return
        except AttributeError:
            await ctx.reply("I couldn't access your permissions! Are you in a server?")
            return
        if operator == "add":
            # with open("channels/"+str(ctx.channel.id),"w") as file:
            #     file.write("0|0")
            self.set_channel_data(ctx.channel.id,0,0)
            self.set_channel_highscore(message.channel.id,0)
            self.channels.append(str(ctx.channel.id))
            await ctx.reply("Channel has been added!")
        if operator == "remove":
            os.remove("channels/"+str(ctx.channel.id))
            os.remove("highscores/"+str(ctx.channel.id))
            self.channels.remove(str(ctx.channel.id))
            await ctx.reply("Channel has been removed!")
        if operator == "set":
            # with open("channels/"+str(ctx.channel.id),"w") as file:
            #     file.write(str(value)+"|0")
            self.set_channel_data(ctx.channel.id,value,0)
            await ctx.reply(f"The counter has been set to {value}! The next number is {value+1}!")
        if operator == "list":
            channels = ""
            for channel in ctx.guild.text_channels:
                if self.is_channel_registered(channel.id):
                    channels+=f"\n<#{channel.id}>"
            channels+=""
            await ctx.reply(embed=Embed(description=channels))

    @commands.command(name="highscore")
    async def get_highscore(self, ctx):
        hiscore = self.get_channel_highscore(ctx.channel.id)
        await ctx.reply(f"The current high score is {hiscore}.")




def setup(client):
    client.add_cog(CountCog(client))
