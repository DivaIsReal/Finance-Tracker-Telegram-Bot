import re
from datetime import datetime
from typing import Optional, Tuple
from models.transaction import Transaction
from config.settings import Config

class MessageParser:
    """Parser untuk mengekstrak informasi dari pesan."""
    
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
        """Bersihkan teks keterangan dari angka/satuan."""
        # Hapus pattern angka dengan satuan
        text = re.sub(r'\d+\.?\d*\s*(?:jt|juta|k|rb|ribu)', '', text, flags=re.IGNORECASE)
        # Hapus angka biasa
        text = re.sub(r'\b\d{3,}\b', '', text)
        # Bersihkan whitespace berlebih
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else 'Transaksi'
    
    @staticmethod
    def parse_message(text: str) -> Optional[Transaction]:
        """Parse pesan menjadi objek Transaction."""
        # Extract amount
        amount = MessageParser.extract_amount(text)
        
        if not amount:
            return None
        
        # Detect type & category
        transaction_type, category = MessageParser.detect_category(text)
        
        # Clean description
        description = MessageParser.clean_description(text, amount)
        
        # Buat Transaction object
        return Transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            date=datetime.now()
        )