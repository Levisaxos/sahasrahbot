import discord
from discord.ext import commands
from quart import abort, jsonify, request

from alttprbot.api.app import app
from config import Config as c

from ..database import config, srlnick
from ..util import srl

DISCORDBOT = None


class Nickname(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global DISCORDBOT
        DISCORDBOT = self.bot

    @commands.command(
        help="Register your SRL nick with SahasrahBot."
    )
    async def srl(self, ctx, nick):
        await srlnick.insert_srl_nick(ctx.author.id, nick)

    @commands.command(
        help="Register your Twitch name with SahasrahBot."
    )
    async def twitch(self, ctx, twitch):
        await srlnick.insert_twitch_name(ctx.author.id, twitch)

    @commands.command(
        help="List the nicknames registered with SahasrahBot."
    )
    async def getnick(self, ctx):
        nick = await srlnick.get_nicknames(ctx.author.id)
        if nick:
            await ctx.send(
                (f"Your currently registered nickname for SRL is `{nick[0]['srl_nick']}`\n"
                 f"Your currently registered nickname for Twitch is `{nick[0]['twitch_name']}`")
            )
        else:
            await ctx.send("You currently do not have any nicknames registered with this bot.  Use the command `$srl yournick` and `$twitch yournick` to do that!")


@app.route('/api/srl/finish', methods=['POST'])
async def finish():
    if request.method == 'POST':
        data = await request.get_json()
        if 'auth' in data and data['auth'] == c.InternalApiToken:
            nickmappings = await srlnick.get_discord_id(data['nick'])
            configguilds = await config.get_all_parameters_by_name('CurrentlyRacingRoleId')
            for configguild in configguilds:
                guild = discord.utils.get(
                    DISCORDBOT.guilds, id=configguild['guild_id'])
                role = discord.utils.get(
                    guild.roles, name=configguild['value'])
                if nickmappings:
                    for nickmapping in nickmappings:
                        user = discord.utils.get(
                            guild.members, id=nickmapping['discord_user_id'])
                        try:
                            await user.remove_roles(role)
                        except discord.HTTPException:
                            continue
        else:
            abort(401)
        return jsonify({})
    else:
        abort(400)


@app.route('/api/srl/start', methods=['POST'])
async def start():
    if request.method == 'POST':
        data = await request.get_json()
        if 'auth' in data and data['auth'] == c.InternalApiToken:
            race = await srl.get_race(data['raceid'])
            configguilds = await config.get_all_parameters_by_name('CurrentlyRacingRoleId')
            for configguild in configguilds:
                guild = discord.utils.get(
                    DISCORDBOT.guilds, id=configguild['guild_id'])
                role = discord.utils.get(
                    guild.roles, name=configguild['value'])
                for entrant in race['entrants']:
                    nickmappings = await srlnick.get_discord_id(entrant)
                    if nickmappings:
                        for nickmapping in nickmappings:
                            user = discord.utils.get(
                                guild.members, id=nickmapping['discord_user_id'])
                            try:
                                await user.add_roles(role)
                            except discord.HTTPException:
                                pass
        else:
            abort(401)
        return jsonify({})
    else:
        abort(400)


def setup(bot):
    bot.add_cog(Nickname(bot))
