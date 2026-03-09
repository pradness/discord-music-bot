<picture align="center">
  <img alt="μsic Logo" src="bin/banner.png">
</picture>

μsic is a Discord music bot that plays audio from YouTube and supports Spotify links via search.

## Features

- Slash commands (e.g. `/play`, `/skip`, `/pause`, `/resume`, `/queue`, `/loop`, `/shuffle`)
- Queue system with loop modes
- YouTube + Spotify-link support (Spotify links are resolved through search)
- Voice playback with Discord E2EE/DAVE support

## Prerequisites

Before running the bot, install:

- Python 3.10 (recommended)
- FFmpeg (required for audio playback)
- A Discord bot token

## 1) Clone the repository

```powershell
git clone https://github.com/<your-username>/discord-music-bot.git
cd discord-music-bot
```

## 2) Create and activate a virtual environment (Windows PowerShell)

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If `py -3.10` is not available, use a direct Python 3.10 path:

```powershell
C:\Path\To\Python310\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3) Install dependencies

```powershell
pip install -r requirements.txt
```

## 4) Configure Discord token

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_bot_token_here
```

## 5) Set up the bot in Discord Developer Portal

1. Go to https://discord.com/developers/applications
2. Create a new application and add a **Bot**.
3. Copy the bot token and put it in `.env`.
4. Under **Bot > Privileged Gateway Intents**, enable:
	 - `MESSAGE CONTENT INTENT`
5. Under **OAuth2 > URL Generator**:
	 - Scopes: `bot`, `applications.commands`
	 - Bot Permissions: at least `Connect`, `Speak`, `Send Messages`, `Use Slash Commands`
6. Use the generated URL to invite the bot to your server.

## 6) Configure FFmpeg

The bot uses FFmpeg through `discord.FFmpegOpusAudio`, so `ffmpeg.exe` must be accessible.

Options:

- Install FFmpeg system-wide and add it to `PATH`, or
- Use the bundled binary in `bin/ffmpeg` and add that folder to `PATH` in your terminal session.

Temporary (PowerShell, current terminal only):

```powershell
$env:Path = "$PWD\bin\ffmpeg;$env:Path"
```

Verify:

```powershell
ffmpeg -version
```

## 7) Run the bot

```powershell
python MyBot.py
```

You should see:

```text
<bot_name>#<discriminator> is online!
```

## Railway Deployment (with FFmpeg)

This repo includes `nixpacks.toml` so Railway installs FFmpeg during build.

### Build and Start

- Build command: `pip install -r requirements.txt`
- Start command: `python MyBot.py`

### Required Railway Variables

- `DISCORD_TOKEN` = your bot token

### Notes

- `runtime.txt` is set to Python 3.10 for better voice stability.
- If you changed build settings earlier, trigger a fresh deploy after pushing latest files.

## Common Issues

- **`PyNaCl library needed in order to use voice`**
	- Run: `pip install -r requirements.txt`

- **Voice close code `4017`**
	- This is related to E2EE/DAVE voice requirements.
	- Ensure dependencies are installed from `requirements.txt` (includes `davey`).
	- Restart the bot after dependency installation.

- **`Timed out connecting to voice` (common on Replit)**
	- This usually means the host cannot complete Discord voice UDP transport.
	- Replit often works for text/slash bots, but voice bots may fail due to networking limits.
	- Try a host with reliable outbound UDP support (VPS, Railway, Render, Fly.io, etc.).
	- If you must test on Replit, keep expectations low for voice playback reliability.

- **`ffmpeg` not found / no audio**
	- Confirm `ffmpeg -version` works in the same terminal where you run the bot.

## Notes

- Keep your token secret; never commit `.env` to git.
- If slash commands do not appear immediately, wait a moment and restart the bot.

