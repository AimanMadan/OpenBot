import asyncio
import logging
from collections import deque

import discord
from discord import app_commands
from discord.ext import commands

from .tools import ffmpeg, musicplayer
from .tools.musicplayer import Track


class GuildMusicState:
    __slots__ = ("queue", "text_channel", "now_playing")

    def __init__(self):
        self.queue: deque[Track] = deque()
        self.text_channel: discord.abc.Messageable | None = None
        self.now_playing: Track | None = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._states: dict[int, GuildMusicState] = {}

    def _get_state(self, guild_id: int) -> GuildMusicState:
        state = self._states.get(guild_id)
        if state is None:
            state = GuildMusicState()
            self._states[guild_id] = state
        return state

    # ── Playback engine ────────────────────────────────────────────────

    def _play_next(self, guild: discord.Guild, error: Exception | None = None):
        """after-callback (runs in a non-async thread)."""
        if error:
            logging.error("Playback error in guild %s: %s", guild.id, error)
        asyncio.run_coroutine_threadsafe(self._play_next_async(guild), self.bot.loop)

    async def _play_next_async(self, guild: discord.Guild):
        state = self._get_state(guild.id)
        voice_client: discord.VoiceClient | None = guild.voice_client

        if not voice_client or not voice_client.is_connected():
            state.now_playing = None
            return

        if not state.queue:
            state.now_playing = None
            return

        track = state.queue.popleft()
        state.now_playing = track

        ffmpeg_path = ffmpeg.find_executable()
        if ffmpeg_path is None:
            state.now_playing = None
            if state.text_channel:
                await state.text_channel.send(
                    "`ffmpeg` is not installed/available. Cannot play audio."
                )
            return

        source = ffmpeg.audio_source(track.url, ffmpeg_path)
        voice_client.play(source, after=lambda e: self._play_next(guild, e))

        if state.text_channel:
            await state.text_channel.send(f"Now playing: **{track.title}**")

    # ── Voice helper ───────────────────────────────────────────────────

    async def _ensure_voice(
        self, interaction: discord.Interaction
    ) -> discord.VoiceClient | None:
        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return None

        voice_state = getattr(interaction.user, "voice", None)
        voice_channel = getattr(voice_state, "channel", None)
        if voice_channel is None:
            await interaction.followup.send(
                "Join a voice channel first, then try the command."
            )
            return None

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        return voice_client

    # ── Commands ───────────────────────────────────────────────────────

    @app_commands.command(
        name="play", description="Play a song or add it to the queue."
    )
    @app_commands.describe(song_query="Search query")
    async def play(self, interaction: discord.Interaction, song_query: str):
        await interaction.response.defer()

        voice_client = await self._ensure_voice(interaction)
        if voice_client is None:
            return

        try:
            query = "ytsearch1:" + song_query
            track_info = await musicplayer.search_ytdlp_async(query)
        except Exception:
            logging.exception("yt-dlp search failed")
            await interaction.followup.send("Search failed (yt-dlp error). Check logs.")
            return

        if not track_info:
            await interaction.followup.send("No results found.")
            return

        audio_url = track_info.get("url")
        title = track_info.get("title", "Untitled")
        if not audio_url:
            await interaction.followup.send("Got a result but no playable audio URL.")
            return

        track = Track(
            title=title,
            url=audio_url,
            requested_by=interaction.user.display_name,
        )

        state = self._get_state(interaction.guild.id)
        state.text_channel = interaction.channel
        state.queue.append(track)

        if voice_client.is_playing() or voice_client.is_paused():
            await interaction.followup.send(
                f"Added to queue (#{len(state.queue)}): **{title}**"
            )
        else:
            await interaction.followup.send(f"Searching... found **{title}**")
            await self._play_next_async(interaction.guild)

    @app_commands.command(name="skip", description="Skip the current track.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return

        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
            await interaction.followup.send("Nothing is playing right now.")
            return

        voice_client.stop()
        await interaction.followup.send("Skipped.")

    @app_commands.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return

        state = self._get_state(interaction.guild.id)
        state.queue.clear()
        state.now_playing = None

        voice_client = interaction.guild.voice_client
        if voice_client is not None:
            voice_client.stop()
            await voice_client.disconnect()

        await interaction.followup.send("Stopped and cleared the queue.")

    @app_commands.command(name="pause", description="Pause the current track.")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return

        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
            await interaction.followup.send("Nothing is playing right now.")
            return

        voice_client.pause()
        await interaction.followup.send("Paused.")

    @app_commands.command(name="resume", description="Resume playback.")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return

        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_paused():
            await interaction.followup.send("Nothing is paused right now.")
            return

        voice_client.resume()
        await interaction.followup.send("Resumed.")

    @app_commands.command(name="queue", description="Show the current music queue.")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "This command can only be used in a server."
            )
            return

        state = self._get_state(interaction.guild.id)

        lines: list[str] = []
        if state.now_playing:
            lines.append(f"**Now playing:** {state.now_playing.title}")

        if state.queue:
            lines.append("")
            for i, track in enumerate(state.queue, start=1):
                lines.append(
                    f"`{i}.` {track.title}  —  requested by {track.requested_by}"
                )
        elif not state.now_playing:
            lines.append("The queue is empty.")

        await interaction.followup.send("\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
