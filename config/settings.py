import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Konfigurasi untuk bot"""
    
    # ========== TELEGRAM ==========
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️  TELEGRAM_TOKEN tidak ditemukan di .env!")
        logger.warning("Bot tidak akan bisa jalan sampai token diisi.")
    
    # ========== GOOGLE SHEETS ==========
    SHEETS_CREDS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    
    # Validasi Spreadsheet ID
    if not SPREADSHEET_ID:
        logger.warning("⚠️  SPREADSHEET_ID tidak ditemukan di .env!")
        logger.warning("Data tidak akan tersimpan ke Google Sheets.")
    if not os.path.exists(SHEETS_CREDS_FILE):
        logger.warning(f"⚠️  File kredensial tidak ditemukan: {SHEETS_CREDS_FILE}")
        logger.warning("Pastikan GOOGLE_CREDENTIALS_FILE di .env mengarah ke credentials.json kamu.")
    
    # ========== KATEGORI & KEYWORDS ==========
    
    # Kategori Pengeluaran & Keywords untuk deteksi
    EXPENSE_KEYWORDS = {
        'Makan': [
            'makan', 'sarapan', 'lunch', 'dinner', 'nasi', 'ayam', 'soto', 'bakso', 
            'mie', 'kopi', 'teh', 'minum', 'snack', 'jajan', 'cemilan', 'food',
            'geprek', 'seblak', 'warteg', 'resto', 'restoran', 'cafe', 'kedai',
            'lapar', 'kenyang', 'minum', 'minuman'
        ],
        'Transport': [
            'transport', 'grab', 'gojek', 'ojek', 'taxi', 'angkot', 'bus',
            'bensin', 'parkir', 'tol', 'kereta', 'travel', 'pergi', 'pulang'
        ],
        'Belanja': [
            'belanja', 'beli', 'baju', 'celana', 'sepatu', 'tas',
            'shopee', 'tokped', 'tokopedia', 'lazada', 'blibli', 'toko',
            'shopping', 'shop'
        ],
        'Tagihan': [
            'listrik', 'air', 'pdam', 'wifi', 'internet', 'pulsa', 'paket data',
            'token', 'bayar', 'cicilan', 'angsuran', 'pln', 'tagihan'
        ],
        'Hiburan': [
            'nonton', 'bioskop', 'film', 'game', 'main', 'liburan', 'wisata',
            'netflix', 'spotify', 'steam', 'tiket', 'jalan-jalan'
        ],
        'Kesehatan': [
            'obat', 'dokter', 'rumah sakit', 'rs', 'klinik', 'vitamin',
            'apotek', 'medical', 'checkup', 'berobat', 'sakit'
        ],
    }
    
    # Keywords untuk Pemasukan
    INCOME_KEYWORDS = [
        'gaji', 'terima', 'transfer', 'bonus', 'freelance', 
        'pendapatan', 'dapat', 'masuk', 'bayaran', 'honor', 
        'untung', 'diterima', 'income'
    ]