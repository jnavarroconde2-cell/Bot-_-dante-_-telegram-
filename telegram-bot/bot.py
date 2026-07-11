import os
import random
import logging

import requests
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Soy DANTE 👑 Escribe /help para ver todo")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/premium – Comprar VIP\n"
        "/playaudio <nombre> – Descargar canción\n"
        "/tienda – Ver precios\n"
        "/meme – Meme random\n"
        "/soporte – Contacto\n"
        "/cun – % de CUN 😈\n"
        "/preñar – Sorpresa 🤰\n"
        "/imagine <prompt> – Imagen IA (próximamente)\n"
        "/calcular <expresión> – Calculadora"
    )


async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /playaudio nombre de la canción")
    nombre = " ".join(context.args)
    await update.message.reply_text(f"Buscando {nombre}... ⏳")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{nombre}", download=True)
            entry = info["entries"][0]
            filename = ydl.prepare_filename(entry)
            # After postprocessing the extension changes to .mp3
            mp3_path = os.path.splitext(filename)[0] + ".mp3"

        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                title=entry.get("title", nombre),
            )
        os.remove(mp3_path)
    except Exception as e:
        logging.exception("playaudio error")
        await update.message.reply_text("No encontré esa canción 😢")


async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buscando meme... 😂")
    try:
        r = requests.get("https://meme-api.com/gimme", timeout=10).json()
        await update.message.reply_photo(photo=r["url"], caption=r["title"])
    except Exception:
        await update.message.reply_text("No pude traer el meme ahora 😢")


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 VIP $5 soles\nYapea 999-999-999 y manda captura")


async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛒 TIENDA:\nAudios $1 | Stickers $1 | VIP $5")


async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Soporte: 999-999-999")


async def cun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Tienes {random.randint(1, 100)}% de CUN 😈")


async def prenar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    victima = random.choice(["a tu ex", "al admin", "a tu crush", "a tu vecina"])
    await update.message.reply_text(f"Hoy voy a preñar {victima} 🤰")


async def imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /imagine un gato astronauta")
    await update.message.reply_text("🎨 Generación de imágenes próximamente...")


async def calcular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /calcular 2 + 2")
    expr = " ".join(context.args)
    try:
        # Only allow safe math expressions
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expr):
            raise ValueError("Caracteres no permitidos")
        resultado = eval(expr, {"__builtins__": {}})
        await update.message.reply_text(f"🧮 {expr} = {resultado}")
    except Exception:
        await update.message.reply_text("Expresión inválida. Ejemplo: /calcular 10 * 3")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(token).build()

    handlers = [
        ("start", start),
        ("help", help_cmd),
        ("playaudio", playaudio),
        ("meme", meme),
        ("premium", premium),
        ("tienda", tienda),
        ("soporte", soporte),
        ("cun", cun),
        ("prenar", prenar),
        ("imagine", imagine),
        ("calcular", calcular),
    ]

    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    app.run_polling()


if __name__ == "__main__":
    main()
