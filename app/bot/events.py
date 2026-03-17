from discord.ext import commands

from .tools.chat import llm


def get_server_name(member) -> str:
    """Return the Discord server (guild) name for the given member."""
    return member.guild.name


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.bot.tree.copy_global_to(guild=guild)
            await self.bot.tree.sync(guild=guild)
        print("OpenBot heartbeat...")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server_name = get_server_name(member)
        await member.send(f"Welcome to {server_name} {member.name}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith("!"):
            reply = llm.response(message.channel.id, message.content)
            await message.channel.send(f"{message.author.mention} {reply}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
