"""
Bot Keuangan - Main Entry Point
Jalankan file ini untuk start bot: python main.py
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import Config
from config.constants import LOG_FORMAT, LOG_LEVEL
from bot.handlers import (
    start_command,
    help_command,
    saldo_command,
    handle_text_message,
    error_handler
)

# Setup logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

def main():
    """Fungsi utama untuk menjalankan bot"""
    
    logger.info("🚀 Memulai Bot Keuangan...")
    logger.info(f"📱 Token: {Config.TELEGRAM_TOKEN[:10] if Config.TELEGRAM_TOKEN else 'NOT SET'}...")
    
    # Buat application dengan token dari config
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    # Daftarkan command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("saldo", saldo_command))
    
    # Daftarkan message handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_text_message
    ))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Jalankan bot
    logger.info("✅ Bot berhasil dijalankan!")
    logger.info("💬 Kirim pesan ke bot kamu di Telegram untuk test")
    logger.info("⚠️  Tekan Ctrl+C untuk stop bot")
    
    # Start polling (bot akan terus berjalan)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()