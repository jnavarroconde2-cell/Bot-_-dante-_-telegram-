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
    await update.message.reply_text("👑 DANTE BOT ON\nEscribe /help para ver todo")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👑 *COMANDOS DANTE BOT* 👑\n\n"
        "*Básicos*\n"
        "/start \\- Iniciar el bot\n"
        "/ping \\- Ver si el bot está vivo\n\n"
        "*Música*\n"
        "/playaudio nombre \\- Pedir cualquier música\n\n"
        "*Entretenimiento*\n"
        "/cun \\- Te dice tu % de cun 😈\n"
        "/preniar \\- A quién preña hoy 🤰\n"
        "/meme \\- Te manda un meme\n"
        "/imagine texto \\- Generar imagen con IA\n"
        "/calcular operacion \\- Hacer cuentas\n"
        "/frase \\- Frase motivacional random\n"
        "/chiste \\- Chiste random\n"
        "/bola8 pregunta \\- Bola mágica 🎱\n"
        "/dado \\- Lanza un dado 🎲\n\n"
        "*Negocio*\n"
        "/premium \\- Comprar VIP\n"
        "/tienda \\- Ver productos\n"
        "/soporte \\- Hablar con humano"
    )
    await update.message.reply_text(texto, parse_mode="MarkdownV2")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PONG 🏓 El bot está vivo")


async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(
            "Usa: /playaudio nombre de la canción\nEjemplo: /playaudio pixel ping slowed"
        )

    nombre = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Buscando: {nombre}... ⏳")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/song.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{nombre}", download=True)
            entry = info["entries"][0]
            titulo = entry["title"]

        mp3_path = "/tmp/song.mp3"
        await msg.delete()
        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                title=titulo,
                caption=f"🎵 {titulo}",
            )
        os.remove(mp3_path)
    except Exception:
        logging.exception("playaudio error")
        await msg.edit_text("😢 No encontré esa canción. Prueba con menos palabras")


async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://meme-api.com/gimme", timeout=10).json()
        await update.message.reply_photo(photo=r["url"], caption=r["title"])
    except Exception:
        await update.message.reply_text("No pude traer el meme ahora 😢")


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 COMPRAR VIP $5\n\n"
        "Beneficios:\n"
        "- Música ilimitada\n"
        "- Sin anuncios\n"
        "- Prioridad en soporte\n\n"
        "Yapea 999-999-999 y manda captura"
    )


async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 VER PRODUCTOS\n\nAudios $1 c/u\nVIP Mensual $5\nYapea 999-999-999"
    )


async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 HABLAR CON HUMANO\n\nWhatsApp: 999-999-999\nHorario: 9am - 10pm"
    )


async def frase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frases = [
        "No me llores, facturame",
        "Si no suma, resta",
        "Modo avión activado",
        "Dios proveerá",
        "El que persevera alcanza",
        "Arriba los que luchan",
        "La envidia es de los mediocres",
    ]
    await update.message.reply_text(f"💬 {random.choice(frases)}")


async def chiste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chistes = [
        "¿Qué le dice un techo a otro? Techo de menos",
        "¿Qué hace una abeja en el baño? Zum-bido",
        "¿Por qué las focas miran al cielo? Por las focas",
        "¿Cómo se llama el campeón de buceo? Agustín",
        "¿Qué le dice una iguana a su hermana gemela? Somos iguanas",
    ]
    await update.message.reply_text(f"😂 {random.choice(chistes)}")


async def bola8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /bola8 ¿pasará algo?")
    respuestas = ["Sí", "No", "Tal vez", "Definitivamente", "Pregunta después", "Las señales dicen no", "Todo indica que sí"]
    await update.message.reply_text(f"🎱 {random.choice(respuestas)}")


async def dado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎲 Te salió: {random.randint(1, 6)}")


async def cun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Tu CUN: {random.randint(1, 100)}% 😈")


async def preniar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    victima = random.choice(["tu ex", "al admin", "a tu crush", "al grupo"])
    await update.message.reply_text(f"Hoy preño a {victima} 🤰")


async def imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /imagine un gato astronauta")
    await update.message.reply_text("🎨 Imagen con IA aún en desarrollo... próximamente")


async def calcular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /calcular 10 * 3 + 2")
    expr = " ".join(context.args)
    try:
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
        ("ping", ping),
        ("playaudio", playaudio),
        ("meme", meme),
        ("premium", premium),
        ("tienda", tienda),
        ("soporte", soporte),
        ("frase", frase),
        ("chiste", chiste),
        ("bola8", bola8),
        ("dado", dado),
        ("cun", cun),
        ("preniar", preniar),
        ("imagine", imagine),
        ("calcular", calcular),
    ]

    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    app.run_polling()


if __name__ == "__main__":
    main()
