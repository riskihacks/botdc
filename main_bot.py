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

# --- PERSISTENT ROLE VIEW SYSTEM ---
class RoleButton(discord.ui.Button):
    def __init__(self, label, role_name, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if not role: return await interaction.response.send_message(f"❌ Role **{self.role_name}** nggak ketemu!", ephemeral=True)
        
        log_ch = bot.get_channel(1504426382921302017) # ROLE_LOG_CH_ID
        if not log_ch: return await interaction.response.send_message("❌ Channel log admin nggak ketemu!", ephemeral=True)
        
        msg = await log_ch.send(f"⏳ **Request Role:** {interaction.user.mention} minta role **{role.name}**")
        await msg.add_reaction("✅"); await msg.add_reaction("❌")
        
        # Simpan log ke DB
        db = get_db(); gid = str(interaction.guild.id)
        if 'role_requests' not in db[gid]: db[gid]['role_requests'] = {}
        db[gid]['role_requests'][str(msg.id)] = {'user_id': interaction.user.id, 'role_id': role.id}
        save_db(db)
        
        await interaction.response.send_message(f"✅ Request **{role.name}** dikirim ke Owner!", ephemeral=True)

class PersistentRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleButton("BM GLORIX", "BM GLORIX", discord.ButtonStyle.danger, "btn_bm_glorix"))
        self.add_item(RoleButton("BM INDOPRIDE", "BM INDOPRIDE", discord.ButtonStyle.primary, "btn_bm_indopride"))
        self.add_item(RoleButton("BM KNRP", "BM KNRP", discord.ButtonStyle.success, "btn_bm_knrp"))
        self.add_item(RoleButton("TAMU BM", "TAMU BM", discord.ButtonStyle.secondary, "btn_tamu_bm"))

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"[+] Bot AFK & Role Online: {bot.user}")
    
    # 1. DAFTARKAN PERSISTENT VIEW (BIAR TOMBOL JALAN TERUS)
    bot.add_view(PersistentRoleView())
    
    # 2. Auto-reconnect ke channel AFK
    db = get_db()
    for gid, data in db.items():
        if isinstance(data, dict):
            ch_id = data.get('afk_ch')
            if ch_id:
                channel = bot.get_channel(ch_id)
                if channel and not any(v.channel == channel for v in bot.voice_clients):
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
    if not ctx.author.voice: return await ctx.send("⚠️ Masuk ke Voice Channel dulu sayang!")
    channel = ctx.author.voice.channel
    if ctx.voice_client: await ctx.voice_client.move_to(channel)
    else: await channel.connect()
    set_guild_data(ctx.guild.id, 'afk_ch', channel.id)
    await ctx.send(f"✅ **BMMC AFK Mode ON!** Aku bakal jagain channel `{channel.name}` 24 jam. 🥀🫡")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        set_guild_data(ctx.guild.id, 'afk_ch', None)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 AFK Mode OFF. Aku pamit dulu ya!")
    else: await ctx.send("⚠️ Aku lagi nggak di Voice Channel.")

# --- PERSISTENT ROLE SYSTEM (REACTION LOGIC) ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    db = get_db()
    for gid, data in db.items():
        if not isinstance(data, dict): continue
        logs = data.get('role_requests', {})
        if str(payload.message_id) in logs:
            req = logs[str(payload.message_id)]
            guild = bot.get_guild(payload.guild_id)
            if not guild: continue
            member = await guild.fetch_member(payload.user_id)
            if not member.guild_permissions.administrator: return 

            user_id = req['user_id']
            role_id = req['role_id']
            try:
                target_member = await guild.fetch_member(user_id)
                role = guild.get_role(role_id)
                if str(payload.emoji) == "✅":
                    await target_member.add_roles(role)
                    msg = await (bot.get_channel(payload.channel_id)).fetch_message(payload.message_id)
                    await msg.edit(content=f"✅ **APPROVED** by {member.mention} for <@{user_id}>")
                    await msg.clear_reactions()
                elif str(payload.emoji) == "❌":
                    msg = await (bot.get_channel(payload.channel_id)).fetch_message(payload.message_id)
                    await msg.edit(content=f"❌ **REJECTED** by {member.mention} for <@{user_id}>")
                    await msg.clear_reactions()
            except: pass

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
    emb = discord.Embed(title="🎭 AMBIL ROLE KAMU 🎭", description="Klik tombol di bawah untuk request role.", color=discord.Color.blue())
    await ctx.send(embed=emb, view=PersistentRoleView())

bot.run(TOKEN)
