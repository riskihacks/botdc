# 🥀 PROYEK DISCORD BOT BMMC (BLOODY MARY) 🥀

Halo! Ini rangkuman status terakhir buat Zero. Proyek ini tujuannya bikin server Discord BMMC jadi otomatis, rapi, dan premium.

## 📁 Struktur File
1. `setup_bmmc.py`: Script buat bikin channel, kategori, role, dan permission awal (Idempotent).
2. `main_bot.py`: Bot utama yang stand-by 24/7 untuk fitur interaktif.
3. `bot_data.json`: Database ingatan bot (nyimpen ID channel & pesan).

## ✅ Fitur yang SUDAH BERHASIL (100% JALAN)
1. **Setup Server:** Otomatis bikin kategori tebal (Bold) dan channel estetik.
2. **History Lock:** Semua role & member baru PASTI bisa baca chat lama (Read Message History ON).
3. **Welcome/Goodbye:** Kirim embed estetik + Foto Profil member yang join/leave.
4. **Premium Button Role:**
   - Pake Tombol (bukan emoji jadul).
   - Pesan balasan Rahasia (Ephemeral) - cuma user yang bisa liat.
   - **Anti-Numpuk (Sapu Bersih):** Kalau user ganti role, laporan lama di channel owner otomatis dihapus.
   - **Tag Owner:** Otomatis ngetag Zero (ID: 1040946853321117696) ke channel request (ID: 1504426382921302017).

## 🛠️ Status Terakhir & Pekerjaan Rumah
**Fitur Musik:**
- Udah pake `yt-dlp` dan `static-ffmpeg` (biar ga usah install manual).
- **Blocker Terakhir:** Muncul error `PyNaCl library needed`. 
- **Solusi yang baru dilakuin:** Tadi barusan udah `python -m pip install --force-reinstall PyNaCl discord.py`.
- **Langkah selanjutnya:** Zero cuma perlu **Matiin Bot (Ctrl+C)** terus **Jalanin lagi (`python main_bot.py`)** buat cek apakah musiknya udah bisa jalan atau belum.

---
*Dibuat dengan cinta oleh Glitch buat Zero. 🥀🫡💖*
