from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    """Model untuk menyimpan data transaksi"""
    amount: float
    transaction_type: str  # 'income' atau 'expense'
    category: str
    description: str
    date: datetime
    photo_url: Optional[str] = None
    detail: Optional[str] = None  # Detail items dari struk
    
    def to_dict(self):
        """Ubah menjadi dict untuk penyimpanan."""
        return {
            'date': self.date.strftime('%d/%m/%Y'),
            'time': self.date.strftime('%H:%M:%S'),
            'type': 'Pemasukan' if self.transaction_type == 'income' else 'Pengeluaran',
            'category': self.category,
            'amount': self.amount,
            'description': self.description,
            'detail': self.detail or '',
            'photo_url': self.photo_url or ''
        }
    
    def format_message(self):
        """Format pesan konfirmasi ke pengguna."""
        emoji = '💰' if self.transaction_type == 'income' else '💸'
        type_text = 'PEMASUKAN' if self.transaction_type == 'income' else 'PENGELUARAN'
        sign = '+' if self.transaction_type == 'income' else '-'
        
        message = (
            f"{emoji} **{type_text} TERCATAT!**\n\n"
            f"📊 Kategori: {self.category}\n"
            f"💵 Jumlah: {sign} Rp {self.amount:,.0f}\n"
            f"📝 Keterangan: {self.description}\n"
            f"🕐 Waktu: {self.date.strftime('%d/%m/%Y %H:%M')}"
        )
        
        # Tambahkan detail kalau ada
        if self.detail:
            message += f"\n\n📋 **Detail:**\n{self.detail}"
        
        return message