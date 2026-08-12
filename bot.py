import os
import asyncio
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import yt_dlp


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات دانلود از اینستاگرام خوش آمدید.\n\n"
        "لینک ویدئو، ریلز یا پست اینستاگرام را ارسال کنید."
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    print("MESSAGE RECEIVED:", text, flush=True)

    if "instagram.com" not in text:
        await update.message.reply_text(
            "❌ لطفاً یک لینک معتبر از اینستاگرام ارسال کنید."
        )
        return

    context.user_data["instagram_url"] = text

    keyboard = [
        [
            InlineKeyboardButton(
                "🎬 دانلود ویدئو",
                callback_data="download_video"
            ),
            InlineKeyboardButton(
                "🎵 استخراج موزیک MP3",
                callback_data="download_audio"
            ),
        ]
    ]

    await update.message.reply_text(
        "لینک دریافت شد ✅\n\n"
        "انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    url = context.user_data.get("instagram_url")

    if not url:
        await query.edit_message_text(
            "❌ لینک پیدا نشد.\n"
            "لطفاً دوباره لینک اینستاگرام را ارسال کنید."
        )
        return

    if query.data == "download_video":
        await download_video(query, url)

    elif query.data == "download_audio":
        await download_audio(query, url)


async def download_video(query, url):
    filename = None

    try:
        await query.edit_message_text(
            "⏳ در حال دانلود ویدئو..."
        )

        loop = asyncio.get_running_loop()

        def download():
            nonlocal filename

            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": "%(id)s.%(ext)s",
                "noplaylist": True,
                "quiet": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True
                )

                filename = ydl.prepare_filename(info)

        await loop.run_in_executor(None, download)

        if not filename or not os.path.exists(filename):
            raise Exception("Video file not found")

        await query.edit_message_text(
            "✅ ویدئو دانلود شد.\n"
            "در حال ارسال..."
        )

        with open(filename, "rb") as video:
            await query.message.reply_video(
                video=video,
                caption="🎬 ویدئو با موفقیت دانلود شد."
            )

        print("VIDEO SENT", flush=True)

    except Exception as e:
        print("VIDEO ERROR:", repr(e), flush=True)

        await query.edit_message_text(
            "❌ دانلود ویدئو انجام نشد."
        )

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass


async def download_audio(query, url):
    source_file = None
    mp3_file = None

    try:
        await query.edit_message_text(
            "⏳ در حال استخراج موزیک..."
        )

        loop = asyncio.get_running_loop()

        def download():
            nonlocal source_file

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "%(id)s.%(ext)s",
                "noplaylist": True,
                "quiet": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True
                )

                source_file = ydl.prepare_filename(info)

        await loop.run_in_executor(None, download)

        if not source_file or not os.path.exists(source_file):
            raise Exception("Audio file not found")

        mp3_file = os.path.splitext(source_file)[0] + ".mp3"

        await query.edit_message_text(
            "🎵 صدا دریافت شد.\n"
            "در حال تبدیل به MP3..."
        )

        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            source_file,
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            mp3_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(
                "FFMPEG ERROR:",
                stderr.decode(errors="ignore"),
                flush=True
            )
            raise Exception("FFmpeg conversion failed")

        if not os.path.exists(mp3_file):
            raise Exception("MP3 file not found")

        await query.edit_message_text(
            "✅ MP3 آماده شد.\n"
            "در حال ارسال..."
        )

        with open(mp3_file, "rb") as audio:
            await query.message.reply_audio(
                audio=audio,
                filename="Instagram_Audio.mp3",
                title="Instagram Audio",
                caption="🎵 موزیک با موفقیت استخراج شد."
            )

        print("MP3 SENT", flush=True)

    except Exception as e:
        print("AUDIO ERROR:", repr(e), flush=True)

        await query.edit_message_text(
            "❌ استخراج موزیک انجام نشد."
        )

    finally:
        for file in (source_file, mp3_file):
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass


def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN not found in .env", flush=True)
        return

    print("TOKEN FOUND", flush=True)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("Bot started", flush=True)

    app.run_polling()


if __name__ == "__main__":
    main()
