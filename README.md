# 🥀 BMMC DISCORD BOT 🥀

Bot multifungsi untuk server **Bloody Mary (BMMC)**.

## ✨ Fitur Utama:
- **Welcome & Goodbye:** Pesan embed estetik dengan avatar member.
- **Button Roles:** Sistem request role menggunakan tombol yang rapi.
- **Auto-Approve:** Persetujuan role cukup dengan reaction dari Owner.
- **Pro Music:** Pemutaran musik YouTube dengan sistem Top 10 Search & Queue.

## 🚀 Cara Install di VPS:
1. **Clone Repository:**
   ```bash
   git clone <link-repo-kamu>
   cd <nama-folder>
   ```
2. **Install Library:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalanin Pake PM2:**
   ```bash
   pm2 start main_bot.py --name "bmmc-bot" --interpreter python3
   ```

## 🛠️ Perintah Bot:
- `/setwelcome` : Set channel welcome.
- `/setmusic` : Set channel musik.
- `/setrole` : Munculkan tombol role (Hanya di Server Utama).
- `/play <judul>` : Cari dan putar musik.
- `/skip` : Skip lagu.
