import discord
from discord.ext import commands
import yt_dlp
import asyncio
import json
import os
import re
from static_ffmpeg import add_paths
from dotenv import load_dotenv
from youtube_search import YoutubeSearch

# --- SETUP ---
load_dotenv()
add_paths()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = 1040946853321117696
MAIN_GUILD_ID = 1503125428875825232 # Server Utama BMMC
ROLE_LOG_CH_ID = 1504426382921302017
DATABASE_FILE = 'bot_data.json'

def load_data():
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_data(data):
    with open(DATABASE_FILE, 'w') as f: json.dump(data, f)

def get_guild_data(guild_id):
    data = load_data(); gid = str(guild_id)
    if gid not in data: data[gid] = {"welcome_ch": None, "goodbye_ch": None, "music_ch": None}; save_data(data)
    return data[gid]

def set_guild_data(guild_id, key, value):
    data = load_data(); gid = str(guild_id)
    if gid not in data: data[gid] = {"welcome_ch": None, "goodbye_ch": None, "music_ch": None}
    data[gid][key] = value; save_data(data)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# --- MUSIC ---
ytdl_format = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': 'cookies.txt',
    'cachedir': False, # <--- BIAR NGGAK NYIMPAN SAMPAH
    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'extractor_args': {'youtube': {'player_client': ['web_embedded', 'ios']}}
}
ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(ytdl_format)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume); self.data = data; self.title = data.get('title')
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data: data = data['entries'][0]
        return cls(discord.FFmpegPCMAudio(data['url'] if stream else ytdl.prepare_filename(data), **ffmpeg_opts), data=data)

queues = {}
def check_queue(ctx):
    gid = ctx.guild.id
    if gid in queues and queues[gid]:
        s = queues[gid].pop(0)
        async def play_next():
            try:
                p = await YTDLSource.from_url(s['url'], loop=bot.loop, stream=True)
                ctx.voice_client.play(p, after=lambda e: check_queue(ctx))
                await ctx.send(f"🎶 **Now Playing:** `{p.title}`")
            except: check_queue(ctx)
        bot.loop.create_task(play_next())

class MusicSelect(discord.ui.Select):
    def __init__(self, options): super().__init__(placeholder="Pilih lagu kamu, Zero...", options=options)
    async def callback(self, interaction):
        await interaction.response.defer()
        if interaction.guild_id not in queues: queues[interaction.guild_id] = []
        queues[interaction.guild_id].append({'url': self.values[0]})
        ctx = await bot.get_context(interaction.message)
        if not interaction.guild.voice_client: await interaction.user.voice.channel.connect()
        if not interaction.guild.voice_client.is_playing(): check_queue(ctx); await interaction.followup.send("✅ Memulai musik!", ephemeral=True)
        else: await interaction.followup.send("➕ Masuk antrian!", ephemeral=True)

class MusicSearchView(discord.ui.View):
    def __init__(self, options): super().__init__(timeout=30); self.add_item(MusicSelect(options))

# --- ROLE VIEW (EXCLUSIVE) ---
class RoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def handle_request(self, interaction, role_name):
        if interaction.guild_id != MAIN_GUILD_ID:
            return await interaction.response.send_message("⚠️ Fitur ini eksklusif buat Server Utama BMMC!", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        log_ch = bot.get_channel(ROLE_LOG_CH_ID)
        if log_ch:
            def is_old(m): return m.author.id == bot.user.id and (interaction.user.mention in m.content or (m.embeds and interaction.user.mention in str(m.embeds[0].to_dict())))
            try: await log_ch.purge(limit=5, check=is_old)
            except: pass
            emb = discord.Embed(title="🎫 NEW ROLE REQUEST", color=discord.Color.orange(), description=f"Klik ⏳ untuk approve role **{role_name}**")
            emb.add_field(name="User", value=interaction.user.mention); emb.add_field(name="Role", value=role_name)
            msg = await log_ch.send(content=f"<@{OWNER_ID}>", embed=emb); await msg.add_reaction("⏳")
            await interaction.followup.send(f"✅ Request **{role_name}** dikirim!", ephemeral=True)

    @discord.ui.button(label="BM GLORIX", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="role_glorix")
    async def glorix(self, i, b): await self.handle_request(i, "BM GLORIX")
    @discord.ui.button(label="BM INDOPRIDE", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="role_indopride")
    async def indopride(self, i, b): await self.handle_request(i, "BM INDOPRIDE")
    @discord.ui.button(label="BM KNRP", style=discord.ButtonStyle.success, emoji="🟢", custom_id="role_knrp")
    async def knrp(self, i, b): await self.handle_request(i, "BM KNRP")
    @discord.ui.button(label="TAMU BM", style=discord.ButtonStyle.secondary, emoji="🟡", custom_id="role_tamu")
    async def tamu(self, i, b): await self.handle_request(i, "TAMU BM")

# --- AUTO APPROVE (EXCLUSIVE) ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != OWNER_ID or str(payload.emoji) != "⏳" or payload.guild_id != MAIN_GUILD_ID: return
    channel = bot.get_channel(payload.channel_id); message = await channel.fetch_message(payload.message_id)
    if message.author.id != bot.user.id or not message.embeds: return
    embed = message.embeds[0]
    if "NEW ROLE REQUEST" not in str(embed.title): return
    try:
        uid = int(re.search(r'\d+', embed.fields[0].value).group()); rn = embed.fields[1].value
        guild = bot.get_guild(payload.guild_id); member = guild.get_member(uid); role = discord.utils.get(guild.roles, name=rn)
        if member and role:
            await member.add_roles(role); await message.clear_reactions(); await message.add_reaction("✅")
            new_emb = embed.copy(); new_emb.title = "✅ ROLE APPROVED"; new_emb.color = discord.Color.green(); new_emb.description = f"Role **{rn}** diberikan oleh Owner."
            await message.edit(embed=new_emb); await channel.send(f"✅ **{member.name}** dapet role **{rn}**!", delete_after=5)
    except Exception as e: print(f"Error: {e}")

@bot.event
async def on_ready(): bot.add_view(RoleView()); print(f'\n[+] Bot Online: {bot.user.name}')

@bot.event
async def on_member_join(m):
    d = get_guild_data(m.guild.id)
    if d.get('welcome_ch'):
        ch = bot.get_channel(d['welcome_ch'])
        if ch:
            emb = discord.Embed(title="✨ WELCOME ✨", description=f"Halo {m.mention}! Selamat datang di {m.guild.name}! 🥀🔥", color=discord.Color.red())
            emb.set_thumbnail(url=m.display_avatar.url); await ch.send(embed=emb)

# --- COMMANDS ---
@bot.command(aliases=['setwelcome'])
async def setupwelcome(ctx):
    await ctx.message.delete(); set_guild_data(ctx.guild.id, 'welcome_ch', ctx.channel.id); await ctx.send("✅ Welcome set!", delete_after=3)

@bot.command(aliases=['setgoodbye'])
async def setupgoodbye(ctx):
    await ctx.message.delete(); set_guild_data(ctx.guild.id, 'goodbye_ch', ctx.channel.id); await ctx.send("✅ Goodbye set!", delete_after=3)

@bot.command(aliases=['setmusic'])
async def setupmusic(ctx):
    await ctx.message.delete(); set_guild_data(ctx.guild.id, 'music_ch', ctx.channel.id); await ctx.send("✅ Music channel set!", delete_after=3)

@bot.command()
async def setrole(ctx):
    if ctx.guild.id != MAIN_GUILD_ID: return await ctx.send("⚠️ Fitur ini eksklusif buat Server Utama BMMC!")
    await ctx.message.delete(); emb = discord.Embed(title="🎭 AMBIL ROLE KAMU 🎭", description="Klik tombol untuk request role.", color=discord.Color.blue())
    await ctx.send(embed=emb, view=RoleView())

@bot.command()
async def play(ctx, *, query):
    d = get_guild_data(ctx.guild.id)
    if d.get('music_ch') and ctx.channel.id != d['music_ch']: return await ctx.send(f"⚠️ Cuma di <#{d['music_ch']}>!", delete_after=5)
    if not ctx.author.voice: return await ctx.send("⚠️ Masuk Voice dulu!")
    
    await ctx.send(f"🔍 Mencari `{query}`...", delete_after=5)
    try:
        # --- CARA CARI BARU (YOUTUBE-SEARCH) ---
        results = YoutubeSearch(query, max_results=10).to_dict()
        if not results: return await ctx.send("❌ Lagu nggak ketemu.")
        
        opts = [discord.SelectOption(label=v['title'][:100], value="https://www.youtube.com" + v['url_suffix']) for v in results]
        await ctx.send("🎶 **Pilih lagu:**", view=MusicSearchView(opts), delete_after=30)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing(): ctx.voice_client.stop(); await ctx.send("⏭️ Lagu di-skip!")
    else: await ctx.send("⚠️ Ga ada lagu yang lagi muter.")

bot.run(TOKEN)
