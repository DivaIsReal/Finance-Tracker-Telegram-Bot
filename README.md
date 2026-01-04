# 💰 Bot Keuangan - Finance Tracking Bot & Dashboard

Bot Telegram untuk mencatat transaksi keuangan otomatis + dashboard web untuk visualisasi data.

## ✨ Fitur

- 🤖 **Bot Telegram**: Catat transaksi dengan pesan natural (contoh: "makan siang 25rb")
- 📊 **Dashboard Web**: Visualisasi pemasukan/pengeluaran, grafik, dan tabel transaksi
- 📄 **Export PDF**: Unduh laporan transaksi per periode
- 🔄 **Auto Sync**: Data otomatis tersimpan ke Google Sheets
- 📱 **Responsive**: Dashboard bisa diakses dari HP atau desktop

## 🚀 Setup Cepat

### 1. Clone Repo & Install Dependencies

```bash
# Clone repository
git clone <repo-url>
cd bot-keuangan

# Install dependencies untuk bot
pip install -r requirements.txt

# Install dependencies untuk backend
pip install -r dashboard/backend/requirements.txt
```

### 2. Setup Google Sheets

1. Buat Google Sheet baru
2. Salin **Spreadsheet ID** dari URL (contoh: `https://docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit`)
3. Buat Service Account di [Google Cloud Console](https://console.cloud.google.com/):
   - Aktifkan Google Sheets API
   - Buat Service Account
   - Download kredensial JSON
4. Rename file kredensial menjadi `credentials.json` dan taruh di root folder
5. Beri akses **Editor** ke Sheet untuk email service account

### 3. Setup Bot Telegram

1. Chat [@BotFather](https://t.me/botfather) di Telegram
2. Buat bot baru dengan `/newbot`
3. Salin token yang diberikan

### 4. Konfigurasi (.env)

```bash
# Salin contoh ke .env
cp .env.example .env

# Edit .env dengan editor favorit
nano .env  # atau notepad .env
```

Isi nilai berikut di `.env`:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_FILE=credentials.json
API_PORT=8001
```

### 5. Jalankan Aplikasi

**Terminal 1 - Bot:**
```bash
python main.py
```

**Terminal 2 - Backend API:**
```bash
python dashboard/backend/api.py
```

**Frontend:**
- Buka `dashboard/frontend/index.html` di browser
- Atau host di web server (Netlify, Vercel, dll)

## 📝 Cara Pakai

### Bot Telegram

Kirim pesan natural ke bot:

**Pengeluaran:**
- `makan siang 25000`
- `beli kopi 15rb`
- `bensin 50k`
- `bayar listrik 200ribu`

**Pemasukan:**
- `gaji 5jt`
- `terima transfer 500rb`
- `bonus 1juta`

Bot akan otomatis:
- Deteksi nominal (support format: 15000, 15rb, 15k, 1.5jt)
- Kategorikan transaksi (Makan, Transport, Belanja, dll)
- Simpan ke Google Sheets

### Dashboard

- **Auto-refresh**: Data ter-update otomatis tiap 30 detik
- **Export PDF**: Pilih periode (Bulan ini, Bulan lalu, Custom, Semua data)
- **Grafik**: Trend 7 hari, kategori pengeluaran, perbandingan bulanan

## 📂 Struktur Folder

```
bot-keuangan/
├── .env                      # Konfigurasi (JANGAN commit!)
├── .env.example             # Contoh konfigurasi
├── credentials.json         # Google service account (JANGAN commit!)
├── requirements.txt         # Dependencies bot
├── main.py                  # Entry point bot
├── bot/
│   └── handlers.py         # Handler pesan Telegram
├── config/
│   └── settings.py         # Konfigurasi aplikasi
├── models/
│   └── transaction.py      # Model data transaksi
├── services/
│   ├── parser.py          # Parse pesan natural language
│   └── sheets.py          # Google Sheets manager
└── dashboard/
    ├── backend/
    │   ├── api.py         # FastAPI backend
    │   └── requirements.txt
    └── frontend/
        └── index.html     # Dashboard web
```

## 🔒 Keamanan

- **JANGAN commit** file `.env` atau `credentials.json` ke Git
- Tambahkan ke `.gitignore`:
  ```
  .env
  credentials.json
  __pycache__/
  *.pyc
  ```
- Untuk production, pakai environment variables di hosting

## 🌐 Deploy (Opsional)

### Bot
- Deploy ke VPS/VM, jalankan sebagai systemd service
- Atau pakai webhook mode di server yang sama dengan backend

### Backend API
- Deploy ke Railway, Fly.io, Render, atau VPS
- Set environment variables di dashboard hosting
- Gunakan reverse proxy (nginx) + HTTPS

### Frontend
- Host di Netlify, Vercel, GitHub Pages (static)
- Update `API_BASE_URL` di `index.html` ke URL backend production

## ⚙️ Troubleshooting

**Bot tidak merespon:**
- Cek `TELEGRAM_TOKEN` di `.env` sudah benar
- Pastikan `python main.py` jalan tanpa error

**Data tidak masuk Sheet:**
- Cek `SPREADSHEET_ID` sudah benar
- Pastikan service account punya akses Editor ke Sheet
- Cek file `credentials.json` ada dan valid

**Dashboard tidak load:**
- Pastikan backend API jalan di port 8001
- Cek `API_BASE_URL` di `index.html` sesuai
- Buka browser console untuk lihat error

**Rate limit Google Sheets:**
- Data di-cache 60 detik, seharusnya aman untuk 1-5 user
- Jika perlu, naikkan cache timeout di `api.py`

## 📦 Update Dependencies

```bash
# Update bot dependencies
pip install -r requirements.txt --upgrade

# Update backend dependencies
pip install -r dashboard/backend/requirements.txt --upgrade
```

## 🛠️ Maintenance

- **Backup**: Export Google Sheet secara berkala
- **Log**: Monitor terminal untuk error
- **Quota**: Google Sheets API limit ~100 req/100 detik

## 📄 Lisensi

Open source untuk penggunaan pribadi dan komersial.

## 👨‍💻 Credits

Created by **Diva**

---

**Happy tracking! 💰📊**
