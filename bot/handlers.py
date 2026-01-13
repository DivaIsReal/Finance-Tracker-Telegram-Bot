import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.parser import MessageParser
from services.sheets import sheets_manager
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Timezone Indonesia (WIB)
WIB = timezone(timedelta(hours=7))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    welcome_message = (
        "👋 **Halo! Selamat datang di Bot Keuangan!**\n\n"
        "Aku bisa bantu kamu catat keuangan dengan mudah!\n\n"
        "📝 **Cara pakai:**\n"
        "Kirim pesan biasa aja, misalnya:\n"
        "• Makan siang 25000\n"
        "• Beli kopi 15rb\n"
        "• Gaji 5jt\n"
        "• Grab ke mall 20k\n\n"
        "� **Lupa nyatet transaksi hari lalu?**\n"
        "• kemarin makan 25000\n"
        "• 2 hari lalu beli kopi 15rb\n"
        "• /add_past 10/01/2026 makan 25000\n\n"
        "⚙️ **Command:**\n"
        "/start - Mulai bot\n"
        "/help - Lihat bantuan lengkap\n"
        "/saldo - Cek saldo\n"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    help_text = (
        "📚 **PANDUAN LENGKAP**\n\n"
        "**Format Pesan:**\n"
        "Kirim pesan natural aja, aku akan otomatis deteksi!\n\n"
        "**Contoh Pengeluaran:**\n"
        "• Makan siang 25000\n"
        "• Beli baju 150rb\n"
        "• Bensin 50k\n"
        "• Bayar listrik 200ribu\n\n"
        "**Contoh Pemasukan:**\n"
        "• Gaji 5jt\n"
        "• Terima transfer 500rb\n"
        "• Bonus 1juta\n\n"
        "**Format Angka:**\n"
        "• 15000 atau 15rb atau 15k → Rp 15.000\n"
        "• 1.5jt atau 1,5jt → Rp 1.500.000\n\n"
        "🕐 **Catat Transaksi Hari Sebelumnya:**\n"
        "Kamu bisa catat pengeluaran yang lupa dengan:\n"
        "• `kemarin makan 25000` - Kemarin\n"
        "• `2 hari lalu beli kopi 15rb` - 2 hari lalu\n"
        "• `minggu lalu bensin 50rb` - Seminggu lalu\n"
        "• `10/01/2026 makan 25000` - Tanggal spesifik (DD/MM/YYYY)\n"
        "• `/add_past 10/01/2026 makan 25000` - Pakai command\n\n"
        "Bot akan otomatis kategorikan transaksi kamu! 🎯"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )

async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /saldo"""
    # Nanti akan dihubungkan ke database/sheets
    await update.message.reply_text(
        "💰 **SALDO KAMU**\n\n"
        "🔜 Fitur ini sedang dalam pengembangan!\n"
        "Akan segera terhubung dengan Google Sheets.",
        parse_mode='Markdown'
    )

async def add_past_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /add_past DD/MM/YYYY deskripsi nominal"""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Format: `/add_past DD/MM/YYYY deskripsi nominal`\n\n"
                "Contoh:\n"
                "`/add_past 10/01/2026 makan siang 25000`\n"
                "`/add_past 09/01/2026 beli kopi 15rb`",
                parse_mode='Markdown'
            )
            return
        
        # Ambil tanggal dari arg pertama
        date_str = context.args[0]
        
        # Parse tanggal
        try:
            parts = date_str.split('/')
            if len(parts) != 3:
                raise ValueError("Format harus DD/MM/YYYY")
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            custom_date = datetime(year, month, day, 
                                  hour=datetime.now(tz=WIB).hour,
                                  minute=datetime.now(tz=WIB).minute,
                                  second=datetime.now(tz=WIB).second,
                                  tzinfo=WIB)
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Format tanggal salah! Gunakan DD/MM/YYYY\n"
                "Contoh: `10/01/2026`",
                parse_mode='Markdown'
            )
            return
        
        # Gabung sisa pesan sebagai deskripsi
        message_text = ' '.join(context.args[1:])
        
        # Parse transaction dengan custom date
        transaction = MessageParser.parse_message(message_text, custom_date=custom_date)
        
        if not transaction:
            await update.message.reply_text(
                "❌ Maaf, nominal tidak ditemukan.\n"
                "Contoh: `/add_past 10/01/2026 makan siang 25000`",
                parse_mode='Markdown'
            )
            return
        
        response = transaction.format_message()
        saved_to_sheets = False
        current_balance = None
        
        if sheets_manager.connected:
            saved_to_sheets = sheets_manager.add_transaction(transaction)
            if saved_to_sheets:
                current_balance = sheets_manager.get_balance()
        else:
            response += "\n\nℹ️  Google Sheets belum dikonfigurasi (SPREADSHEET_ID/credentials.json)."
        
        if saved_to_sheets:
            response += "\n\n✅ Tersimpan ke Google Sheets!"
            if current_balance is not None:
                response += f"\n💰 Saldo Terkini: Rp {current_balance:,.0f}"
        elif sheets_manager.connected:
            response += "\n\n⚠️  Gagal menyimpan ke Google Sheets."
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in add_past_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Maaf, terjadi error saat memproses pesan. Coba lagi ya!"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan text biasa"""
    user_text = update.message.text or ""
    
    try:
        transaction = MessageParser.parse_message(user_text)
        
        if not transaction:
            await update.message.reply_text(
                "❌ Maaf, nominal tidak ditemukan.\n"
                "Contoh: \"makan siang 25000\", \"beli kopi 15rb\", atau \"gaji 5jt\"."
            )
            return
        
        response = transaction.format_message()
        saved_to_sheets = False
        current_balance = None
        
        if sheets_manager.connected:
            saved_to_sheets = sheets_manager.add_transaction(transaction)
            if saved_to_sheets:
                current_balance = sheets_manager.get_balance()
        else:
            response += "\n\nℹ️  Google Sheets belum dikonfigurasi (SPREADSHEET_ID/credentials.json)."
        
        if saved_to_sheets:
            response += "\n\n✅ Tersimpan ke Google Sheets!"
            if current_balance is not None:
                response += f"\n💰 Saldo Terkini: Rp {current_balance:,.0f}"
        elif sheets_manager.connected:
            response += "\n\n⚠️  Gagal menyimpan ke Google Sheets."
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Maaf, terjadi error saat memproses pesan. Coba lagi ya!"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error"""
    logger.error(f'Update {update} caused error {context.error}', exc_info=True)
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Maaf, terjadi error!\n"
            "Coba lagi atau hubungi admin."
        )