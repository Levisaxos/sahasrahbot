import asyncio
import re

import aiocache
import aiohttp
import bs4
import discord
import html5lib
from discord.ext import commands, tasks

from config import Config as c

from ..database import config, daily, permissions
from ..util.alttpr_discord import alttpr


def is_daily_channel():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        result = await config.get_parameter(ctx.guild.id, 'DailyAnnouncerChannel')
        if result is not None:
            channels = result['value'].split(',')
            if ctx.channel.name in channels:
                return True
        return False
    return commands.check(predicate)


class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announce_daily.start()

    @commands.command(
        name='daily',
        brief='Returns the current daily seed.',
        help='Returns the currently daily seed.')
    @is_daily_channel()
    async def daily(self, ctx):
        perma_id = await find_daily_hash()
        seed = await get_daily_seed(perma_id)
        embed = await seed.embed(
            emojis=self.bot.emojis,
            notes="This is today's daily challenge.  The latest challenge can always be found at https://alttpr.com/daily"
        )
        await update_daily(hash)
        await ctx.send(embed=embed)

    @tasks.loop(minutes=5, reconnect=True)
    async def announce_daily(self):
        perma_id = await find_daily_hash()
        if await update_daily(perma_id):
            seed = await get_daily_seed(perma_id)
            embed = await seed.embed(
                emojis=self.bot.emojis,
                notes="This is today's daily challenge.  The latest challenge can always be found at https://alttpr.com/daily"
            )
            daily_announcer_channels = await config.get_all_parameters_by_name('DailyAnnouncerChannel')
            for result in daily_announcer_channels:
                guild = self.bot.get_guild(result['guild_id'])
                for channel_name in result['value'].split(","):
                    channel = discord.utils.get(
                        guild.text_channels, name=channel_name)
                    await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Daily(bot))


async def update_daily(gamehash):
    latest_daily = await daily.get_latest_daily()
    if not latest_daily['hash'] == gamehash:
        print('omg new daily')
        await daily.set_new_daily(gamehash)
        return True
    else:
        return False


@aiocache.cached(ttl=86400, cache=aiocache.SimpleMemoryCache)
async def get_daily_seed(perma_id):
    return await alttpr(hash=perma_id)


@aiocache.cached(ttl=60, cache=aiocache.SimpleMemoryCache)
async def find_daily_hash():
    website = await alttpr()
    return await website.find_daily_hash()
