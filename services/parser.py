import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from models.transaction import Transaction
from config.settings import Config

# Timezone Indonesia (WIB)
WIB = timezone(timedelta(hours=7))

class MessageParser:
    """Parser untuk mengekstrak informasi dari pesan."""
    
    # Mapping untuk angka bahasa Indonesia
    INDONESIAN_NUMBERS = {
        'satu': 1, 'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5,
        'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9,
        'sepuluh': 10, 'sebelas': 11, 'dua belas': 12
    }
    
    @staticmethod
    def parse_indonesian_number(text: str) -> Optional[int]:
        """Parse angka dari bahasa Indonesia."""
        text_lower = text.lower().strip()
        
        # Check long numbers first (e.g., "dua belas")
        for words, num in MessageParser.INDONESIAN_NUMBERS.items():
            if text_lower == words:
                return num
        
        return None
    
    @staticmethod
    def extract_date(text: str) -> Optional[datetime]:
        """Ekstrak tanggal dari pesan (kemarin, 2 hari lalu, atau format tanggal)."""
        text_lower = text.lower()
        now = datetime.now(tz=WIB)
        
        # Pattern: "kemarin", "yesterday"
        if re.search(r'\bkemarin\b|\byesterday\b', text_lower):
            result = now.replace(hour=0, minute=0, second=0) - timedelta(days=1)
            return result
        
        # Pattern: "N hari yang lalu" atau "N hari lalu", "N days ago" (dengan angka)
        days_match = re.search(r'(\d+)\s*(?:hari\s*(?:yang\s*)?)?lalu', text_lower)
        if days_match:
            days = int(days_match.group(1))
            result = now.replace(hour=0, minute=0, second=0) - timedelta(days=days)
            return result
        
        # Pattern: "kata_angka hari yang lalu" atau "kata_angka hari lalu" (dengan bahasa Indonesia)
        # Contoh: "dua hari yang lalu", "tiga hari lalu", "lima hari yang lalu"
        indo_days_match = re.search(r'(satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|sebelas|dua\s+belas)\s+(?:hari\s*(?:yang\s*)?)?lalu', text_lower)
        if indo_days_match:
            days_word = indo_days_match.group(1)
            days = MessageParser.parse_indonesian_number(days_word)
            if days:
                result = now.replace(hour=0, minute=0, second=0) - timedelta(days=days)
                return result
        
        # Pattern: "minggu lalu", "minggu kemarin", "last week" (7 hari lalu)
        if re.search(r'minggu\s*(?:lalu|kemarin)|last\s*week', text_lower):
            result = now.replace(hour=0, minute=0, second=0) - timedelta(days=7)
            return result
        
        # Pattern: "bulan lalu", "last month" (30 hari lalu)
        if re.search(r'bulan\s*(?:lalu|kemarin)|last\s*month', text_lower):
            result = now.replace(hour=0, minute=0, second=0) - timedelta(days=30)
            return result
        
        # Pattern: tanggal format DD/MM/YYYY atau DD-MM-YYYY
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if date_match:
            try:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3))
                # Buat datetime dengan waktu pukul 00:00:00
                parsed_date = datetime(year, month, day, 
                                      hour=0, minute=0, second=0, 
                                      tzinfo=WIB)
                return parsed_date
            except ValueError:
                pass
        
        # Tidak ada tanggal ditemukan
        return None
    
    @staticmethod
    def clean_text_from_date(text: str) -> str:
        """Hapus pattern tanggal dari teks untuk cleaning description."""
        # Hapus "kemarin", "N hari lalu", dll
        text = re.sub(r'\bkemarin\b|\byesterday\b', '', text, flags=re.IGNORECASE)
        # Hapus "N hari lalu" atau "N hari yang lalu" (angka)
        text = re.sub(r'\d+\s*(?:hari\s*(?:yang\s*)?)?lalu', '', text, flags=re.IGNORECASE)
        # Hapus "kata_angka hari lalu" (bahasa Indonesia)
        text = re.sub(r'(satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|sebelas|dua\s+belas)\s+(?:hari\s*(?:yang\s*)?)?lalu', '', text, flags=re.IGNORECASE)
        text = re.sub(r'minggu\s*(?:lalu|kemarin)|last\s*week', '', text, flags=re.IGNORECASE)
        text = re.sub(r'bulan\s*(?:lalu|kemarin)|last\s*month', '', text, flags=re.IGNORECASE)
        # Hapus format tanggal
        text = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', '', text)
        return text
    
    @staticmethod
    def extract_amount(text: str) -> Optional[float]:
        """Ambil nominal uang (format: 15000, 15rb/k, 1.5jt, 1,5jt)."""
        text = text.lower().replace(',', '.')
        
        # Pattern untuk jutaan (1.5jt, 2jt, 1.5juta, 5jt)
        juta_match = re.search(r'(\d+\.?\d*)\s*(?:jt|juta)', text)
        if juta_match:
            return float(juta_match.group(1)) * 1_000_000
        
        # Pattern untuk ribuan (15k, 15rb, 15ribu)
        ribu_match = re.search(r'(\d+\.?\d*)\s*(?:k\b|rb|ribu)', text)
        if ribu_match:
            return float(ribu_match.group(1)) * 1_000
        
        # Pattern untuk angka biasa (5000, 15000, 250000)
        # Cari angka dengan minimal 3 digit (asumsi uang minimal 100)
        angka_match = re.search(r'\b(\d{3,})\b', text)
        if angka_match:
            return float(angka_match.group(1))
        
        return None
    
    @staticmethod
    def detect_category(text: str) -> Tuple[str, str]:
        """Deteksi tipe transaksi dan kategori."""
        text = text.lower()
        
        # Check income keywords dulu
        for keyword in Config.INCOME_KEYWORDS:
            if keyword in text:
                return 'income', 'Pemasukan'
        
        # Check expense categories
        for category, keywords in Config.EXPENSE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return 'expense', category
        
        # Default: expense dengan kategori Lainnya
        return 'expense', 'Lainnya'
    
    @staticmethod
    def clean_description(text: str, amount: float) -> str:
        """Bersihkan teks keterangan dari angka/satuan dan tanggal."""
        # Hapus pattern tanggal dulu
        text = MessageParser.clean_text_from_date(text)
        # Hapus pattern angka dengan satuan
        text = re.sub(r'\d+\.?\d*\s*(?:jt|juta|k|rb|ribu)', '', text, flags=re.IGNORECASE)
        # Hapus angka biasa
        text = re.sub(r'\b\d{3,}\b', '', text)
        # Bersihkan whitespace berlebih
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else 'Transaksi'
    
    @staticmethod
    def parse_message(text: str, custom_date: Optional[datetime] = None) -> Optional[Transaction]:
        """Parse pesan menjadi objek Transaction.
        
        Args:
            text: Pesan dari user
            custom_date: Tanggal custom (jika ada), jika tidak ada akan di-parse dari text
        """
        # Extract amount
        amount = MessageParser.extract_amount(text)
        
        if not amount:
            return None
        
        # Detect type & category
        transaction_type, category = MessageParser.detect_category(text)
        
        # Clean description
        description = MessageParser.clean_description(text, amount)
        
        # Tentukan tanggal
        if custom_date:
            transaction_date = custom_date
        else:
            # Coba ekstrak dari text, jika tidak ada gunakan sekarang
            transaction_date = MessageParser.extract_date(text) or datetime.now(tz=WIB)
        
        # Buat Transaction object
        return Transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            date=transaction_date
        )