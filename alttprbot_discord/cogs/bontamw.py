import discord
from aiohttp import ClientResponseError
from discord.ext import commands

from alttprbot.exceptions import SahasrahBotException
from alttprbot.util import http
from config import Config as c


class BontaMultiworld(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help=('Host a multiworld using an attached multidata file from Bonta\'s multiworld implementation.\n'
              'The multidata file that is attached must be from the multiworld_31 branch or another compatible implementation.\n\n'
              'Returns a "token" that can be used with the $mwmsg command to send commands to the server console.\n\n'
              'Warning: Games are automatically closed after 24 hours.  If you require more time than that, you may re-open the game using $mwresume'
        ),
        brief='Host a multiworld using Bonta\'s multiworld implementation.'
    )
    async def mwhost(self, ctx):
        if not ctx.message.attachments:
            raise SahasrahBotException('Must attach a multidata file.')

        data = {
            'multidata_url': ctx.message.attachments[0].url,
            'admin': ctx.author.id,
            'meta': {
                'channel': None if isinstance(ctx.channel, discord.DMChannel) else ctx.channel.name,
                'guild': ctx.guild.name if ctx.guild else None,
                'multidata_url': ctx.message.attachments[0].url,
                'name': f'{ctx.author.name}#{ctx.author.discriminator}'
            }
        }
        try:
            multiworld = await http.request_json_post(url='http://localhost:5000/game', data=data, returntype='json')
        except ClientResponseError as err:
            raise SahasrahBotException('Unable to generate host using the provided multidata.  Ensure you\'re using the latest version of the mutiworld (<https://github.com/Bonta0/ALttPEntranceRandomizer/tree/multiworld_31>)!') from err

        if not multiworld.get('success', True):
            raise SahasrahBotException(f"Unable to generate host using the provided multidata.  {multiworld.get('description', '')}")

        await ctx.send(
            f"Game Token: {multiworld['token']}\n"
            f"Host: {c.MultiworldHostBase}:{multiworld['port']}"
        )

    @commands.command(
        help=(
            'Sends a command to the multiworld server.\n'
            'The msg should be wrapped in quotes.  For example: $mwmsg abc123 "/kick Synack"\n'
            'Only the creator of the game, or the owner of this bot, may send commands.'
        ),
        brief='Send a command to the multiworld server.'
    )
    async def mwmsg(self, ctx, token, msg):
        result = await http.request_generic(url=f'http://localhost:5000/game/{token}', method='get', returntype='json')

        if not result['admin'] == ctx.author.id:
            raise SahasrahBotException('You must be the creater of the game to send messages to it.')

        data = {
            'msg': msg
        }
        await http.request_json_put(url=f'http://localhost:5000/game/{token}/msg', data=data)

    @commands.command(
        help=(
            'Resume an existing multiworld that was previously closed.\n'
            'Specify the existing token, and port number.\n\n'
            'Multidata and multisave file are removed from the server after 7 days.'
        ),
        brief='Resume a multiworld that was previously closed.'
    )
    async def mwresume(self, ctx, token, port):
        data = {
            'token': token,
            'port': port,
            'admin': ctx.author.id
        }
        multiworld = await http.request_json_post(url='http://localhost:5000/game', data=data, returntype='json')

        await ctx.send(
            f"Game Token: {multiworld['token']}\n"
            f"Host: {c.MultiworldHostBase}:{multiworld['port']}"
        )

def setup(bot):
    bot.add_cog(BontaMultiworld(bot))
