import discord
import asyncio
import json
import time
from discord.ext import commands
from discord.ext.commands import Bot
from configparser import ConfigParser
import ast
import wolframalpha

class CountCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.tokens = ConfigParser()
        self.tokens.read("tokens.ini")
        self.client = wolframalpha.Client(self.tokens.get("tokens","wolframalphatoken"))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content == 'The wheels on the subwoofers go?':
            await message.reply("ZOOM DOKO DOMB")

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


def setup(client):
    client.add_cog(CountCog(client))
