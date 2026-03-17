import asyncio
from dataclasses import dataclass

import yt_dlp

ydl_config = {
    "format": "bestaudio[abr<=96]/bestaudio",
    "noplaylist": True,
    "youtube_include_dash_manifest": False,
    "youtube_include_hls_manifest": False,
}


@dataclass
class Track:
    title: str
    url: str
    requested_by: str


async def search_ytdlp_async(query: str) -> dict | None:
    """Search yt-dlp and return a single track dict, or None."""
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, lambda: _extract(query))
    return _resolve_single_track(results)


def _extract(query: str) -> dict:
    with yt_dlp.YoutubeDL(ydl_config) as ydl:
        return ydl.extract_info(query, download=False)


def _resolve_single_track(results: dict | None) -> dict | None:
    if results is None:
        return None
    entries = results.get("entries")
    if entries:
        return entries[0]
    if results.get("url"):
        return results
    return None
