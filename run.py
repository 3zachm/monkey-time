import asyncio
import os
import io
import configparser
import datetime
import random

import discord
import json
from discord.ext import commands, tasks

script_loc = os.path.dirname(os.path.realpath(__file__))
config_loc = script_loc + '/config.ini'
json_loc = script_loc + '/servers.json'

if not os.path.exists(config_loc):
    config = configparser.ConfigParser()
    config['discord'] = {'token': ''}
    config['monkey time'] = {'hour':'6', 'minute':'0'}
    config.write(open(config_loc, 'w'))
    print('Config generated. Please edit it with your token.')
    quit()

if not os.path.exists(json_loc):
    with open(json_loc, 'w') as w:
        json.dump({}, w, indent=4)

with open(config_loc) as c:
    discord_config = c.read()
config = configparser.RawConfigParser(allow_no_value=True)
config.read_file(io.StringIO(discord_config))

bot_token = config.get('discord', 'token')
bot = commands.Bot(command_prefix="!monkey ")

@bot.event
async def on_ready():
    if not hasattr(bot, 'appinfo'):
        bot.appinfo = await bot.application_info()
    print("\n")
    print_log("monkey time")
    bot.last_video = None
    bot.video_list = []
    make_owners(script_loc + '/owners.json', bot)
    while True:
        await monkey_loop()

@bot.event
async def on_guild_join(guild):
    print_log("Joined \"" + guild.name + "\"")

@bot.command()
async def set(ctx):
    if ctx.guild is None:
        guild_id = ctx.author.id
        channel_id = 1
    else:
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        if ctx.message.author.guild_permissions.administrator is not True:
            return
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    servers_json[str(guild_id)] = channel_id
    with open(json_loc, 'w') as w:
        json.dump(servers_json, w, indent=4)
    initial_c = 0xFF0000
    message = await ctx.send(embed=discord.Embed(
        title="monkey time  🎷🐒",
        description="monkey time has been set to be received in this channel!\nthere's only one monkey time per server",
        color=initial_c
    ))
    colors = [0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082, 0x9400D3]
    for _ in range(2):
        for c in colors:
            await message.edit(embed=discord.Embed(
                title="monkey time  🎷🐒",
                description="monkey time has been set to be received in this channel!\nthere's only one monkey time per server",
                color=c
            ))
            await asyncio.sleep(1)

@bot.command()
async def remove(ctx):
    if ctx.guild is None:
        guild_id = ctx.author.id
    else:
        guild_id = ctx.guild.id
        if ctx.message.author.guild_permissions.administrator is not True:
            return
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    try:
        del servers_json[str(guild_id)]
        embed=discord.Embed(
            title="monkey time stopped  🐒",
            description="monkey time has stopped in this server :(",
            color=0x000000
        )
    except KeyError:
        embed=discord.Embed(
            title="monkey time isn't set here",
            description="set monkey time with !monkey set",
            color=0x000000
        )
    with open(json_loc, 'w') as w:
        json.dump(servers_json, w, indent=4)
    await ctx.send(embed=embed)

def owner_check(ctx):
    with open(script_loc + '/owners.json', 'r') as r:
        owner_list = json.load(r)
    for owner in owner_list['DISCORD_IDS']:
        if owner['id'] == ctx.message.author.id:
            return True
    return False

@bot.command()
@commands.check(owner_check)
async def queue(ctx, *, video):
    if os.path.exists(script_loc + "/uploads/" + video):
        bot.video_list.append(video)
        await ctx.send("Added `{0}` to the queue".format(video))
    else:
        await ctx.send("`" + (script_loc + "/uploads/" + video) + "`" + " does not exist")

@bot.command()
@commands.check(owner_check)
async def cancel(ctx, index):
    try:
        index = int(index)
        video = bot.video_list[index]
        del bot.video_list[index]
        await ctx.send("{0} was removed".format(video))
    except IndexError:
        await ctx.send("Index {0} doesn't exist".format(index))
    except ValueError:
        await ctx.send("{0} is not a valid integer".format(index))

@bot.command()
@commands.check(owner_check)
async def list(ctx):
    message = "```Current queue:\n\n"
    count = 0
    for video in bot.video_list:
        message += "{0}. {1}\n".format(count, video)
        count+= 1
    message += "```"
    await ctx.send(message)

def print_log(str):
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}: ' + str)

def make_owners(path, bot):
    if not os.path.exists(path):
        ids = {"DISCORD_IDS": []}
        discrim = str(bot.appinfo.owner).replace(str(bot.appinfo.owner.name) + "#", '')
        ids["DISCORD_IDS"].append({"name": bot.appinfo.owner.name, "discrim": discrim, "id": bot.appinfo.owner.id})
        with open(path, 'w') as w:
            json.dump(ids, w, indent=4)

async def wait_until(dt):
    now = datetime.datetime.now()
    await asyncio.sleep((dt - now).total_seconds())

async def monkey_loop():
    # get random video until it isn't the same as the last one
    new_video = False
    if len(bot.video_list) > 0:
        video = bot.video_list[0]
        new_video = True
    while new_video is False:
        new_video = random.choice(os.listdir(script_loc + "/uploads/"))
        if bot.last_video != new_video:
            bot.video_list.append(new_video)
            new_video = True
    # wait until tomorrow at XX:XX:XX.XX
    t_time = [int(config.get('monkey time', 'hour')), int(config.get('monkey time', 'minute')), 0, 0]
    today_time = datetime.datetime.now()
    possible_today = today_time.replace(hour=t_time[0], minute=t_time[1], second=t_time[2], microsecond=t_time[3])
    # check if the target time is still within the current day, set next monkey accordingly
    if (possible_today - today_time).total_seconds() > 0:
        next_monkey = possible_today
    else:
        tomorrow = today_time + datetime.timedelta(days = 1)
        next_monkey = tomorrow.replace(hour=t_time[0], minute=t_time[1], second=t_time[2], microsecond=t_time[3])
    print_log(f'Next monkey will occur at {next_monkey:%Y-%m-%d %H:%M:%S}')
    await wait_until(next_monkey)
    if bot.video_list == 0:
        bot.video_list[0] = random.choice(os.listdir(script_loc + "/uploads/"))
    # recursively send to all servers (ok for small scale, should use dedicated link ideally)
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    servers = servers_json.items()
    bot.last_video = bot.video_list[0]
    print_log("Sending " + bot.video_list[0] + "...")
    for s, c in servers:
        if c == 1:
            member = await bot.fetch_user(s)
            channel = await member.create_dm()
            guild_name = str(member)
        else:
            channel = await bot.fetch_channel(c)
            guild = await bot.fetch_guild(s)
            guild_name = guild.name
        await channel.send(file=discord.File(script_loc + '/uploads/' + bot.video_list[0]))
        print_log("Sent to \"" + str(guild_name) + "\"")
    if len(bot.video_list) > 0:
        del bot.video_list[0]

bot.run(bot_token)