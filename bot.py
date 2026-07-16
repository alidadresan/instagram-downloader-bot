import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "به ربات دانلود از اینستاگرام خوش آمدید.\n\n"
        "لینک ویدئو، ریلز یا پست اینستاگرام را ارسال کنید."
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text(
        "⏳ لینک شما دریافت شد.\n"
        "در حال آماده‌سازی دانلود..."
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    print("Bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
