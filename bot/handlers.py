import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.parser import MessageParser
from services.sheets import sheets_manager
from datetime import datetime

logger = logging.getLogger(__name__)

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
        "📸 Atau kirim foto struk langsung!\n\n"
        "⚙️ **Command:**\n"
        "/start - Mulai bot\n"
        "/help - Lihat bantuan\n"
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