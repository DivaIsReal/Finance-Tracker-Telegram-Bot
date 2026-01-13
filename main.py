"""Entry point Bot Keuangan (jalankan dengan: python main.py)."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import Config
from config.constants import LOG_FORMAT, LOG_LEVEL
from bot.handlers import (
    start_command,
    help_command,
    saldo_command,
    add_past_command,
    handle_text_message,
    error_handler
)

logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

def main():
    """Fungsi utama untuk menjalankan bot"""
    
    logger.info("🚀 Memulai Bot Keuangan...")
    logger.info(f"📱 Token: {Config.TELEGRAM_TOKEN[:10] if Config.TELEGRAM_TOKEN else 'NOT SET'}...")
    
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("saldo", saldo_command))
    app.add_handler(CommandHandler("add_past", add_past_command))
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_text_message
    ))
    
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot berhasil dijalankan!")
    logger.info("💬 Kirim pesan ke bot kamu di Telegram untuk test")
    logger.info("⚠️  Tekan Ctrl+C untuk stop bot")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()