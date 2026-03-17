import shutil

import discord

FFMPEG_CONFIG = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


def find_executable() -> str | None:
    """Return the path to ffmpeg, or None if not installed."""
    return shutil.which("ffmpeg")


def audio_source(url: str, executable: str) -> discord.FFmpegPCMAudio:
    """Create an FFmpegPCMAudio source for the given stream URL."""
    return discord.FFmpegPCMAudio(url, executable=executable, **FFMPEG_CONFIG)
