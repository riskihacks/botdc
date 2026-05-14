import discord
from discord.ext import commands
import asyncio

# --- DATA DARI ZERO ---
TOKEN = 'MTUwNDQxNjUyMDQwOTcxMDY4Nw.Gy9q-H.hWMsOm9TlTdV7SqvDpDIMIIQDwr8cJLAWgaDbs'
GUILD_ID = 1503125428875825232

def to_bold(text):
    bold_map = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽ｑ𝗿𝘀𝘁ｕ𝘃ｗｘ𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    )
    return text.translate(bold_map)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'\n[+] Terhubung sebagai: {bot.user.name}')
    guild = bot.get_guild(GUILD_ID)
    
    if not guild:
        print(f'[!] ERROR: Guild ID {GUILD_ID} tidak ditemukan.')
        await bot.close()
        return

    print(f'[+] Memulai setup otomatis (ULTIMATE HISTORY LOCK) di: {guild.name}')
    print('--------------------------------------------------')

    async def get_or_create_role(name, perms, color):
        role = discord.utils.get(guild.roles, name=name)
        if not role:
            role = await guild.create_role(name=name, permissions=perms, color=color, hoist=True)
            print(f'    [+] Role {name} dibuat.')
        else:
            await role.edit(permissions=perms) # Paksa update permission global
            print(f'    [-] Role {name} sudah ada, update permission global.')
        return role

    async def get_or_create_category(name, overwrites):
        cat = discord.utils.get(guild.categories, name=name)
        if not cat:
            cat = await guild.create_category(name=name, overwrites=overwrites)
            print(f'    [+] Category {name} dibuat.')
        else:
            await cat.edit(overwrites=overwrites)
            print(f'    [-] Category {name} sudah ada, update permission.')
        return cat

    async def get_or_create_text(name, cat, overwrites=None):
        channel = discord.utils.get(cat.text_channels, name=name)
        if not channel:
            await guild.create_text_channel(name, category=cat, overwrites=overwrites if overwrites else {})
            print(f'        > Channel {name} dibuat.')
        else:
            if overwrites:
                for target, perm in overwrites.items():
                    await channel.set_permissions(target, overwrite=perm)
                print(f'        > Channel {name} sudah ada, update permission.')
            else:
                print(f'        > Channel {name} sudah ada, skip.')

    async def get_or_create_voice(name, cat, overwrites=None):
        channel = discord.utils.get(cat.voice_channels, name=name)
        if not channel:
            await guild.create_voice_channel(name, category=cat, overwrites=overwrites if overwrites else {})
            print(f'        > Voice {name} dibuat.')
        else:
            if overwrites:
                for target, perm in overwrites.items():
                    await channel.set_permissions(target, overwrite=perm)
                print(f'        > Voice {name} sudah ada, update permission.')
            else:
                print(f'        > Voice {name} sudah ada, skip.')

    try:
        # 1. UPDATE @EVERYONE GLOBAL PERMS (Mastiin Read History nyala buat semua)
        everyone = guild.default_role
        everyone_perms = everyone.permissions
        everyone_perms.update(read_message_history=True)
        await everyone.edit(permissions=everyone_perms)
        print('[*] @everyone global permission updated (Read History ON)')

        # 2. ROLES (BM, PRESS, TAMU)
        bm_perms = discord.Permissions(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, add_reactions=True, embed_links=True, mention_everyone=True)
        press_perms = discord.Permissions(administrator=True)
        tamu_perms = discord.Permissions(view_channel=True, send_messages=True, read_message_history=True, add_reactions=True)

        roles_bm = {}
        for n in ["BM GLORIX", "BM INDOPRIDE", "BM KNRP"]:
            roles_bm[n] = await get_or_create_role(n, bm_perms, discord.Color.red())

        roles_press = {}
        for n in ["PRESS GLORIX", "PRESS INDOPRIDE", "PRESS KNRP"]:
            roles_press[n] = await get_or_create_role(n, press_perms, discord.Color.dark_purple())

        role_tamu = await get_or_create_role("TAMU BM", tamu_perms, discord.Color.gold())

        # 3. CATEGORIES & CHANNELS
        
        # ALIANZI
        ov_alianzi = {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True, add_reactions=True),
            role_tamu: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
        }
        cat_alianzi = await get_or_create_category(f"📂 {to_bold('ALIANZI BLOODY MARY')}", ov_alianzi)
        await get_or_create_text(f"👋┃{to_bold('welcome')}", cat_alianzi)
        await get_or_create_text(f"🚪┃{to_bold('goodbye')}", cat_alianzi)
        await get_or_create_text(f"🎭┃{to_bold('req-role')}", cat_alianzi)
        await get_or_create_text(f"🎫┃{to_bold('role-request')}", cat_alianzi)

        # TAMU BM
        ov_tamu = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            role_tamu: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            **{r: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True) for r in roles_bm.values()}
        }
        cat_tamu = await get_or_create_category(f"🤝 {to_bold('TAMU BM')}", ov_tamu)
        await get_or_create_text(f"💬┃{to_bold('chat-tamu')}", cat_tamu)
        await get_or_create_voice(f"🔊┃{to_bold('voice-tamu')}", cat_tamu)

        # BM PENGHANCUR
        ov_bm = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            role_tamu: discord.PermissionOverwrite(view_channel=False),
            **{r: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True) for r in roles_bm.values()}
        }
        cat_penghancur = await get_or_create_category(f"💥 {to_bold('BM PENGHANCUR')}", ov_bm)
        
        ov_ann = ov_bm.copy()
        for r in roles_bm.values(): ov_ann[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True, add_reactions=True)
        await get_or_create_text(f"📢┃{to_bold('pengumuman')}", cat_penghancur, overwrites=ov_ann)
        
        for ch in ["share-content", "galery-bmmc", "logo-bmmc", "share-mods", "f8-command", "live-streaming"]:
            await get_or_create_text(f"📤┃{to_bold(ch)}", cat_penghancur)

        # BM CHAT
        cat_chat = await get_or_create_category(f"💬 {to_bold('BLOODY MARY CHAT')}", ov_bm)
        await get_or_create_text(f"🗣️┃{to_bold('all-bm-chat')}", cat_chat)
        await get_or_create_text(f"🎵┃{to_bold('req-music')}", cat_chat)

        # VOICE BM
        cat_voice = await get_or_create_category(f"🔊 {to_bold('VOICE BM')}", ov_bm)
        ov_jing = ov_bm.copy()
        ov_jing[role_tamu] = discord.PermissionOverwrite(view_channel=True, connect=True, read_message_history=True)
        
        await get_or_create_voice(f"🎙️┃{to_bold('VOICE JING-SENPAI-KERTA')}", cat_voice, overwrites=ov_jing)
        await get_or_create_voice(f"🎙️┃{to_bold('RAPAT KELUARGA')}", cat_voice)
        await get_or_create_voice(f"🎙️┃{to_bold('MABAR APA AJA')}", cat_voice)

        print('\n✅ ULTIMATE HISTORY LOCK SELESAI! Cek Discord, Zero!')
        
    except Exception as e:
        print(f'[!] Terjadi kesalahan: {e}')

    await bot.close()

bot.run(TOKEN)
