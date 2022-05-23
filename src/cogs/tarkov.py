# import discord
from discord.ext import commands


# TODO: Use params when searching Tarkov Wiki
class Tarkov(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(Tarkov(bot))
