from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from .tools.chat import history, llm


class Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="context_status",
        description="Show how much conversation history is stored for this channel.",
    )
    async def context_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        stats = history.history_stats(interaction.channel_id)

        if stats["total"] == 0:
            await interaction.followup.send("No conversation history for this channel.")
            return

        elapsed = ""
        if stats["last_updated"]:
            delta = datetime.now(timezone.utc) - stats["last_updated"]
            minutes = int(delta.total_seconds() // 60)
            if minutes < 1:
                elapsed = "just now"
            elif minutes < 60:
                elapsed = f"{minutes}m ago"
            else:
                elapsed = f"{minutes // 60}h {minutes % 60}m ago"

        used = stats["last_input_tokens"]
        limit = stats["token_limit"]
        pct = (used / limit * 100) if limit else 0

        lines = [
            "**Channel context**",
            f"Messages: {stats['total']}",
            f"Context window: **{used:,}** / {limit:,} tokens ({pct:.1f}%)",
            f"Session tokens: {stats['total_input_tokens']:,} in / {stats['total_output_tokens']:,} out",
            f"Last updated: {elapsed}",
        ]

        if pct >= 78:
            lines.append(
                f"⚠️ Approaching auto-summarize threshold ({history.AUTO_SUMMARIZE_THRESHOLD:,} tokens)"
            )

        await interaction.followup.send("\n".join(lines))

    @app_commands.command(
        name="context_clear",
        description="Clear all conversation history for this channel.",
    )
    async def context_clear(self, interaction: discord.Interaction):
        await interaction.response.defer()

        stats = history.history_stats(interaction.channel_id)
        history.clear_history(interaction.channel_id)

        if stats["total"] == 0:
            await interaction.followup.send(
                "Nothing to clear — history was already empty."
            )
        else:
            await interaction.followup.send(
                f"Cleared {stats['total']} messages from this channel's context."
            )

    @app_commands.command(
        name="context_summarize",
        description="Summarize the conversation history for this channel and reset context.",
    )
    async def context_summarize(self, interaction: discord.Interaction):
        await interaction.response.defer()

        summary = llm.summarize(interaction.channel_id)

        if summary is None:
            await interaction.followup.send(
                "No conversation history to summarize in this channel."
            )
            return

        await interaction.followup.send(f"**Context summary:**\n{summary}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Context(bot))
