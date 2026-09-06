import os
import uuid
import glob
import subprocess
import yt_dlp

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


keyboard = [
    ["🎬 دانلود ویدئو"],
    ["🎵 استخراج موسیقی"]
]

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "ربات دانلود اینستاگرام آماده است.\n\n"
        "نوع دانلود را انتخاب کنید:",
        reply_markup=reply_markup
    )


def download_audio(url):
    uid = uuid.uuid4().hex
    filename = f"audio_{uid}"

    options = {
        "outtmpl": filename + ".%(ext)s",
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "retries": 2,
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    downloaded_files = glob.glob(filename + ".*")

    if not downloaded_files:
        raise Exception("فایل دانلود نشد")

    src_file = downloaded_files[0]
    mp3_file = filename + ".mp3"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", src_file,
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", "128k",
            mp3_file
        ],
        check=True,
        capture_output=True
    )

    if os.path.exists(src_file) and src_file != mp3_file:
        os.remove(src_file)

    if not os.path.exists(mp3_file):
        raise Exception("فایل صوتی ساخته نشد")

    return mp3_file


def download_video(url):
    uid = uuid.uuid4().hex
    filename = f"video_{uid}"

    options = {
        "outtmpl": filename + ".%(ext)s",
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "retries": 2,
        "socket_timeout": 30
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    files = glob.glob(filename + ".*")

    if not files:
        raise Exception("فایل ویدئو ساخته نشد")

    return files[0]


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎵 استخراج موسیقی":
        context.user_data["mode"] = "audio"
        await update.message.reply_text(
            "لینک اینستاگرام را ارسال کنید 🎵"
        )
        return

    if text == "🎬 دانلود ویدئو":
        context.user_data["mode"] = "video"
        await update.message.reply_text(
            "لینک اینستاگرام را ارسال کنید 🎬"
        )
        return

    if "instagram.com" not in text:
        await update.message.reply_text(
            "❌ لینک اینستاگرام ارسال کنید"
        )
        return
