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
        self.wolframalphaclient = wolframalpha.Client(self.tokens.get("tokens","wolframalphatoken"))
        self.channels = os.listdir("channels")
        
    def is_channel_registered(self, channelid):
        return str(channelid) in self.channels

    def get_channel_data(self, channelid, ForceIntegerConversions=True):
        with open("channels/"+str(channelid),"r") as file:
            data=file.read().split("|")
            if ForceIntegerConversions:
                return int(data[0]),int(data[1])
            else:
                return float(data[0]),float(data[1])
    
    def set_channel_data(self, channelid, counter, userid):
        with open("channels/"+str(channelid),"w") as file:
            file.write(f"{counter}|{userid}")
    
    def get_channel_highscore(self, channelid, ForceIntegerConversions=True):
        with open("highscores/"+str(channelid),"r") as file:
            if ForceIntegerConversions:
                return int(file.read())
            else:
                return float(file.read())
    
    def set_channel_highscore(self, channelid, counter):
        with open("highscores/"+str(channelid),"w") as file:
            file.write(f"{counter}")

    def get_channel_settings(self, channelid):
        filepath = "settings/"+str(channelid)+".json"
        if not os.path.exists(filepath):
            filepath = "settings/default.json"
        with open("settings/default.json","r") as file:
            defaultsettings = json.load(file)
        with open(filepath,"r") as file:
            defaultsettings.update(json.load(file))
            return defaultsettings

    def set_channel_setting(self, channelid, key, value):
        filepath = "settings/"+str(channelid)+".json"
        if not os.path.exists(filepath):
            filepath = "settings/default.json"
        with open(filepath,"r") as file:
            settings = json.load(file)
        with open("settings/default.json","r") as file:
            defaultsettings = json.load(file)
        if not key in defaultsettings.keys():
            raise KeyError("Setting not found")
        writepath = "settings/"+str(channelid)+".json"
        valuetype = type(defaultsettings[key])
        if valuetype in (int, float):
            number = float(value)
            if number.is_integer():
                number=int(number)
            settings.update({key:number})
        elif valuetype == bool:
            istrue = value.lower() in ["1", "true", "yes"]
            settings.update({key:istrue})
        else: #str & others
            settings.update({key:value})
        filepath = "settings/"+str(channelid)+".json"
        with open(filepath,"w") as file:
            return json.dump(settings,file)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not self.is_channel_registered(message.channel.id):
            return
        settings = self.get_channel_settings(message.channel.id)
        if message.content.startswith("|"):
            query = message.content[1:]
            await message.add_reaction("<:WolframAlpha:951901576103096330>")
            if not settings["EnableWolframAlpha"]:
                await message.add_reaction("‼")
                await message.reply('Wolfram|Alpha queries have been disabled by an administrator.')
                return
            await message.add_reaction("<:ContactingWolframAlpha:951959127150690364>")
            res = await self.solve_wolframalpha(query)
            await message.remove_reaction("<:ContactingWolframAlpha:951959127150690364>",self.client.user)
            if res==None or res==[] or res==[""]:
                await message.add_reaction("<:Blunder:887422389040844810>")
                await message.reply('Wolfram|Alpha did not return an answer for that query.')
                return
            if type(res)==list:
                res=res[0]
            try:
                if "\n" in res:
                    res=res.split("\n")[0]
            except: pass
            while res.count(".")>1:
                splitres=res.split(".")
                res=splitres[0]+("".join(splitres[1:]))
            try:
                res = float("".join(list(filter(lambda x: x.isnumeric() or x == ".",res))))
            except Exception as e:
                await message.add_reaction("<:Blunder:887422389040844810>")
                await message.reply(f'The answer to that does not seem to convert nicely into a number. ({e})')
                raise ArithmeticError(f"Could not convert answer {res} into a number")
            await self.attempt_count(message, res)
        elif settings["EnableExpressions"]:
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
        else:
            firstword = message.content.split(" ")[0]
            try:
                ex = float(firstword)
                if ex.is_integer():
                    ex=int(ex)
            except:
                pass
            else:
                await self.attempt_count(message, ex)
    
    async def attempt_count(self, message, guess):
        if self.is_channel_registered(message.channel.id):
            settings = self.get_channel_settings(message.channel.id)
            goal_number, previous_author = self.get_channel_data(message.channel.id,settings["ForceIntegerConversions"])
            goal_number+=settings["Step"]
            goal_number=round(goal_number,16)#Avoid floating point number imprecision
            if settings["RoundAllGuesses"]:
                guess=int(round(guess))
            else:
                guess=round(guess,16)
            highscore = self.get_channel_highscore(message.channel.id, settings["ForceIntegerConversions"])
            died = False
            if message.author.id==previous_author and not settings["AllowSingleUserCount"]:
                nextnumber = settings["StartingNumber"]+settings["Step"]
                await message.reply(f"Oof, you failed! You counted twice in a row. If you feel this was unjustified, contact the mods. The next number is {nextnumber}.")
                died = True
            elif guess == goal_number:
                self.set_channel_data(message.channel.id,goal_number,message.author.id)
                if goal_number>highscore:
                    await message.add_reaction("☑️")
                else:
                    await message.add_reaction("✅")
            else:
                nextnumber = settings["StartingNumber"]+settings["Step"]
                await message.reply(f"Oof, you failed! The next number was {goal_number}, but you said {guess}. If you feel this was unjustified, contact the mods. The next number is {nextnumber}.")
                died = True
            if died:
                await message.add_reaction("⚠")
                self.set_channel_data(message.channel.id,settings["StartingNumber"],0)
                point_reached = goal_number-settings["Step"]
                if point_reached>highscore:
                    await message.channel.send(f"You set a new high score! ({point_reached})")
                    self.set_channel_highscore(message.channel.id,point_reached)

    async def solve_wolframalpha(self, expression):
        res = self.wolframalphaclient.query(expression)
        if not res.success:
            return
        for idmatch in (
            "IntegerSolution", "Solution", "SymbolicSolution",
            "Result", "DecimalApproximation",
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
        """Perform operations on this channel
        Possible operators are:
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
            if self.is_channel_registered(ctx.channel.id):
                await ctx.reply("Channel has already been added!")
                return
            self.set_channel_data(ctx.channel.id,0,0)
            self.set_channel_highscore(ctx.channel.id,0)
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
            settings = self.get_channel_settings(ctx.channel.id)
            self.set_channel_data(ctx.channel.id,value,0)
            nextvalue = value+settings["Step"]
            await ctx.reply(f"The counter has been set to {value}! The next number is {nextvalue}!")
        if operator == "list":
            channels = ""
            for channel in ctx.guild.text_channels:
                if self.is_channel_registered(channel.id):
                    channels+=f"\n<#{channel.id}>"
            channels+=""
            if channels == "":
                channels="I'm not linked to any channels in this server!\nAdd channels by running the command `c#channel add` in them!"
            await ctx.reply(embed=Embed(description=channels))

    @commands.command(name="config")
    async def set_config(self, ctx, key, value):
        """Configure game settings for this channel. (THIS WILL RESET YOUR STREAK)
Available settings:

Step - Sets by what number you count, your stepping value (ex. Step 0.1 = 0.1, 0.2, 0.3, 0.4, 0.5) (defaults to 1)
StartingNumber - What number you start at (minus the Step value) (defaults to 0)
EnableWolframAlpha - Whether to enable Wolfram|Alpha queries (defaults to true)
EnableExpressions - Whether to enable (Python 3 supported) math expressions (defaults to true)
RoundAllGuesses - Whether to round all guesses to the nearest integer (defaults to false)
AllowSingleUserCount - Whether to disable the "A single person is not allowed to say 2 numbers in a row" rule (defaults to false)
ForceIntegerConversions - An extra safeguard to ensure no internal rounding errors can happen by internally only using whole numbers. Disable this if your stepping value or starting number has a decimal point. (defaults to true)"""
        try:
            self.set_channel_setting(ctx.channel.id, key, value)
        except KeyError:
            await ctx.reply(f"No setting called {key} was found!")
        else:
            await ctx.reply(f"Set {key} to {value}! (You have been warned, your streak has been reset!)")
            settings = self.get_channel_settings(ctx.channel.id)
            self.set_channel_data(ctx.channel.id,settings["StartingNumber"],0)

    @commands.command(name="highscore")
    async def get_highscore(self, ctx):
        settings = self.get_channel_settings(message.channel.id)
        hiscore = self.get_channel_highscore(ctx.channel.id, settings["ForceIntegerConversions"])
        await ctx.reply(f"The current high score is {hiscore}.")




def setup(client):
    client.add_cog(CountCog(client))
