import discord
from discord.ext import commands
from cogs.utils import constants as const
import hashlib
import logging
import os
import ffmpeg
import time

logger = logging.getLogger(__name__)


# TODO: Command that plays Youtube music (via VPN) to access new releases early
class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = []

    @commands.command(aliases=["jasså"])
    async def jassa(self, ctx: commands.Context, args: str):
        await ctx.message.add_reaction(const.OK)
        async with ctx.channel.typing():
            name = hashlib.md5(args.encode()).hexdigest()
            filename = name + ".mp4"
            optimized = name + ".gif"

            for gif in self.cache:
                try:
                    if gif[name]:
                        logger.info("Gif cached, sending url")
                        return await ctx.send(gif[name])
                except KeyError:
                    pass

            start_time = time.time()
            logger.info("Making new gif")
            # Generate mp4 with text
            # TODO: use "pipe:" to avoid writing to disk
            try:
                (
                    ffmpeg
                    .input('media/template.mp4')
                    .drawtext(fontfile="ProximaNova-Semibold.otf", text=args, x=160, y=659, fontsize=33, fontcolor="white", enable="between(t,0.5,5)")
                    .filter('fps', fps=19)
                    .filter('scale', "400", "trunc(ow/a/2)*2", flags="lanczos")
                    .output(filename)
                    .run(quiet=True)
                )
            except ffmpeg.Error as e:
                logger.error('stdout:', e.stdout.decode('utf8'))
                logger.error('stderr:', e.stderr.decode('utf8'))
                raise e
            # Convert mp4 to gif
            logger.info("Converting mp4 to gif")
            try:
                (
                    ffmpeg
                    .filter([
                        ffmpeg.input(filename),
                        ffmpeg.input("media/palette.png")
                    ],
                        filter_name="paletteuse",
                        dither="bayer"
                    )
                    .filter("fps", fps=19, round="up")
                    .output(optimized)
                    .run(quiet=True)
                )
            except ffmpeg.Error as e:
                logger.error("stdout:", e.stdout.decode("utf8"))
                logger.error("stderr:", e.stderr.decode("utf8"))
                raise e

            logger.info(f"Successfully generated gif with {args} in {time.time()-start_time} seconds")

            upload = await ctx.send(file=discord.File(optimized))
            # Add the discord url to cache
            self.cache.append({name: upload.attachments[0].url})
            # Remove cached files
            os.remove(filename)
            os.remove(optimized)

    @jassa.error
    async def jassa_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.add_reaction(const.NO)
            await ctx.send(f"Mangler navn.\nRiktig bruk: `{ctx.prefix}jasså <navn>`")

    @commands.command(aliases=["lb"])
    @commands.guild_only()
    async def roleleaderboard(self, ctx: commands.Context, args: str = None):
        await ctx.message.add_reaction(const.OK)
        # Parse args
        if args is None:
            limit = 10
        elif args.lower() == "full":
            # Set the limit to a high number
            limit = 999999
        else:
            if args.isdigit():
                limit = int(args)
            else:
                return await ctx.send(f"{discord.utils.escape_markdown(args)} is not a valid number. Please use a number or `full`")
            if limit < 0:
                return await ctx.send("Please use a number greater than 0")
        # Get the role leaderboard
        members_list = ctx.guild.members
        leaderboard = {}
        for member in members_list:
            leaderboard[member.display_name] = len(member.roles)
        # Sort the leaderboard
        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        leaderboard_str = ""
        for i, member in enumerate(sorted_leaderboard):
            if i == limit:
                break
            username = discord.utils.escape_markdown(member[0])
            current = f"{i+1}. {username}: {member[1]} roles\n"
            if len(leaderboard_str) + len(current) >= 4096:
                await ctx.send("Too many users, displaying as many as possible")
                break
            else:
                leaderboard_str += current
        # Send the leaderboard
        # TODO: Add pagination
        embed = discord.Embed(title="Role leaderboard", description=leaderboard_str, color=discord.Color.gold())
        # embed.add_field(name="Role leaderboard", value=leaderboard_str)
        await ctx.send(embed=embed)
        await ctx.send(len(leaderboard_str))


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
