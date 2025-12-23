import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import yt_dlp
from urllib.parse import urlparse

# BOT TOKENINGIZ
BOT_TOKEN = "8530648577:AAFrEPqxpM8MNFi6B66azBFIOCks4_anONY"  # <<<< O‘Z TOKENINGIZNI QO‘YING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'continuedl': True,
    'merge_output_format': 'mp4',
    'cookiefile': 'cookies.txt',  # Agar cookies.txt bo‘lsa
}

# Start tugmasi uchun keyboard
def get_start_keyboard():
    keyboard = [
        [KeyboardButton("📹 YouTube yuklash")],
        [KeyboardButton("📸 Instagram yuklash")],
        [KeyboardButton("🎵 Audio yuklash")],
        [KeyboardButton("ℹ️ Yordam")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men YouTube va Instagramdan video yuklab beraman 🎥\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_start_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if url == "📹 YouTube yuklash":
        await update.message.reply_text("YouTube havolasini yuboring:")
        return

    if url == "📸 Instagram yuklash":
        await update.message.reply_text("Hozircha Instagram yuklash mavjud emas. Faqat YouTube ishlaydi.")
        return

    if url == "🎵 Audio yuklash":
        await update.message.reply_text("Audio yuklash uchun YouTube havolasini yuboring:")
        return

    if url == "ℹ️ Yordam":
        await update.message.reply_text("Bot haqida ma’lumot: YouTube havolasini yuboring, sifatni tanlang va yuklanadi.")
        return

    if not urlparse(url).scheme:
        return

    if "youtube.com" in url or "youtu.be" in url:
        await show_quality_buttons(update, url)

    else:
        await update.message.reply_text("Faqat YouTube havolasi.")

async def show_quality_buttons(update: Update, url: str):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title', 'Video')
        formats = info.get('formats', [])

        keyboard = []
        available_heights = [144, 240, 360, 480, 720, 1080]

        for height in available_heights:
            has_quality = any(f.get('height') == height and f.get('ext') == 'mp4' and f.get('vcodec') != 'none' for f in formats)
            if has_quality:
                keyboard.append([InlineKeyboardButton(f"{height}p", callback_data=f"{url}|{height}")])

        keyboard.append([InlineKeyboardButton("Audio (mp3)", callback_data=f"{url}|audio")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎬 {title}\n\nTasvir sifatini tanlang:",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f"Xato: {str(e)[:200]}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url, choice = query.data.split('|')

    if choice == "audio":
        await query.edit_message_text("Qo‘shiq yuklanmoqda... 🎵")
        await download_audio(url, query.message)
    else:
        height = int(choice)
        await query.edit_message_text(f"{height}p sifatda yuklanmoqda... ⏳")
        await download_youtube_quality(url, height, query.message)

async def download_youtube_quality(url: str, height: int, message):
    try:
        ydl_opts_quality = ydl_opts.copy()
        ydl_opts_quality['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]'

        with yt_dlp.YoutubeDL(ydl_opts_quality) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await message.reply_video(
            video=open(filename, 'rb'),
            caption=f"🎬 {info.get('title', 'Video')} ({height}p)",
            supports_streaming=True
        )
        os.remove(filename)

    except Exception as e:
        logger.error(e)
        await message.reply_text(f"Xato: {str(e)[:200]}")

async def download_audio(url: str, message):
    try:
        ydl_audio_opts = ydl_opts.copy()
        ydl_audio_opts['format'] = 'bestaudio/best'
        ydl_audio_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

        with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        await message.reply_audio(
            audio=open(filename, 'rb'),
            caption=f"🎵 {info.get('title', 'Qo‘shiq')}"
        )
        os.remove(filename)

    except Exception as e:
        logger.error(e)
        await message.reply_text(f"Xato: {str(e)[:200]}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()