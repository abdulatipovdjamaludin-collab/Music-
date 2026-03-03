import os
import logging
import asyncio
import tempfile
import subprocess
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import threading
import signal
import sys
from typing import Optional, Dict

# ================ НАСТРОЙКИ ================
BOT_TOKEN = "8719005469:AAFjCYA7_kRPe-bcJTZUnk5X9hKjA3obFU"
ADMIN_ID = 5929364458
CHANNEL_ID = -1003862305705
CHANNEL_LINK = "https://t.me/твой_канал"
AUDD_API_KEY = "e3b4ce5b27eafae6cc7978fee246eb84"  # Твой ключ

# ================ ЛОГИРОВАНИЕ ================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================ ПЕРЕВОДЫ ================
TRANSLATIONS = {
    'ru': {
        'choose_language': '🌐 Выберите язык:',
        'language_selected': '✅ Язык выбран: Русский',
        'subscribe_first': '📢 Чтобы пользоваться ботом, подпишись на канал!\n\nПосле подписки нажми кнопку ниже:',
        'subscribe_button': '📢 Подписаться на канал',
        'check_button': '🔄 Я подписался',
        'thanks_subscribe': '✅ Спасибо за подписку! Теперь ты можешь пользоваться ботом.\n\nОтправь мне название трека или видео с музыкой.',
        'not_subscribed': '❌ Подписка не найдена. Пожалуйста, подпишись на канал!',
        'welcome': '🎵 Привет! Я музыкальный бот.\n\nОтправь мне название трека или видео с музыкой, и я найду его!\n\nПример: Imagine Dragons - Believer',
        'searching': '🔍 Ищу: {query}',
        'processing_video': '🎬 Обрабатываю видео, подожди...',
        'recognizing': '🎵 Распознаю музыку из видео...',
        'found': '🎵 Найдено: {title}',
        'download': '⬇️ Скачать',
        'not_found': '❌ Не удалось распознать музыку. Попробуй другое видео.',
        'error': '❌ Ошибка: {error}',
        'not_video': '❌ Пожалуйста, отправь видеофайл или ссылку на видео.'
    },
    'en': {
        'choose_language': '🌐 Choose language:',
        'language_selected': '✅ Language selected: English',
        'subscribe_first': '📢 To use the bot, subscribe to the channel!\n\nAfter subscribing, click the button below:',
        'subscribe_button': '📢 Subscribe to channel',
        'check_button': '🔄 I have subscribed',
        'thanks_subscribe': '✅ Thanks for subscribing! Now you can use the bot.\n\nSend me a track name or video with music.',
        'not_subscribed': '❌ Subscription not found. Please subscribe to the channel!',
        'welcome': '🎵 Hello! I am a music bot.\n\nSend me a track name or video with music, and I will find it!\n\nExample: Imagine Dragons - Believer',
        'searching': '🔍 Searching: {query}',
        'processing_video': '🎬 Processing video, please wait...',
        'recognizing': '🎵 Recognizing music from video...',
        'found': '🎵 Found: {title}',
        'download': '⬇️ Download',
        'not_found': '❌ Could not recognize music. Try another video.',
        'error': '❌ Error: {error}',
        'not_video': '❌ Please send a video file or video link.'
    },
    'zh': {
        'choose_language': '🌐 选择语言:',
        'language_selected': '✅ 已选择语言: 中文',
        'subscribe_first': '📢 要使用机器人，请订阅频道！\n\n订阅后，请点击下面的按钮：',
        'subscribe_button': '📢 订阅频道',
        'check_button': '🔄 我已订阅',
        'thanks_subscribe': '✅ 感谢订阅！现在您可以使用机器人。\n\n向我发送曲目名称或带有音乐的视频。',
        'not_subscribed': '❌ 未找到订阅。请订阅频道！',
        'welcome': '🎵 你好！我是音乐机器人。\n\n向我发送曲目名称或带有音乐的视频，我会找到它！\n\n例如: Imagine Dragons - Believer',
        'searching': '🔍 搜索中: {query}',
        'processing_video': '🎬 正在处理视频，请稍候...',
        'recognizing': '🎵 正在从视频中识别音乐...',
        'found': '🎵 找到: {title}',
        'download': '⬇️ 下载',
        'not_found': '❌ 无法识别音乐。请尝试其他视频。',
        'error': '❌ 错误: {error}',
        'not_video': '❌ 请发送视频文件或视频链接。'
    },
    'uk': {
        'choose_language': '🌐 Виберіть мову:',
        'language_selected': '✅ Мову вибрано: Українська',
        'subscribe_first': '📢 Щоб користуватися ботом, підпишись на канал!\n\nПісля підписки натисни кнопку нижче:',
        'subscribe_button': '📢 Підписатися на канал',
        'check_button': '🔄 Я підписався',
        'thanks_subscribe': '✅ Дякую за підписку! Тепер ти можеш користуватися ботом.\n\nНадішли мені назву треку або відео з музикою.',
        'not_subscribed': '❌ Підписку не знайдено. Будь ласка, підпишись на канал!',
        'welcome': '🎵 Привіт! Я музичний бот.\n\nНадішли мені назву треку або відео з музикою, і я знайду його!\n\nПриклад: Imagine Dragons - Believer',
        'searching': '🔍 Шукаю: {query}',
        'processing_video': '🎬 Обробляю відео, зачекай...',
        'recognizing': '🎵 Розпізнаю музику з відео...',
        'found': '🎵 Знайдено: {title}',
        'download': '⬇️ Завантажити',
        'not_found': '❌ Не вдалося розпізнати музику. Спробуй інше відео.',
        'error': '❌ Помилка: {error}',
        'not_video': '❌ Будь ласка, надішли відеофайл або посилання на відео.'
    }
}

# ================ ХРАНИЛИЩЕ ЯЗЫКОВ ПОЛЬЗОВАТЕЛЕЙ ================
user_languages: Dict[int, str] = {}

def get_text(user_id: int, key: str, **kwargs) -> str:
    """Получить текст на языке пользователя"""
    lang = user_languages.get(user_id, 'ru')
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['ru'][key])
    return text.format(**kwargs)

# ================ ОБРАБОТЧИК ЗАВЕРШЕНИЯ ================
def signal_handler(sig, frame):
    logger.info("Получен сигнал завершения, останавливаю бота...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ================ ФУНКЦИЯ ПРОВЕРКИ ПОДПИСКИ ================
async def check_subscription(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ['left', 'kicked']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

def get_subscription_keyboard(user_id: int):
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'subscribe_button'), url=CHANNEL_LINK)],
        [InlineKeyboardButton(get_text(user_id, 'check_button'), callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    """Клавиатура выбора языка"""
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
            InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================ ФУНКЦИЯ РАСПОЗНАВАНИЯ МУЗЫКИ ИЗ ВИДЕО ================
async def recognize_music_from_video(file_path: str) -> Optional[str]:
    """
    Извлекает аудио из видео и отправляет в AudD API для распознавания
    """
    try:
        # Создаем временный файл для аудио
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_audio:
            audio_path = tmp_audio.name
        
        # Проверяем наличие ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg не установлен")
            return None
        
        # Извлекаем аудио с помощью ffmpeg
        cmd = [
            'ffmpeg', '-i', file_path,
            '-vn', '-acodec', 'libmp3lame',
            '-ab', '128k', '-ar', '44100',
            '-y', audio_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            logger.error("FFmpeg error")
            return None
        
        # Отправляем в AudD API
        with open(audio_path, 'rb') as f:
            files = {'file': f}
            data = {'api_token': AUDD_API_KEY, 'return': 'apple_music,spotify'}
            
            response = requests.post(
                'https://api.audd.io/recognize',
                files=files,
                data=data,
                timeout=30
            )
            
            # Удаляем временный файл
            try:
                os.unlink(audio_path)
            except:
                pass
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' and result.get('result'):
                    track = result['result']
                    return f"{track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error recognizing music: {e}")
        return None

# ================ ОБРАБОТЧИК КОМАНДЫ /START ================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Если язык еще не выбран, предлагаем выбрать
    if user_id not in user_languages:
        await update.message.reply_text(
            TRANSLATIONS['ru']['choose_language'],
            reply_markup=get_language_keyboard()
        )
        return
    
    # Проверяем подписку
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text(
            get_text(user_id, 'subscribe_first'),
            reply_markup=get_subscription_keyboard(user_id)
        )
        return
    
    await update.message.reply_text(get_text(user_id, 'welcome'))

# ================ ОБРАБОТЧИК ВЫБОРА ЯЗЫКА ================
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.replace('lang_', '')
    
    # Сохраняем язык пользователя
    user_languages[user_id] = lang_code
    
    # Проверяем подписку
    if not await check_subscription(user_id, context.bot):
        await query.edit_message_text(
            get_text(user_id, 'subscribe_first'),
            reply_markup=get_subscription_keyboard(user_id)
        )
        return
    
    await query.edit_message_text(get_text(user_id, 'welcome'))

# ================ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем язык
    if user_id not in user_languages:
        await update.message.reply_text(
            TRANSLATIONS['ru']['choose_language'],
            reply_markup=get_language_keyboard()
        )
        return
    
    # Проверяем подписку
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text(
            get_text(user_id, 'subscribe_first'),
            reply_markup=get_subscription_keyboard(user_id)
        )
        return
    
    query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.message.reply_text(get_text(user_id, 'searching', query=query))

# ================ ОБРАБОТЧИК ВИДЕО ================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем язык
    if user_id not in user_languages:
        await update.message.reply_text(
            TRANSLATIONS['ru']['choose_language'],
            reply_markup=get_language_keyboard()
        )
        return
    
    # Проверяем подписку
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text(
            get_text(user_id, 'subscribe_first'),
            reply_markup=get_subscription_keyboard(user_id)
        )
        return
    
    # Отправляем статус
    status_msg = await update.message.reply_text(get_text(user_id, 'processing_video'))
    
    try:
        # Скачиваем видео
        file = await update.message.video.get_file()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_video:
            video_path = tmp_video.name
            await file.download_to_drive(video_path)
        
        # Обновляем статус
        await status_msg.edit_text(get_text(user_id, 'recognizing'))
        
        # Распознаем музыку
        track_title = await recognize_music_from_video(video_path)
        
        # Удаляем временные файлы
        try:
            os.unlink(video_path)
        except:
            pass
        
        if track_title:
            # Создаем клавиатуру для скачивания
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'download'), callback_data=f"download_{track_title}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                get_text(user_id, 'found', title=track_title),
                reply_markup=reply_markup
            )
        else:
            await status_msg.edit_text(get_text(user_id, 'not_found'))
            
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await status_msg.edit_text(get_text(user_id, 'error', error=str(e)))

# ================ ОБРАБОТЧИК КНОПОК ================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "check_sub":
        if await check_subscription(user_id, context.bot):
            await query.edit_message_text(get_text(user_id, 'thanks_subscribe'))
        else:
            await query.edit_message_text(
                get_text(user_id, 'not_subscribed'),
                reply_markup=get_subscription_keyboard(user_id)
            )
    elif query.data.startswith('lang_'):
        await language_callback(update, context)
    elif query.data.startswith('download_'):
        track = query.data.replace('download_', '')
        await query.message.reply_text(f"🔗 Ссылка на скачивание скоро появится!")

# ================ FLASK ДЛЯ RENDER ================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Music Bot with Video Recognition is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_bot():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_callback, pattern="^(lang_|check_sub|download_)"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        
        logger.info("🎵 Музыкальный бот с видео-распознаванием запущен!")
        application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    run_bot()
