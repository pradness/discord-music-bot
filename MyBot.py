import os
import re
from asyncio import AbstractEventLoop
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
from collections import deque
import asyncio

# Setup token in .env as DISCORD_TOKEN=....
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

SONG_QUEUES = {}
LOOP_STATES = {} # Stores loop state (False, 'song', 'queue')
CURRENT_SONGS = {} # Stores the current song for looping

async def search_ytdlp_async(query, ydl_opts):
    running_loop: AbstractEventLoop = asyncio.get_running_loop()
    return await running_loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

# Setup of intents. Intents are permissions the bot has on the server
intents = discord.Intents.default()
intents.message_content = True

# Bot setup, IDK if this is needed since bot doesn't work on text commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot ready-up code
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

# ----------------------- EMBED FUNCTION -----------------------
color= discord.Color(0x2f222b)
def embed_message(em_type, em_type2, query=None, first_song=None, song_details=None, songs_added_count=0, latency_ms=0):
    match em_type:
        case 0:
            match em_type2:
                case 0:
                    ping_embed = discord.Embed(title="🏓 Pong!", description=f"**Latency:** `{latency_ms}ms`", color=color)
                    ping_embed.set_author(name="<:search:1400019848716750909> What?")
                    return ping_embed
        case 1:
            match em_type2:
                case 1:
                    skip_embed = discord.Embed(description="<:skip:1400020069899305112> Skipped the current song.", color=color)
                    return skip_embed
                case 2:
                    error_embed = discord.Embed(description="<:dino:1400378459401879592> Not playing anything to skip.", color=color)
                    return error_embed
        case 2:
            match em_type2:
                case 1:
                    pause_embed = discord.Embed(description="<:pause:1400019996813426838> Playback paused!", color=color)
                    pause_embed.set_footer(text="Use /resume to continue playback.")
                    return pause_embed
                case 2:
                    warn_embed = discord.Embed(description="<:warn:1400378403932213294> I'm not in a voice channel.", color=color)
                    return warn_embed
                case 3:
                    error_embed = discord.Embed(description="<:dino:1400378459401879592> I'm not playing anything to pause.", color=color)
                    return error_embed
        case 3:
            match em_type2:
                case 1:
                    resume_embed = discord.Embed(description="<:resume:1400019898335363103> Playback resumed!", color=color)
                    return resume_embed
                case 2:
                    error_embed = discord.Embed(description="<:dino:1400378459401879592> I'm not paused right now.", color=color)
                    return error_embed
                case 3:
                    warm_embed = discord.Embed(description="<:warn:1400378403932213294> I'm not in a voice channel.", color= color)
                    return warm_embed
        case 4:
            match em_type2:
                case 1:
                    stop_embed = discord.Embed(description="<:stop:1400022283774590976> Stopped playback and cleared the queue.", color=color)
                    return stop_embed
                case 2:
                    error_embed = discord.Embed(description="<:dino:1400378459401879592> I'm not connected to any voice channel.", color= color)
                    return error_embed
        case 5:
            match em_type2:
                case 1:
                    warn_embed= discord.Embed(description="<:warn:1400378403932213294> You must be in a voice channel to play music.", color=color)
                    return warn_embed
                case 2:
                    error_embed= discord.Embed(description=f"<:404:1400378493681930260> No results found for `{query}`.", color=color)
                    return error_embed
                case 3:
                    added_embed = discord.Embed(
                        description=f"<:play:1400019949019205634> Added to Queue\n###**[{first_song['title']}]({first_song['webpage_url']})**\n**{first_song.get('uploader')}**\n**Duration: {format_duration(first_song.get('duration', 0))}**",
                        color=color
                    )
                    added_embed.set_thumbnail(url=first_song['thumbnail'])
                    added_embed.set_footer(
                        text=f"Requested by {first_song['requester'].display_name}",
                        icon_url=first_song['requester'].display_avatar.url
                    )
                    return added_embed
                case 4:
                    playlist_embed = discord.Embed(
                        description=f"<:play:1400019949019205634> Playlist Added\n### Added **{songs_added_count}** songs to the queue.",
                        color=color
                    )
                    playlist_embed.set_footer(
                        text=f"Requested by {first_song['requester'].display_name}",
                        icon_url=first_song['requester'].display_avatar.url
                    )
                    return playlist_embed
                case 5:
                    error_embed= discord.Embed(description=f"<:404:1400378493681930260> Could not process the link/query: `{query}`.", color=color)
                    return error_embed
        case 6:
            match em_type2:
                case 1:
                    play_embed = discord.Embed(
                        description=f"<:now:1400019778206433290> Now Playing \n## **[{song_details['title']}]({song_details['webpage_url']})**\n  **Duration: {format_duration(song_details.get('duration', 0))}**",
                        color=color,
                        timestamp=discord.utils.utcnow()
                    )
                    play_embed.set_image(url=song_details['thumbnail'])
                    play_embed.set_footer(
                        text=f"Requested by {song_details['requester'].display_name or 'Unknown'}",
                        icon_url=song_details['requester'].display_avatar.url or None
                    )
                    return play_embed
                case 2:
                    now_embed = discord.Embed(
                        description=f"<:now:1400019778206433290> Now Playing \n## **[{song_details['title']}]({song_details['webpage_url']})**\n {song_details['progress_bar']}", # Put the bar in the description
                        color=color
                    )
                    now_embed.set_image(url=song_details['thumbnail'])
                    now_embed.set_footer(
                        text=f"Requested by {song_details['requester'].display_name}",
                        icon_url=song_details['requester'].display_avatar.url
                    )
                    return now_embed
                case 3:
                    error_embed = discord.Embed(description="<:dino:1400378459401879592> Nothing is currently playing.", color=color)
                    return error_embed
        case 7:
            match em_type2:
                case 1: 
                    empty_embed = discord.Embed(
                        description="<:wrong:1400378542805483540> The queue is currently empty.",
                        color=color
                    )
                    return empty_embed
                case 2:
                    removed_embed = discord.Embed(
                        description=f" Removed **{song_details['title']}** from the queue.",
                        color=discord.Color.green()
                    )

                    

# ----------------------- PING COMMAND -----------------------
@bot.tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    embed= embed_message(0, 0, latency_ms=latency_ms)
    await interaction.response.send_message(embed=embed)

# ----------------------- SKIP COMMAND -----------------------
@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        embed = embed_message(1,1)
        await interaction.response.send_message(embed=embed)
    else:
        embed = embed_message(1,2)
        await interaction.response.send_message(embed=embed)

# ----------------------- PAUSE COMMAND -----------------------
@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        embed= embed_message(2,2)
        return await interaction.response.send_message(embed=embed)
    if not voice_client.is_playing():
        embed= embed_message(2,3)
        return await interaction.response.send_message(embed=embed)
    
    voice_client.pause()
    embed = embed_message(2,1)
    await interaction.response.send_message(embed=embed)

# ----------------------- RESUME COMMAND -----------------------
@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        embed = embed_message(3,3)
        return await interaction.response.send_message(embed=embed)
    if not voice_client.is_paused():
        embed = embed_message(3,2)
        return await interaction.response.send_message(embed=embed)
    
    voice_client.resume()
    embed = embed_message(3,1)
    await interaction.response.send_message(embed=embed)

# ----------------------- STOP COMMAND -----------------------
@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        embed = embed_message(4,2)
        return await interaction.followup.send(embed=embed)

    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()
        
    embed = embed_message(4,1)
    await interaction.followup.send(embed=embed)
    await voice_client.disconnect(force=True)

# ----------------------- PLAY COMMAND -----------------------
@bot.tree.command(name="play", description="Play a song, playlist, or add it to the queue.")
@app_commands.describe(query="Search term or a URL from YouTube/Spotify")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    voice_channel = interaction.user.voice.channel if interaction.user.voice else None
    if voice_channel is None:
        embed = embed_message(5, 1)
        await interaction.followup.send(embed=embed)
        return

    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    import re

    if "spotify.com" in query:
        query = f"ytsearch:{query}"
    elif "youtube.com" in query:
        match = re.search(r"v=([a-zA-Z0-9_-]+)", query)
        if match:
            video_id = match.group(1)
            query = f"ytsearch:{video_id}"
    elif "youtu.be" in query:
        query = re.sub(r"https?://youtu\.be/", "", query)
        query = re.sub(r"\?.*", "", query)
        query = f"ytsearch:{query}"
    else:
         query = query

    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": False,
        "default_search": "ytsearch",
    }
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if not tracks:
        embed = embed_message(5, 2, query=query)
        await interaction.followup.send(embed=embed)
        return

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    songs_added_count = 0
    for track in tracks:
        print("--- Found Track ---")
        print(f"Title: {track.get('title')}")
        print(f"Uploader: {track.get('uploader')}")
        print(f"Duration: {track.get('duration')}")
        print("--------------------")
        song_details = {
            "audio_url": track.get("url"),
            "title": track.get("title", "Untitled"),
            "webpage_url": track.get("webpage_url"),
            "uploader": track.get("uploader", "Unknown"),
            "thumbnail": track.get("thumbnail"),
            "requester": interaction.user,
            "duration": track.get("duration"),
            "is_live": track.get('is_live', False)
        }
        if song_details["audio_url"]:
            SONG_QUEUES[guild_id].append(song_details)
            songs_added_count += 1

    if songs_added_count == 1:
        first_song = SONG_QUEUES[guild_id][-1]
        embed= embed_message(5, 3, first_song=first_song)
    elif songs_added_count > 1:
        embed= embed_message(5, 4, songs_added_count=songs_added_count, first_song=SONG_QUEUES[guild_id][-1])
    else:
        embed= embed_message(5, 5, query=query)
        
    await interaction.followup.send(embed=embed)

    if not (voice_client.is_playing() or voice_client.is_paused()):
        await play_next_song(voice_client, guild_id, interaction.channel)

async def play_next_song(voice_client, guild_id, channel):
    loop_mode = LOOP_STATES.get(guild_id, False)
    
    song_to_play = None

    if loop_mode == "song":
        song_to_play = CURRENT_SONGS.get(guild_id)
    elif loop_mode == "queue":
        finished_song = CURRENT_SONGS.get(guild_id)
        if finished_song:
            SONG_QUEUES[guild_id].append(finished_song)
        
        if SONG_QUEUES[guild_id]:
            song_to_play = SONG_QUEUES[guild_id].popleft()
    else:
        if guild_id in SONG_QUEUES and SONG_QUEUES[guild_id]:
            song_to_play = SONG_QUEUES[guild_id].popleft()

    if song_to_play:
        song_to_play['start_time'] = discord.utils.utcnow()
        CURRENT_SONGS[guild_id] = song_to_play
        
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }
        source = discord.FFmpegOpusAudio(song_to_play['audio_url'], **ffmpeg_options)

        def after_play(error):
            if error:
                print(f"Error playing {song_to_play.get('title', 'a song')}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)

        # Create and send the "Playing" embed.
        embed = embed_message(6, 1, song_details=song_to_play)
        await channel.send(embed=embed)

    else:
        CURRENT_SONGS[guild_id] = None
        LOOP_STATES[guild_id] = False
        if voice_client.is_connected():
            await voice_client.disconnect()

# ----------------------- NOW PLAYING COMMAND -----------------------
@bot.tree.command(name="nowplaying", description="Shows details about the currently playing song.")
async def nowplaying(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    current_song = CURRENT_SONGS.get(guild_id)

    if not current_song or not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
        embed= embed_message(6, 3)
        return await interaction.response.send_message(embed=embed)

    if current_song.get('is_live'):
        progress_bar = "Broadcasting Live 🔴"
    else:
        start_time = current_song['start_time']
        elapsed = (discord.utils.utcnow() - start_time).total_seconds()
        duration = current_song['duration']
        
        if elapsed > duration:
            elapsed = duration

        BAR_LENGTH = 14
        position = int(BAR_LENGTH * (elapsed / duration))
        bar = "<:line:1399847396850008234>" * position + "<:current:1399847455859937290>" + "<:line:1399847396850008234>" * (BAR_LENGTH - position)
        
        elapsed_str = format_duration(int(elapsed))
        duration_str = format_duration(duration)
        progress_bar = f"**{elapsed_str}** {bar} **{duration_str}**"
        
    current_song['progress_bar'] = progress_bar
    embed= embed_message(6, 2, song_details=current_song)

    await interaction.response.send_message(embed=embed)

def format_duration(seconds: int):
    """Converts seconds into an MM:SS or HH:MM:SS string."""
    if seconds is None:
        return "N/A"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

# ----------------------- REMOVE COMMAND -----------------------
@bot.tree.command(name="remove", description="Remove a song from the queue by its position.")
@app_commands.describe(position="Position of the song in the queue (1-based index).")
async def remove(interaction: discord.Interaction, position: int):
    guild_id = str(interaction.guild_id)
    if guild_id not in SONG_QUEUES or not SONG_QUEUES[guild_id]:
        embed = discord.Embed(
            description="❌ The queue is currently empty.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    song_queue = SONG_QUEUES[guild_id]
    queue_length = len(song_queue)

    # Validate the user's input position.
    # The user sees a 1-based list, so we check against that.
    if not (1 <= position <= queue_length):
        embed = discord.Embed(
            description=f"❌ Invalid position. Please enter a number between 1 and {queue_length}.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    index_to_remove = position - 1
    song_queue.rotate(-index_to_remove)
    removed_song = song_queue.popleft()
    song_queue.rotate(index_to_remove)
    embed = embed_message(7, 2, song_details=removed_song)
    await interaction.response.send_message(embed=embed)

# ----------------------- LOOP COMMAND -----------------------
@bot.tree.command(name="loop", description="Set the loop mode for the player.")
@app_commands.describe(mode="Choose the loop mode.")
@app_commands.choices(mode=[
    app_commands.Choice(name="Off", value="off"),
    app_commands.Choice(name="Loop Current Song", value="song"),
    app_commands.Choice(name="Loop Entire Queue", value="queue")
])
async def loop(interaction: discord.Interaction, mode: app_commands.Choice[str]):
    guild_id = str(interaction.guild_id)
    user_choice = mode.value

    if user_choice == "song":
        LOOP_STATES[guild_id] = "song"
        embed = discord.Embed(
            description="🔂 Looping for the current song is now **enabled**.",
            color=discord.Color.green()
        )
    elif user_choice == "queue":
        LOOP_STATES[guild_id] = "queue"
        embed = discord.Embed(
            description="🔁 Looping for the entire queue is now **enabled**.",
            color=discord.Color.green()
        )
    else:  # This handles the "off" choice
        LOOP_STATES[guild_id] = False
        embed = discord.Embed(
            description="<:wrong:1400378542805483540> Looping is now **disabled**.",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed)

# ----------------------- SHUFFLE COMMAND -----------------------
@bot.tree.command(name="shuffle", description="Shuffle the current song queue.")
async def shuffle(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    if guild_id not in SONG_QUEUES or not SONG_QUEUES[guild_id]:
        embed = discord.Embed(description="<:dino:1400378459401879592> The queue is empty, nothing to shuffle.", color=color)
        return await interaction.response.send_message(embed=embed)

    import random
    random.shuffle(SONG_QUEUES[guild_id])
    
    embed = discord.Embed(description="🔀 The song queue has been shuffled.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# ----------------------- QUEUE COMMAND -----------------------
@bot.tree.command(name="queue", description="Display the current song queue.")
async def queue(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    current_song = CURRENT_SONGS.get(guild_id)
    song_queue = SONG_QUEUES.get(guild_id, deque())

    if not current_song and not song_queue:
        embed = embed_message(7, 1)
        return await interaction.response.send_message(embed=embed)

    embed = discord.Embed(
        title="<:now:1400019778206433290> Music Queue",
        color=color
    )

    if current_song:
        elapsed = (discord.utils.utcnow() - current_song['start_time']).total_seconds()
        duration = current_song['duration']
        if current_song.get('is_live'):
            progress_display = "🔴 Live"
        else:
            elapsed_str = format_duration(int(elapsed))
            duration_str = format_duration(duration)
            progress_display = f"`{elapsed_str} / {duration_str}`"

        embed.add_field(
            name="Now Playing",
            value=f"**[{current_song['title']}]({current_song['webpage_url']})**\n{progress_display} | Requested by: {current_song['requester'].mention}",
            inline=False
        )

    if song_queue:
        queue_list = ""
        for i, song in enumerate(list(song_queue)[:25]):
            duration_str = format_duration(song.get('duration'))
            line = f"{i+1}. **[{song['title']}]({song['webpage_url']})** {duration_str} | {song['requester'].mention}\n"
            
            if len(queue_list) + len(line) > 1024:
                queue_list += f"\n...and {len(song_queue) - i} more."
                break

            queue_list += line

        embed.add_field(name="Up Next", value=queue_list, inline=False)

    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)