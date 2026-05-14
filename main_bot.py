import discord
from discord.ext import commands
import os
import asyncio
import json
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = 1040946853321117696
MAIN_GUILD_ID = 1503125428875825232 
DATABASE_FILE = 'bot_data.json'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# --- DATABASE ---
def get_db():
    if not os.path.exists(DATABASE_FILE): return {}
    with open(DATABASE_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DATABASE_FILE, 'w') as f: json.dump(data, f, indent=4)

def get_guild_data(guild_id):
    db = get_db(); gid = str(guild_id)
    if gid not in db: db[gid] = {'welcome_ch': None, 'goodbye_ch': None, 'afk_ch': None}; save_db(db)
    return db[gid]

def set_guild_data(guild_id, key, val):
    db = get_db(); gid = str(guild_id); d = get_guild_data(guild_id)
    db[gid][key] = val; save_db(db)

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"[+] Bot AFK Online: {bot.user}")
    # Auto-reconnect ke channel AFK terakhir jika ada
    db = get_db()
    for gid, data in db.items():
        if isinstance(data, dict): # <--- PASTIKAN DATANYA BENERAN PETA (DICT)
            ch_id = data.get('afk_ch')
            if ch_id:
                channel = bot.get_channel(ch_id)
                if channel:
                    try: await channel.connect()
                    except: pass

@bot.event
async def on_member_join(member):
    d = get_guild_data(member.guild.id)
    if d.get('welcome_ch'):
        ch = bot.get_channel(d['welcome_ch'])
        if ch:
            emb = discord.Embed(title="WELCOME!", description=f"Halo {member.mention}, selamat datang di **{member.guild.name}**!", color=discord.Color.green())
            if member.avatar: emb.set_thumbnail(url=member.avatar.url)
            await ch.send(embed=emb)

@bot.event
async def on_member_remove(member):
    d = get_guild_data(member.guild.id)
    if d.get('goodbye_ch'):
        ch = bot.get_channel(d['goodbye_ch'])
        if ch: await ch.send(f"👋 **{member.name}** baru aja keluar dari server.")

# --- AFK VOICE FEATURES ---
@bot.command()
async def join(ctx):
    """Bot masuk ke Voice Channel dan AFK selamanya"""
    if not ctx.author.voice: return await ctx.send("⚠️ Masuk ke Voice Channel dulu sayang!")
    
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    
    set_guild_data(ctx.guild.id, 'afk_ch', channel.id)
    await ctx.send(f"✅ **BMMC AFK Mode ON!** Aku bakal jagain channel `{channel.name}` 24 jam buat kamu. 🥀🫡")

@bot.command()
async def leave(ctx):
    """Bot keluar dari Voice Channel"""
    if ctx.voice_client:
        set_guild_data(ctx.guild.id, 'afk_ch', None)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 AFK Mode OFF. Aku pamit dulu ya!")
    else:
        await ctx.send("⚠️ Aku lagi nggak di Voice Channel mana pun kok.")

# --- PERSISTENT ROLE SYSTEM (REACTION LOGIC) ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    db = get_db()
    for gid, data in db.items():
        logs = data.get('role_requests', {})
        if str(payload.message_id) in logs:
            req = logs[str(payload.message_id)]
            guild = bot.get_guild(payload.guild_id)
            if not guild: continue
            member = await guild.fetch_member(payload.user_id)
            if not member.guild_permissions.administrator: return # Cuma admin yang bisa approve

            user_id = req['user_id']
            role_id = req['role_id']
            target_member = await guild.fetch_member(user_id)
            role = guild.get_role(role_id)

            if str(payload.emoji) == "✅":
                await target_member.add_roles(role)
                channel = bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.edit(content=f"✅ **APPROVED** by {member.mention} for <@{user_id}>", view=None)
                await msg.clear_reactions()
            elif str(payload.emoji) == "❌":
                channel = bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.edit(content=f"❌ **REJECTED** by {member.mention}", view=None)
                await msg.clear_reactions()

# --- SETUP COMMANDS ---
@bot.command()
async def setupwelcome(ctx):
    await ctx.message.delete(); set_guild_data(ctx.guild.id, 'welcome_ch', ctx.channel.id); await ctx.send("✅ Welcome set!", delete_after=3)

@bot.command()
async def setupgoodbye(ctx):
    await ctx.message.delete(); set_guild_data(ctx.guild.id, 'goodbye_ch', ctx.channel.id); await ctx.send("✅ Goodbye set!", delete_after=3)

@bot.command()
async def setrole(ctx):
    if ctx.guild.id != MAIN_GUILD_ID: return await ctx.send("⚠️ Fitur ini eksklusif buat Server Utama BMMC!")
    await ctx.message.delete()
    
    class RoleButton(discord.ui.Button):
        def __init__(self, label, role_id):
            super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=f"role_{role_id}")
            self.role_id = role_id

        async def callback(self, interaction):
            role = interaction.guild.get_role(self.role_id)
            log_ch = bot.get_channel(1504426382921302017) # ROLE_LOG_CH_ID
            msg = await log_ch.send(f"⏳ **Request Role:** {interaction.user.mention} minta role **{role.name}**")
            await msg.add_reaction("✅"); await msg.add_reaction("❌")
            
            # Simpan log ke DB
            db = get_db(); gid = str(interaction.guild.id)
            if 'role_requests' not in db[gid]: db[gid]['role_requests'] = {}
            db[gid]['role_requests'][str(msg.id)] = {'user_id': interaction.user.id, 'role_id': self.role_id}
            save_db(db)
            
            await interaction.response.send_message("⏳ Request kamu udah dikirim ke Admin. Sabar ya!", ephemeral=True)

    view = discord.ui.View(timeout=None)
    roles = [
        ("MEMBER BMMC", 1504412211995476020),
        ("GIRL BMMC", 1504412351233654815),
        ("PARTNER BMMC", 1504412467365675039)
    ]
    for label, rid in roles: view.add_item(RoleButton(label, rid))
    
    emb = discord.Embed(title="🎭 AMBIL ROLE KAMU 🎭", description="Klik tombol untuk request role.", color=discord.Color.blue())
    await ctx.send(embed=emb, view=view)

bot.run(TOKEN)
