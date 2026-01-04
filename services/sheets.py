import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
from models.transaction import Transaction
from config.settings import Config

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Pengelola operasi Google Sheets."""
    
    def __init__(self):
        self.client = None
        self.sheet = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Bangun koneksi ke Google Sheets."""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                Config.SHEETS_CREDS_FILE, 
                scope
            )
            
            self.client = gspread.authorize(creds)
            
            # Buka spreadsheet by ID
            spreadsheet = self.client.open_by_key(Config.SPREADSHEET_ID)
            self.sheet = spreadsheet.sheet1
            self._setup_header()
            
            self.connected = True
            logger.info("✅ Berhasil terhubung ke Google Sheets!")
            
        except FileNotFoundError:
            logger.error(f"❌ File credentials.json tidak ditemukan: {Config.SHEETS_CREDS_FILE}")
            self.connected = False
            
        except Exception as e:
            logger.error(f"❌ Error koneksi ke Google Sheets: {e}", exc_info=True)
            self.connected = False
    
    def _setup_header(self):
        """Buat header di baris pertama bila belum tersedia."""
        try:
            first_row = self.sheet.row_values(1)
            
            if not first_row or first_row[0] != 'Tanggal':
                headers = ['Tanggal', 'Waktu', 'Tipe', 'Kategori', 'Jumlah', 'Keterangan', 'Saldo']
                self.sheet.update('A1:G1', [headers])
                self.sheet.format('A1:G1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                })
                
                logger.info("📋 Header berhasil dibuat!")
        except Exception as e:
            logger.warning(f"Tidak bisa setup header: {e}")
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Tambah transaksi ke Google Sheets, True jika berhasil."""
        if not self.connected:
            logger.error("❌ Tidak terhubung ke Google Sheets")
            return False
        
        try:
            data = transaction.to_dict()
            
            current_balance = self._get_current_balance()
            
            if transaction.transaction_type == 'income':
                new_balance = current_balance + transaction.amount
            else:
                new_balance = current_balance - transaction.amount
            
            amount_display = transaction.amount if transaction.transaction_type == 'income' else -transaction.amount
            
            row = [
                data['date'],
                data['time'],
                data['type'],
                data['category'],
                amount_display,
                data['description'],
                data['detail'],
                new_balance
            ]
            
            self.sheet.append_row(row)
            
            logger.info(f"✅ Transaksi berhasil ditambahkan: Rp {transaction.amount:,.0f} | Saldo: Rp {new_balance:,.0f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saat menyimpan ke sheets: {e}", exc_info=True)
            return False
    
    def _get_current_balance(self) -> float:
        """Ambil saldo terakhir dari kolom saldo."""
        try:
            saldo_col = self.sheet.col_values(8)
            if len(saldo_col) > 1:
                last_balance = saldo_col[-1]
                try:
                    return float(str(last_balance).replace(',', ''))
                except:
                    return 0.0
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Tidak bisa ambil saldo terakhir: {e}")
            return 0.0
    
    def get_today_summary(self) -> dict:
        """Ringkasan transaksi harian (belum diimplementasikan)."""
        pass
    
    def get_balance(self) -> float:
        """Get saldo terkini"""
        if not self.connected:
            return 0.0
        
        return self._get_current_balance()


# Singleton instance
sheets_manager = GoogleSheetsManager()