import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Soy DANTE 👑 ¿En qué te ayudo? Usa /help")


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 VIP $5 soles\nYapea 999-999-999 y manda captura")


async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mándame el nombre de la canción 🎵")


async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tienda: Audios $1 | Stickers $1 | VIP $5")


async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Toma tu meme 😂")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/premium - Comprar VIP\n"
        "/playaudio - Pedir música\n"
        "/tienda - Ver precios\n"
        "/meme - Meme random"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", ayuda))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("playaudio", playaudio))
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("meme", meme))

    app.run_polling()


if __name__ == "__main__":
    main()
