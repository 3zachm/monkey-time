import asyncio
import os
import io
import configparser
import datetime

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
    print("\n")
    print_log("monkey time")
    while True:
        await monkey_loop()

@bot.event
async def on_guild_join(guild):
    print_log("Joined \"" + guild.name + "\"")

@bot.command()
@commands.has_permissions(administrator=True)
async def set(ctx):
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    servers_json[str(ctx.guild.id)] = ctx.channel.id
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
@commands.has_permissions(administrator=True)
async def remove(ctx):
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    try:
        del servers_json[str(ctx.guild.id)]
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
    await ctx.send(embed=discord.Embed(
        title="monkey time stopped  🐒",
        description="monkey time has stopped in this server :(",
        color=0x000000
    ))

def print_log(str):
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}: ' + str)

async def wait_until(dt):
    now = datetime.datetime.now()
    await asyncio.sleep((dt - now).total_seconds())

async def monkey_loop():
    # wait until tomorrow at XX:XX:XX.XX
    t_time = [int(config.get('monkey time', 'hour')), int(config.get('monkey time', 'minute')), 0, 0] 
    today_time = datetime.datetime.now()
    print_log("Waiting...")
    possible_today = today_time.replace(hour=t_time[0], minute=t_time[1], second=t_time[2], microsecond=t_time[3])
    # check if the target time is still within the current day, set next monkey accordingly
    if (possible_today - today_time).total_seconds() > 0:
        next_monkey = possible_today
    else:
        tomorrow = today_time + datetime.timedelta(days = 1)
        next_monkey = tomorrow.replace(hour=t_time[0], minute=t_time[1], second=t_time[2], microsecond=t_time[3])
    print_log(f'Next monkey will occur at {next_monkey:%Y-%m-%d %H:%M:%S}')
    await wait_until(next_monkey)
    # recursively send to all servers (ok for small scale, should use dedicated link ideally)
    with open(json_loc, 'r') as r:
        servers_json = json.load(r)
    servers = servers_json.items()
    print_log("Monkey sent!")
    for s, c in servers:
        channel = bot.get_channel(c)
        await channel.send(file=discord.File(script_loc + '/monkey.mp4'))

bot.run(bot_token)