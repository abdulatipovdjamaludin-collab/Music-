import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading

# ================ НАСТРОЙКИ ================
BOT_TOKEN = "8719005469:AAFjCYA7_kRPe-bcJTZUnk5Xa9hKjA3obFU"

# ================ ЛОГИРОВАНИЕ ================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================ КОМАНДА START ================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Привет! Я музыкальный бот. Я работаю!")

# ================ ЗАПУСК БОТА ================
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("✅ Бот запущен!")
    app.run_polling()

# ================ FLASK ДЛЯ RENDER ================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    flask_thread = threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))))
    flask_thread.daemon = True
    flask_thread.start()
    run_bot()

