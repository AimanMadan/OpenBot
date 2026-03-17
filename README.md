# OpenBot

A Discord bot with AI-powered chat (via OpenAI) and music playback with a per-server queue.

## Features

- **AI Chat** -- Prefix any message with `!` to get a response powered by OpenAI.
- **Music Playback** -- Search YouTube and stream audio into a voice channel with a full queue system.
  - `/play <query>` -- Search and play a track, or add it to the queue.
  - `/skip` -- Skip to the next track in the queue.
  - `/pause` -- Pause the current track.
  - `/resume` -- Resume a paused track.
  - `/stop` -- Stop playback, clear the queue, and disconnect.
  - `/queue` -- Show the currently playing track and upcoming queue.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- ffmpeg (required for audio playback)
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- An OpenAI API key

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/AimanMadan/OpenBot.git
cd DiscordBot
```

### 2. Create a `.env` file

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Slash commands are automatically synced to every server the bot is in on startup.

### 3. Install dependencies

```bash
uv sync
```

### 4. Install ffmpeg

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (winget)
winget install ffmpeg
```

### 5. Run the bot

```bash
uv run app/main.py
```

## Docker

Build and run with Docker Compose (ffmpeg is included in the image):

```bash
docker compose up -d --build
```

The container reads secrets from `.env` via the `env_file` directive -- nothing is baked into the image.

## Discord Developer Portal Setup

When configuring your bot on the [Developer Portal](https://discord.com/developers/applications):

### OAuth2 Scopes

| Scope | Required for |
|---|---|
| `bot` | Joining servers and responding to events/messages |
| `applications.commands` | Registering slash commands (`/play`, `/skip`, etc.) |

### Bot Permissions

| Permission | Required for |
|---|---|
| Send Messages | Sending text responses and "Now playing" updates |
| Read Message History | Following up on deferred slash command interactions |
| Connect | Joining voice channels |
| Speak | Transmitting audio in voice channels |
| Use Slash Commands | Allowing users to invoke `/play`, `/skip`, etc. |

### Privileged Gateway Intents

Toggle these on in the **Bot** settings page:

| Intent | Required for |
|---|---|
| Message Content | Reading message text for the `!` chat prefix |
| Server Members | Firing `on_member_join` welcome messages |

Generate the invite URL from **OAuth2 > URL Generator** with both scopes and all permissions above, then open it to add the bot to your server.

## Project Structure

```
app/
├── main.py          # Entrypoint (uv run app/main.py)
├── config.py        # Pydantic settings loaded from .env
└── bot/
    ├── __init__.py      # Bot class, intents, logging, run()
    ├── music.py         # Music cog -- slash commands and queue engine
    ├── events.py        # Events cog -- on_ready, on_member_join, on_message
    └── tools/
        ├── ffmpeg.py        # ffmpeg executable lookup and audio source factory
        ├── llm.py           # OpenAI chat integration
        └── musicplayer.py   # yt-dlp search helpers and Track dataclass
```

## License

This project is licensed under the [MIT License](LICENSE).
