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

    async def admin_check(self, ctx):
        try:
            if not ctx.message.author.guild_permissions.administrator:
                await ctx.reply("You're not an administrator, sorry!")
                return False
        except AttributeError:
            await ctx.reply("I couldn't access your permissions! Are you in a server?")
            return False
        else:
            return True

    async def channel_check(self, ctx):
        if self.is_channel_registered(ctx.channel.id):
            return True
        else:
            await ctx.reply("This channel has not been registered!")
            return False

    def get_channel_data(self, channelid, ForceIntegerConversions=True):
        with open("channels/"+str(channelid),"r") as file:
            data=file.read().split("|")
            if ForceIntegerConversions:
                return int(data[0]),int(data[1]),int(data[2])
            else:
                return float(data[0]),int(data[1]),int(data[2])
    
    def set_channel_data(self, channelid, counter, userid, timescounted):
        with open("channels/"+str(channelid),"w") as file:
            file.write(f"{counter}|{userid}|{timescounted}")
    
    def get_channel_highscore(self, channelid):
        with open("highscores/"+str(channelid),"r") as file:
            return int(file.read())
    
    def set_channel_highscore(self, channelid, counter):
        with open("highscores/"+str(channelid),"w") as file:
            file.write(f"{counter}")

    def get_default_settings(self):
        with open("settings/default.json","r") as file:
            return json.load(file)

    def get_channel_settings(self, channelid):
        filepath = "settings/"+str(channelid)+".json"
        if not os.path.exists(filepath):
            filepath = "settings/default.json"
        settings = self.get_default_settings()
        with open(filepath,"r") as file:
            settings.update(json.load(file))
            return settings

    def set_channel_setting(self, channelid, key, value):
        if value.lower().removeprefix("-") in ("nan", "inf", "infinity"):
            raise ValueError("No.")
        filepath = "settings/"+str(channelid)+".json"
        if not os.path.exists(filepath):
            filepath = "settings/default.json"
        with open(filepath,"r") as file:
            settings = json.load(file)
        defaultsettings = self.get_default_settings()
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

    def get_channel_rankability(self, channelid):
        try:
            with open("streakrankability/"+str(channelid),"r") as file:
                return bool(int(file.read()))
        except FileNotFoundError:
            self.set_channel_rankability(channelid, False)
            return False
    
    def set_channel_rankability(self, channelid, rankability):
        with open("streakrankability/"+str(channelid),"w") as file:
            file.write(str(int(rankability)))

    def check_setting_rankability(self, channelid):
        return self.get_channel_settings(channelid) == self.get_default_settings()

    def reset_channel_rankability(self, channelid):
        are_settings_rankable = self.check_setting_rankability(channelid)
        self.set_channel_rankability(channelid, are_settings_rankable)

    def reset_streak(self, channelid):
        settings = self.get_channel_settings(channelid)
        self.set_channel_data(channelid,settings["StartingNumber"],0,0)
        self.reset_channel_rankability(channelid)

    def reset_config(self, channelid):
        try: os.remove("settings/"+str(channelid)+".json")
        except FileNotFoundError: pass

    def get_leaderboards(self):
        with open("leaderboards.json","r") as file:
            return json.load(file)

    def set_leaderboards(self, data):
        with open("leaderboards.json","w") as file:
            return json.dump(data,file)

    def get_lowest_score_channel_id_from_scores(self, scores):
        lowestcandidate = None
        lowestscore = float("inf")
        for channelid in scores:
            if scores[channelid]["score"]<=lowestscore:#using <= on purpose here so we're taking out the bottom of the leaderboard even if we have a tie
                lowestscore=scores[channelid]["score"]
                lowestcandidate=channelid
        return lowestcandidate

    def get_displayable_leaderboard_format(self, leaderboards):
        out="```"
        for placing,scoredict in enumerate(sorted(leaderboards.values(),key=lambda x: x["score"], reverse=True)):
            channelname = scoredict["name"]
            guildname = scoredict["guildname"]
            score = scoredict["score"]
            placingtext = str(placing+1).zfill(2)
            out+=f"\n#{placingtext} - {guildname} #{channelname}: {score}"
        out+="\n```"
        return out

    async def check_and_place_on_leaderboard(self, message, score):
        leaderboards = self.get_leaderboards()
        if len(leaderboards["scores"])==20:
            if not score>leaderboards["metadata"]["lowest_leaderboard_score"]:
                return
        strid = str(message.channel.id)
        if strid in leaderboards["scores"]:
            if score <= leaderboards["scores"][strid]["score"]:
                return
        await message.channel.send("🎊🎊 You have reached a spot on the global leaderboards! 🎊🎊")
        recalcmessage = await message.channel.send("Now recalculating leaderboard placings...")
        leaderboards["scores"].update(
            {
                strid: {
                    "name": message.channel.name,
                    "guildname": message.guild.name,
                    "score": score
                }
            }
        )
        if len(leaderboards["scores"])>20:
            lowest = self.get_lowest_score_channel_id_from_scores(leaderboards["scores"])
            leaderboards.pop(lowest)
            lowest = self.get_lowest_score_channel_id_from_scores(leaderboards["scores"])
            leaderboards["metadata"]["lowest_leaderboard_score"]=leaderboards["scores"][lowest]["score"]
        self.set_leaderboards(leaderboards)
        await message.channel.send(self.get_displayable_leaderboard_format(leaderboards["scores"]))
        await recalcmessage.delete()

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
                res = float("".join(list(filter(lambda x: x.isnumeric() or x in ".-",res))))
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
        if not self.is_channel_registered(message.channel.id): return
        settings = self.get_channel_settings(message.channel.id)
        goal_number, previous_author, timescounted = self.get_channel_data(message.channel.id,settings["ForceIntegerConversions"])
        goal_number+=settings["Step"]
        goal_number=round(goal_number,16)#Avoid floating point number imprecision
        if settings["RoundAllGuesses"]:
            guess=int(round(guess))
        else:
            guess=round(guess,16)
        highscore = self.get_channel_highscore(message.channel.id)
        died = False
        if message.author.id==previous_author and not settings["AllowSingleUserCount"]:
            nextnumber = settings["StartingNumber"]+settings["Step"]
            await message.reply(f"Oof, you failed! You counted twice in a row. If you feel this was unjustified, contact the mods. The next number is {nextnumber}.")
            died = True
        elif guess == goal_number:
            self.set_channel_data(message.channel.id,goal_number,message.author.id, timescounted+1)
            if timescounted>=highscore:
                await message.add_reaction("☑️")
            else:
                await message.add_reaction("✅")
        else:
            nextnumber = settings["StartingNumber"]+settings["Step"]
            await message.reply(f"Oof, you failed! The next number was {goal_number}, but you said {guess}. If you feel this was unjustified, contact the mods. The next number is {nextnumber}.")
            died = True
        if died:
            await message.add_reaction("⚠")
            if timescounted>highscore:
                await message.channel.send(f"You set a new (local) high score! ({timescounted})")
                self.set_channel_highscore(message.channel.id,timescounted)
            if self.get_channel_rankability(message.channel.id):
                await self.check_and_place_on_leaderboard(message,timescounted)
            self.reset_streak(message.channel.id)

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
        # message = str(await self.solve_wolframalpha(" ".join(expression)))
        # if message in ("", "None"):
        #     message = "[Empty output]"
        message = """As of 3/19/2022, 8:30 PM CEST, the c#wolframalpha command has been disabled to prevent it from being overused and single-handedly using up the API key.

From now on, please use the official Wolfram|Alpha website.
https://wolframalpha.com/"""
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
        if not await self.admin_check(ctx): return
        if operator == "add":
            # with open("channels/"+str(ctx.channel.id),"w") as file:
            #     file.write("0|0")
            if self.is_channel_registered(ctx.channel.id):
                await ctx.reply("Channel has already been added!")
                return
            self.set_channel_data(ctx.channel.id,0,0,0)
            self.set_channel_highscore(ctx.channel.id,0)
            self.set_channel_rankability(ctx.channel.id, True)
            self.channels.append(str(ctx.channel.id))
            await ctx.reply("Channel has been added!")
        if operator == "remove":
            if not await self.channel_check(ctx): return
            os.remove("channels/"+str(ctx.channel.id))
            os.remove("highscores/"+str(ctx.channel.id))
            try: os.remove("streakrankability/"+str(ctx.channel.id))
            except FileNotFoundError: pass
            self.reset_config(ctx.channel.id)
            self.channels.remove(str(ctx.channel.id))
            await ctx.reply("Channel has been removed!")
        if operator == "set":
            # with open("channels/"+str(ctx.channel.id),"w") as file:
            #     file.write(str(value)+"|0")
            if not await self.channel_check(ctx): return
            settings = self.get_channel_settings(ctx.channel.id)
            try:
                estimatedSteps = int((value-settings["StartingNumber"])/settings["Step"])
            except:
                estimatedSteps=0
            self.set_channel_data(ctx.channel.id,value,0,estimatedSteps)
            self.set_channel_rankability(ctx.channel.id, False)
            nextvalue = value+settings["Step"]
            await ctx.reply(f"The counter has been set to {value}! The next number is {nextvalue}!")
            await ctx.send("This streak is no longer rankable.")
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
        if not await self.admin_check(ctx): return
        if not await self.channel_check(ctx): return
        try:
            self.set_channel_setting(ctx.channel.id, key, value)
        except KeyError:
            await ctx.reply(f"No setting called {key} was found!")
        except ValueError:
            await ctx.reply(f"Setting could not be changed!")
        else:
            self.reset_streak(ctx.channel.id)
            await ctx.reply(f"Set {key} to {value}! (You have been warned, your streak has been reset!)")

    @commands.command(name="resetconfig")
    async def reset_config_command(self, ctx):
        """Resets your configuration to the default (rankable) one. Also resets your streak."""
        if not await self.admin_check(ctx): return
        if not await self.channel_check(ctx): return
        self.reset_config(ctx.channel.id)
        await ctx.reply("Your configuration has been reset to the default (rankable) configuration!")
        self.reset_streak(ctx.channel.id)
        await ctx.send(f"You have been warned, your streak has been reset!")

    @commands.command(name="highscore")
    async def get_highscore(self, ctx):
        if not await self.channel_check(ctx): return
        hiscore = self.get_channel_highscore(ctx.channel.id)
        await ctx.reply(f"The current high score is {hiscore}.")

    @commands.command(name="leaderboard", aliases=["leaderboards"])
    async def display_leaderboards(self, ctx):
        leaderboards = self.get_leaderboards()
        await ctx.reply(self.get_displayable_leaderboard_format(leaderboards["scores"]))

    @commands.command(name="rankability", aliases=["rankable"])
    async def is_rankable(self, ctx):
        if not await self.channel_check(ctx): return
        rankable = "" if self.get_channel_rankability(ctx.channel.id) else " not"
        await ctx.reply(f"The current streak is{rankable} rankable.")




def setup(client):
    client.add_cog(CountCog(client))
