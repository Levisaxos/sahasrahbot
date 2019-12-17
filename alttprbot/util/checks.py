from discord.ext import commands

from ..database import config


def restrict_to_channels_by_guild_config(parameter, default=True):
    async def predicate(ctx):
        if ctx.guild is None:
            return True

        result = await config.get_parameter(ctx.guild.id, parameter)
        if result is None:
            return default

        channels = result['value'].split(',')
        if ctx.channel.name in channels:
            return True

        return False
    return commands.check(predicate)


def has_any_channel(*channels):
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        return ctx.channel and ctx.channel.name in channels
    return commands.check(predicate)
