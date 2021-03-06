import asyncio
import hashlib
import io
import json
import logging
import os
import random
import stat
import sys
import time
import traceback
from datetime import datetime
from distutils.util import strtobool
from urllib.parse import quote

import coloredlogs
import discord
import ffmpeg
import requests
import rule34
from bs4 import BeautifulSoup as bs
from discord.ext import commands

token = os.environ["BOT_TOKEN"]
ownerid = int(os.environ["OWNER_ID"])
tarkov_key = os.getenv("TARKOV_API")
if os.getenv("ERROR_DM") is not None:
    dm = bool(strtobool(os.getenv("ERROR_DM")))
else:
    dm = True
prefix = os.getenv("PREFIX", "+")

logger = logging.getLogger("discord")
logger.setLevel(logging.CRITICAL)
logging.Formatter()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
coloredlogs.install(
    level="INFO",
    fmt="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

rule34 = rule34.Sync()

intents = discord.Intents().default()
intents.members = True

bot = commands.Bot(command_prefix=prefix, owner_id=ownerid, intents=intents)

# Emojis :)
ok = "✅"
no = "❌"
nsfw = "🔞"

# TODO: Add a task that selects a random user to change server icon

if tarkov_key is not None:
    tarkov_market = True
    logging.info("Tarkov API enabled. (from https://tarkov-market.com)")
else:
    tarkov_market = False
    logging.warning("No tarkov-market API key found, price of items won't be available")

# Check for linux and folders
if sys.platform != "linux":
    logging.warning("Bot is not made for non Linux installations. Persistence may not work")
try:
    if os.path.isdir("/jassa-bot/output/optimized"):
        logging.info("All files are correct :). Persistence is enabled")
    else:
        os.makedirs("/jassa-bot/output/optimized")
        logging.info("Made output folders, persistence is now enabled")
    if not os.path.isfile("/jassa-bot/aliases.json"):
        logging.info("Missing aliases.json, making file")
        with open("/jassa-bot/aliases.json", "a") as f:
            f.write("{}")
        os.chmod("/jassa-bot/aliases.json", stat.S_IRWXO)
except PermissionError as e:
    logging.warning(e)
    logging.warning("Permission denied for /jassa-bot directory. Persistence will not work!")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(prefix + "jasså"))
    logging.info(f"Logged in as {bot.user}")


@bot.event
async def on_command(ctx):
    logging.info(f"{ctx.message.author} called {ctx.command}")


@bot.event
async def on_command_error(ctx, error):
    await ctx.message.remove_reaction(ok, bot.user)
    error = getattr(error, 'original', error)
    if isinstance(error, commands.NSFWChannelRequired):
        await ctx.message.add_reaction(nsfw)
        # Only send meme response in the right discord server
        if ctx.guild.id == 461648348622094347:
            await ctx.send("IKKE I GENERAL DA! KUN I <#607395883239342080>")
        else:
            await ctx.send("This command is only available in channels marked NSFW")
    elif isinstance(error, commands.NotOwner):
        await ctx.message.add_reaction(no)
        await ctx.send("You have to be the bot owner to use this command")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.message.add_reaction(no)
        await ctx.send("This command is only available in a guild")
    elif not isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown error")
        logging.error(f'"{error}" in {ctx.guild.name}: {ctx.channel.name}')
        # Only error if not already handled
        matches = [no, nsfw]
        for reaction in ctx.message.reactions:
            if any(x in reaction.emoji for x in matches):
                return
        await ctx.message.add_reaction(no)
        if dm is True:
            owner = bot.get_user(int(ownerid))
            trace = traceback.format_exception(type(error), error, error.__traceback__, file=sys.stderr)
            if "NoneType: None" in trace:
                trace = str(error)
            if len(trace) < 2000:
                await owner.send(f"**Guild:** {ctx.guild.name} **Channel:** {ctx.channel.name} **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n```\n{trace}\n```")
            else:
                await owner.send(f"Errored in {ctx.guild.name}, {ctx.channel.name} at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                await owner.send(file=discord.File(io.StringIO(trace), filename="traceback.txt"))
        traceback.print_exception(type(error), error, error.__traceback__)


@bot.command(aliases=["pog"])
async def ping(ctx):
    ping = round(bot.latency * 1000)
    await ctx.send(f"{ping}ms")
    logging.info(f"{ping}ms")


@bot.command(aliases=["jasså"])
async def jassa(ctx, args):
    await ctx.message.add_reaction(ok)
    async with ctx.channel.typing():
        name = hashlib.md5(args.encode()).hexdigest()
        filename = "/jassa-bot/output/" + name + ".mp4"
        optimized = "/jassa-bot/output/optimized/" + name + ".gif"

        if os.path.isfile(optimized):
            logging.info("Gif exists, sending file")
            await ctx.send(file=discord.File(optimized))
        else:
            start_time = time.time()
            logging.info("Making new gif")
            # Generate mp4 with text
            try:
                (
                    ffmpeg
                    .input('media/template.mp4')
                    .drawtext(fontfile="ProximaNova-Semibold.otf", text=args, x=160, y=656, fontsize=32.5, fontcolor="white", enable="between(t,0.5,5)")
                    .filter('fps', fps=19)
                    .filter('scale', "400", "trunc(ow/a/2)*2", flags="lanczos")
                    .output(filename)
                    .run(quiet=True)
                )
            except ffmpeg.Error as e:
                print('stdout:', e.stdout.decode('utf8'))
                print('stderr:', e.stderr.decode('utf8'))
                raise e
            # Convert mp4 to gif
            logging.info("Converting mp4 to gif")
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
                print("stdout:", e.stdout.decode("utf8"))
                print("stderr:", e.stderr.decode("utf8"))
                raise e
            logging.info(f"Successfully generated gif with {args} in {time.time()-start_time} seconds")

            await ctx.send(file=discord.File(optimized))


@jassa.error
async def jassa_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.add_reaction(no)
        await ctx.send("Mangler navn (eller noe annet).\nRiktig bruk: `+jasså <navn>`")


@bot.command(aliases=["shut", "shutyobitchassup", "shutyobitchass", "sybap"])
@commands.guild_only()
async def shutup(ctx):
    await ctx.message.add_reaction(ok)
    try:
        mention = ctx.message.mentions[0]
    except IndexError:
        # Get author from previous message if no one is mentioned
        history = await ctx.channel.history(limit=2).flatten()
        mention = history[1].author
    if ctx.message.role_mentions:
        await ctx.message.remove_reaction(ok, bot.user)
        await ctx.message.add_reaction(no)
        return await ctx.send("You mentioned a role. Please mention a user.")
    if mention == ctx.message.author:
        await ctx.message.remove_reaction(ok, bot.user)
        await ctx.message.add_reaction(no)
        return await ctx.send("Unable to find a user to mute (mention them)")
    if mention.bot:
        await ctx.message.remove_reaction(ok, bot.user)
        await ctx.message.add_reaction(no)
        return await ctx.send("Won't mute a bot ;)")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role is None:
        await ctx.message.remove_reaction(ok, bot.user)
        await ctx.message.add_reaction(no)
        return await ctx.send("The role `Muted` does not exist. Has it been renamed?")
    # Make sure users don't accidentally get muted in VCs
    # TODO: Optimize this
    channels = ctx.guild.voice_channels
    for channel in channels:
        # ? If user calling command is in a vc with the other, also do vc mute
        await channel.set_permissions(muted_role, speak=True)
    await ctx.message.author.add_roles(muted_role)
    await mention.add_roles(muted_role)
    await ctx.send("https://tenor.com/view/meryl-streep-shut-up-yell-gif-15386483")
    await asyncio.sleep(60)
    await ctx.message.author.remove_roles(muted_role)
    await mention.remove_roles(muted_role)


@bot.command(aliases=["q"])
async def quest(ctx, *, args: str):
    await ctx.message.add_reaction(ok)
    query = quote(args)
    search_url = "https://escapefromtarkov.gamepedia.com/Special:Search?search=" + query
    r = requests.get(search_url)
    results = bs(r.text, "html.parser")
    if results.find("a", class_="unified-search__result__title"):
        result = results.find("a", class_="unified-search__result__title").get("href")
        r = requests.get(result)
        page = bs(r.text, "html.parser")
    else:
        page = results
    if page.find("table", class_="plainlinks ambox ambox-green"):
        result = "https://escapefromtarkov.gamepedia.com" + page.find("div", class_="mw-parser-output").find("a").get("href")
        r = requests.get(result)
        page = bs(r.text, "html.parser")
    title = page.find("h1").get_text()
    if "Search results for" in title:
        await ctx.send(f"Unable to find {discord.utils.escape_markdown(args)}, try being more specific.")
        return
    embed = discord.Embed(title=title, url=r.url)

    if tarkov_market:
        api = requests.get('https://tarkov-market.com/api/v1/item?q=' + title, headers={'x-api-key': tarkov_key})
        try:
            tarkov_item = api.json()[0]
        except IndexError:
            # If no results are found, state so
            embed.add_field(name="Price", value=f"No results found for {title}")
            return
        name = tarkov_item["name"]
        price = format(tarkov_item["price"], ",")
        avg24h = format(tarkov_item["avg24hPrice"], ",")
        per_slot = format(int(tarkov_item["price"] / tarkov_item["slots"]), ",")
        trader_name = tarkov_item["traderName"]
        trader_price = format(tarkov_item["traderPrice"], ",")

        # Check if wiki and API name is same, if not display API name to avoid wrong price
        if name == title:
            name_string = "Price"
        else:
            name_string = f"Price ({name})"

        embed.add_field(name=name_string, value=f"**Current:** {price} ₽\n**Per slot:** {per_slot} ₽\n**24h average:** {avg24h} ₽\n**{trader_name}:** {trader_price} ₽")

    if page.find(id="Quests"):
        quests = page.find(id="Quests").find_parent("h2").find_next_sibling("ul").find_all("li")
        quests_string = ""
        for quest in quests:
            text = quest.get_text()
            for href in quest.find_all("a"):
                quest_name = href.get_text()
                quest_url = "https://escapefromtarkov.gamepedia.com" + href.get("href")
                text = text.replace(quest_name, f"[{quest_name}]({quest_url})")
            if "in raid" in text:
                text = text.replace("in raid", "**in raid**")
            quests_string += text + "\n"
        if len(quests_string) > 1024:
            embed.add_field(name="Quests", value=f"Too many quests to show, see more [here]({r.url + '#Quests'})", inline=False)
        else:
            embed.add_field(name="Quests", value=quests_string, inline=False)

    if page.find(id="Hideout"):
        uses_element = page.find(id="Hideout").find_parent("h2").find_next_sibling()
        uses_string = ""
        if uses_element.name == "p":
            uses_string = uses_element.text
        else:
            uses = uses_element.find_all("li")
            for use in uses:
                uses_string += use.get_text() + "\n"
        if len(uses_string) > 1024:
            embed.add_field(name="Hideout", value=f"Too many hideout uses to show, see more [here]({r.url + '#Hideout'})", inline=False)
        else:
            embed.add_field(name="Hideout", value=uses_string, inline=False)

    # TODO: Fix formatting for Trading and Crafting embed
    #       Fix weird formatting for multiple items (both with x amount and + another item)
    #       Formatting for additional notes (ex. "After completing his task ...")
    if page.find(id="Trading"):
        trades = page.find(id="Trading").find_parent("h2").find_next_sibling("table").find_all("tr")
        trades_string = ""
        previous_level = ""
        for trade in trades:
            th = trade.find_all("th")
            trader_info = th[2].get_text().strip().split()
            trader = trader_info[0]
            trader_level = trader_info[1]
            barter_in = th[0].get_text().strip()
            barter_out = th[4].get_text().strip()
            if trader_level != previous_level:
                trades_string += f"**{trader} {trader_level}:**\n"
            previous_level = trader_level
            trades_string += f"{barter_in} -> {barter_out}\n"
        if len(trades_string) > 1024:
            embed.add_field(name="Trading", value=f"Too many trades to show, see more [here]({r.url + '#Trading'})", inline=False)
        else:
            embed.add_field(name="Trading", value=trades_string, inline=False)

    if page.find(id="Crafting"):
        crafts = page.find(id="Crafting").find_parent("h2").find_next_sibling("table").find_all("tr")
        crafts_string = ""
        previous_station = ""
        for craft in crafts:
            th = craft.find_all("th")
            station = th[2].find("big").get_text()
            time = th[2].get_text().strip().replace(station, "")
            craft_in = th[0].get_text().strip()
            craft_out = th[4].get_text().strip()
            if station != previous_station:
                crafts_string += f"**{station}:**\n"
            previous_station = station
            crafts_string += f"{time}: {craft_in} -> {craft_out}\n"
        if len(crafts_string) > 1024:
            embed.add_field(name="Crafting", value=f"Too many crafts to show, see more [here]({r.url + '#Crafting'})", inline=False)
        else:
            embed.add_field(name="Crafting", value=crafts_string, inline=False)
    icon = None

    # Check for icon
    if page.find("td", class_="va-infobox-icon"):
        icon = page.find("td", class_="va-infobox-icon").find("img").get("src")
    else:
        # TODO: Make it so that it retries until it finds an item
        if page.find("td", class_="va-infobox-mainimage-image"):
            icon = page.find("td", class_="va-infobox-mainimage-image").find("img").get("src")
        embed.set_footer(text="This might not be an item")

    if icon is not None:
        embed.set_thumbnail(url=icon)
    await ctx.send(embed=embed)


@quest.error
async def quest_error(ctx, error):
    await ctx.message.add_reaction(no)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing search query. Usage: `+quest <query>`")
    else:
        await ctx.send("Unknown error when processing command. ||<@140586848819871744>||")


@bot.command()
@commands.has_guild_permissions(administrator=True)
async def vcmute(ctx):
    # This command has only been tested with the Vexera Muted role
    await ctx.message.add_reaction(ok)
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role is None:
        return await ctx.send("The role `Muted` does not exist. Has it been renamed?")
    channels = ctx.guild.voice_channels
    perm = not channels[0].overwrites_for(muted_role).speak
    for channel in channels:
        await channel.set_permissions(muted_role, speak=perm)
    await ctx.send(f"Set Speak permission for the Muted role to {perm} in {len(channels)} voice channels")


@bot.command(aliases=["mv"])
@commands.has_guild_permissions(move_members=True)
async def moveall(ctx, *, channel: str):
    await ctx.message.add_reaction(ok)
    with open("/jassa-bot/aliases.json", "r") as f:
        aliases = json.load(f)
    try:
        channel = aliases[str(ctx.guild.id)][channel]
        channel = bot.get_channel(int(channel))
    except KeyError:
        channel = discord.utils.find(lambda x: x.name == channel, ctx.guild.voice_channels)

    for member in ctx.message.author.voice.channel.members:
        await member.move_to(channel)
        logging.info(f"Moved {member} to {channel} in {ctx.guild}")


@moveall.error
async def moveall_error(ctx, error):
    await ctx.message.add_reaction(no)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing voice channel ID/name to move to. Usage: `+moveall <vc id/name>`")
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("Unable to find channel")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions for this command (Move Members)")


@bot.command(aliases=["mvalias", "movealias"])
@commands.has_guild_permissions(administrator=True)
async def alias(ctx, alias: str, channel: discord.VoiceChannel = None):
    await ctx.message.add_reaction(ok)
    with open("/jassa-bot/aliases.json", "r") as f:
        aliases = json.load(f)
    try:
        aliases[str(ctx.guild.id)]
    except KeyError:
        print("Guild ID not already in list, adding it")
        aliases[str(ctx.guild.id)] = {}

    if channel is None:
        await ctx.send(f"Removed alias for channel ID {aliases[str(ctx.guild.id)][alias]}")
        aliases[str(ctx.guild.id)].pop(alias)
    else:
        alias_list = {}
        alias_list[alias] = str(channel.id)
        aliases[str(ctx.guild.id)].update(alias_list)
        await ctx.send("Added alias for channel")

    with open("/jassa-bot/aliases.json", "w") as f:
        json.dump(aliases, f, indent=4)


@alias.error
async def alias_error(ctx, error):
    await ctx.message.add_reaction(no)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing alias and/or channel ID. Usage: `+alias <alias> <channel ID/name in quotes>`")
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("Unable to find channel")


@bot.command(aliases=["lb", "rolelb", "leaderboard"])
async def roleleaderboard(ctx, arg: str = None):
    try:
        await ctx.message.add_reaction(ok)
        if arg is None:
            limit = 11
        elif arg == "full":
            limit = -999999
        else:
            limit = int(arg) + 1
        members_list = ctx.guild.members
        roles = {}
        for member in members_list:
            roles[member.display_name] = len(member.roles)
        sorted_list = {k: v for k, v in sorted(roles.items(), key=lambda item: item[1], reverse=True)}
        embed = discord.Embed(colour=discord.Colour.gold())
        value_string = ""
        role_place = 1
        for item in sorted_list.items():
            if role_place == limit:
                break
            username = discord.utils.escape_markdown(item[0], ignore_links=False)
            current = f"{role_place}. {username}: {item[1]} roles\n"
            if len(value_string) + len(current) >= 1024:
                await ctx.send("Too many users, displaying as many as possible")
                break
            else:
                value_string += current
            role_place += 1
        embed.add_field(name="Role leaderboard", value=value_string)
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.message.add_reaction(no)
        await ctx.message.remove_reaction(ok, bot.user)
        await ctx.send("Command only accepts either numbers or `full` as arguments")


@roleleaderboard.error
async def lb_error(ctx, error):
    await ctx.message.add_reaction(no)


@bot.command(aliases=["rule34"])
@commands.is_nsfw()
async def r34(ctx, *, tags):
    # Check for illegal tags
    if ("cub" or "loli" or "shota" or "child" or "underage" or "shotacon") in tags:
        await ctx.message.add_reaction(nsfw)
        await ctx.send("NEI TOS")
    else:
        logging.info(f"Rule34: Searching for {tags}")
        await ctx.message.add_reaction(ok)
        # TODO: Swap to use getImages instead
        xml_url = rule34.URLGen(tags + "+-cub -loli -underage -shotacon -shota")
        logging.info(f"Got API url for {tags}: {xml_url}")
        xml = bs(requests.get(xml_url).text, "lxml")
        urls = []
        for post in xml.findAll("post"):
            file_url = post.attrs["file_url"]
            urls += [file_url]
        count = len(urls)
        count_text = str(count)
        if count >= 100:
            count_text = "100+"
        if count >= 1:
            random_url = random.choice(urls)
            await ctx.send(f"Found {count_text} results, here is one of them")
            await ctx.send(random_url)
            logging.info(f"Rule34: Sent {random_url} with tag(s): {tags}")
        else:
            logging.info(f"Rule34: No posts were found with the tag(s): {tags}")
            await ctx.send(f"No posts were found with the tag(s): {tags}")


@r34.error
async def r34_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.add_reaction(no)
        await ctx.send("Missing tags to search for.\nUsage: `+r34/rule34 <tags>` or for multiple tags `+r34/rule34 <tag1> <tag2> ...`")


@bot.command()
@commands.is_owner()
async def close(ctx):
    ctx.add_reaction("👋")
    await bot.close()


bot.run(token)
