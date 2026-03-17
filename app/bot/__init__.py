import logging

import discord
from discord.ext import commands

from config import settings

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class DiscordBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("bot.music")
        await self.load_extension("bot.events")
        await self.load_extension("bot.context")


bot = DiscordBot(command_prefix="#", intents=intents)


def run():
    token = settings.discord_token.get_secret_value()
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
