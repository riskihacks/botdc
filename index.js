const { 
    Client, GatewayIntentBits, EmbedBuilder, ActionRowBuilder, ButtonBuilder, 
    ButtonStyle, Events, StringSelectMenuBuilder, PermissionsBitField 
} = require('discord.js');
const { 
    joinVoiceChannel, createAudioPlayer, createAudioResource, 
    AudioPlayerStatus, VoiceConnectionStatus 
} = require('@discordjs/voice');
const play = require('play-dl');
const yts = require('yt-search'); // PENCARI CADANGAN (LEBIH STABIL)
const fs = require('fs');

// --- KONFIGURASI ---
const TOKEN = 'MTUwNDQxNjUyMDQwOTcxMDY4Nw.Gy9q-H.hWMsOm9TlTdV7SqvDpDIMIIQDwr8cJLAWgaDbs';
const OWNER_ID = '1040946853321117696';
const MAIN_GUILD_ID = '1503125428875825232';
const ROLE_LOG_CH_ID = '1504426382921302017';
const DATABASE_FILE = './bot_data.json';

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMessageReactions
    ]
});

// --- ANTI-CRASH ---
process.on('unhandledRejection', e => { console.error('R:', e); });
process.on('uncaughtException', e => { console.error('E:', e); });

// --- DATABASE ---
function loadData() { return fs.existsSync(DATABASE_FILE) ? JSON.parse(fs.readFileSync(DATABASE_FILE, 'utf8')) : {}; }
function saveData(data) { fs.writeFileSync(DATABASE_FILE, JSON.stringify(data, null, 2)); }
function getGuildData(gid) {
    let d = loadData(); if (!d[gid]) { d[gid] = { welcome_ch: null, music_ch: null }; saveData(d); }
    return d[gid];
}
function setGuildData(gid, k, v) { let d = loadData(); if (!d[gid]) d[gid] = { welcome_ch: null, music_ch: null }; d[gid][k] = v; saveData(d); }

// --- MUSIC ---
const queues = new Map();
async function playNext(gid, ch) {
    const q = queues.get(gid); if (!q || q.songs.length === 0) return;
    const s = q.songs.shift(); if (!s || !s.url) return;
    try {
        console.log(`[Music] Playing: ${s.title}`);
        let stream = await play.stream(s.url);
        let res = createAudioResource(stream.stream, { inputType: stream.type });
        q.player.play(res);
        ch.send(`🎶 **Now Playing:** \`${s.title}\``);
    } catch (e) { console.error(e); playNext(gid, ch); }
}

client.once(Events.ClientReady, c => { console.log(`\n[+] Bot Online: ${c.user.tag}`); });

client.on(Events.GuildMemberAdd, m => {
    const d = getGuildData(m.guild.id); if (!d.welcome_ch) return;
    const ch = m.guild.channels.cache.get(d.welcome_ch); if (!ch) return;
    const emb = new EmbedBuilder().setTitle("✨ WELCOME ✨").setDescription(`Halo <@${m.id}>! Selamat datang di ${m.guild.name}! 🥀🔥`).setColor(0xFF0000).setThumbnail(m.user.displayAvatarURL());
    ch.send({ embeds: [emb] });
});

client.on(Events.InteractionCreate, async i => {
    try {
        if (!i.isMessageComponent()) return;
        await i.deferReply({ ephemeral: true });

        // MUSIC SELECT
        if (i.isStringSelectMenu() && i.customId === 'music_select') {
            const url = i.values[0];
            const info = await play.video_info(url);
            if (!queues.has(i.guildId)) {
                const p = createAudioPlayer(); p.on(AudioPlayerStatus.Idle, () => playNext(i.guildId, i.channel));
                queues.set(i.guildId, { player: p, connection: null, songs: [] });
            }
            const q = queues.get(i.guildId);
            q.songs.push({ url, title: info.video_details.title });
            if (!i.member.voice.channel) return i.followUp("⚠️ Masuk Voice dulu!");
            if (!q.connection) {
                q.connection = joinVoiceChannel({ channelId: i.member.voice.channel.id, guildId: i.guildId, adapterCreator: i.guild.voiceAdapterCreator });
                q.connection.subscribe(q.player);
            }
            if (q.player.state.status === AudioPlayerStatus.Idle) { playNext(i.guildId, i.channel); await i.followUp("✅ Memulai musik!"); }
            else await i.followUp("➕ Masuk antrian!");
        }

        // ROLE BUTTONS
        if (i.isButton() && i.customId.startsWith('role_')) {
            if (i.guildId !== MAIN_GUILD_ID) return i.followUp("⚠️ Eksklusif BMMC!");
            const map = { 'role_glorix': 'BM GLORIX', 'role_indopride': 'BM INDOPRIDE', 'role_knrp': 'BM KNRP', 'role_tamu': 'TAMU BM' };
            const rn = map[i.customId]; const log = i.guild.channels.cache.get(ROLE_LOG_CH_ID);
            if (log) {
                const msgs = await log.messages.fetch({ limit: 10 });
                const old = msgs.filter(m => m.author.id === client.user.id && m.embeds[0] && m.embeds[0].fields[0].value.includes(i.user.id));
                await Promise.all(old.map(m => m.delete().catch(() => {})));
                const emb = new EmbedBuilder().setTitle("🎫 NEW ROLE REQUEST").setColor(0xFFA500).setDescription(`Klik ⏳ untuk approve **${rn}**`).addFields({ name: "User", value: `<@${i.user.id}>`, inline: true }, { name: "Role", value: rn, inline: true });
                const m = await log.send({ content: `<@${OWNER_ID}>`, embeds: [emb] }); await m.react("⏳");
                await i.followUp(`✅ Request **${rn}** dikirim!`);
            }
        }
    } catch (e) { console.error(e); }
});

client.on(Events.MessageCreate, async m => {
    try {
        if (m.author.bot || !m.content.startsWith('/')) return;
        const args = m.content.slice(1).split(/ +/); const cmd = args.shift().toLowerCase();
        if (cmd === 'setwelcome') { setGuildData(m.guildId, 'welcome_ch', m.channelId); m.delete(); m.channel.send("✅ Welcome set!").then(x => setTimeout(() => x.delete(), 3000)); }
        if (cmd === 'setmusic') { setGuildData(m.guildId, 'music_ch', m.channelId); m.delete(); m.channel.send("✅ Music set!").then(x => setTimeout(() => x.delete(), 3000)); }
        if (cmd === 'setrole') {
            if (m.guildId !== MAIN_GUILD_ID) return m.reply("⚠️ Khusus Utama!");
            m.delete(); const emb = new EmbedBuilder().setTitle("🎭 AMBIL ROLE 🎭").setDescription("Klik tombol...").setColor(0x0000FF);
            const row = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('role_glorix').setLabel('BM GLORIX').setStyle(ButtonStyle.Danger).setEmoji('🔴'),
                new ButtonBuilder().setCustomId('role_indopride').setLabel('BM INDOPRIDE').setStyle(ButtonStyle.Primary).setEmoji('🔵'),
                new ButtonBuilder().setCustomId('role_knrp').setLabel('BM KNRP').setStyle(ButtonStyle.Success).setEmoji('🟢'),
                new ButtonBuilder().setCustomId('role_tamu').setLabel('TAMU BM').setStyle(ButtonStyle.Secondary).setEmoji('🟡')
            );
            m.channel.send({ embeds: [emb], components: [row] });
        }
        if (cmd === 'play') {
            const d = getGuildData(m.guildId); if (d.music_ch && m.channelId !== d.music_ch) return;
            const q = args.join(' '); if (!q) return m.reply("Cari apa sayang?");
            const r = await yts(q); // PAKE YT-SEARCH (LEBIH STABIL)
            const opts = r.videos.slice(0, 10).map(v => ({ label: v.title.slice(0, 100), value: v.url }));
            const row = new ActionRowBuilder().addComponents(new StringSelectMenuBuilder().setCustomId('music_select').setPlaceholder('Pilih lagu...').addOptions(opts));
            m.channel.send({ content: "🎶 **Pilih lagu dari Top 10:**", components: [row] });
        }
        if (cmd === 'skip') { const q = queues.get(m.guildId); if (q) { q.player.stop(); m.channel.send("⏭️ Skip!"); } }
        if (cmd === 'stop') { const q = queues.get(m.guildId); if (q) { q.connection.destroy(); queues.delete(m.guildId); m.channel.send("⏹️ Stop!"); } }
    } catch (e) { console.error(e); }
});

client.on(Events.MessageReactionAdd, async (r, u) => {
    try {
        if (u.id !== OWNER_ID || r.emoji.name !== "⏳") return;
        const m = await r.message.fetch(); const emb = m.embeds[0];
        if (!emb || !emb.title.includes("NEW ROLE REQUEST")) return;
        const uid = emb.fields[0].value.replace(/[<@!>]/g, ''); const rn = emb.fields[1].value;
        const mem = await m.guild.members.fetch(uid); const rol = m.guild.roles.cache.find(x => x.name === rn);
        if (mem && rol) {
            await mem.roles.add(rol); await m.reactions.removeAll(); await m.react("✅");
            const nEmb = EmbedBuilder.from(emb).setTitle("✅ ROLE APPROVED").setColor(0x00FF00).setDescription(`Role **${rn}** diberikan.`);
            await m.edit({ embeds: [nEmb] });
            m.channel.send(`✅ **${mem.user.username}** sukses!`).then(x => setTimeout(() => x.delete(), 5000));
        }
    } catch (e) { console.error(e); }
});

client.login(TOKEN);
