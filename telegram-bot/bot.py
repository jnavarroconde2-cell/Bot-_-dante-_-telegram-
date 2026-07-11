import os
import json
import random
import logging
import time
from io import BytesIO

import requests
import yt_dlp
from PIL import Image
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

ARCHIVO = "/tmp/economia.json"

TIENDA_ITEMS = {
    "espada":  {"precio": 500,  "desc": "⚔️ Espada del robo +20%"},
    "escudo":  {"precio": 400,  "desc": "🛡️ Escudo anti-robo"},
    "amuleto": {"precio": 300,  "desc": "🧿 Amuleto de la suerte"},
    "varita":  {"precio": 600,  "desc": "🪄 Varita mágica"},
    "corona":  {"precio": 1000, "desc": "👑 Corona de DANTE"},
}

GACHA_PREMIOS = [
    ("💎 Diamante", 2000),
    ("⭐ Estrella",   800),
    ("🎖️ Medalla",   500),
    ("🍀 Trébol",    300),
    ("🪨 Piedra",     50),
]
GACHA_PESO = [5, 15, 25, 30, 25]


# ─── Economía helpers ──────────────────────────────────────────────────────────

def cargar_datos() -> dict:
    try:
        with open(ARCHIVO, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_datos(data: dict):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f)


def get_user(data: dict, uid: str) -> dict:
    if uid not in data:
        data[uid] = {"dinero": 100, "items": [], "trabajo_ts": 0, "diario_ts": 0, "warns": 0}
    return data[uid]


# ─── Admin helper ─────────────────────────────────────────────────────────────

async def es_admin(update: Update) -> bool:
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception:
        return False


# ─── Básicos ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 DANTE BOT ON\nEscribe /help para ver todo")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👑 COMANDOS DANTE BOT 👑\n\n"
        "📌 Básicos\n"
        "/start  /ping  /help\n\n"
        "🎵 Música\n"
        "/playaudio nombre — busca y elige con botones\n\n"
        "📥 Descargas\n"
        "/video link — descargar video YouTube\n"
        "/ytmp3 link — descargar audio MP3\n"
        "/yts nombre — buscar videos\n\n"
        "🎮 Entretenimiento\n"
        "/cun  /preniar  /meme  /picante\n"
        "/frase  /chiste  /dado  /coin\n"
        "/bola8 pregunta\n"
        "/ship @p1 @p2\n"
        "/ppt piedra|papel|tijera\n"
        "/sorteo  /gato  /perro\n"
        "/calcular operacion\n\n"
        "💰 Economía\n"
        "/balance  /trabajar  /diario\n"
        "/robar (responde un mensaje)\n"
        "/tiendaeco  /comprar item\n"
        "/inventario  /gacha\n\n"
        "🔒 Solo admins\n"
        "/kick  /ban  /warn  /link\n\n"
        "🛒 Negocio\n"
        "/premium  /tienda  /soporte"
    )
    await update.message.reply_text(texto)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PONG 🏓 El bot está vivo")


# ─── Música con botones inline ────────────────────────────────────────────────

async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /playaudio nombre de la canción")
    nombre = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Buscando: {nombre}... ⏳")
    try:
        ydl_opts = {"quiet": True, "noplaylist": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{nombre}", download=False)

        teclado = []
        for i, entry in enumerate(info["entries"]):
            titulo = (entry.get("title") or "Sin título")[:45]
            dur = entry.get("duration") or 0
            mins, secs = divmod(int(dur), 60)
            btn = InlineKeyboardButton(
                f"{i+1}. {titulo} ({mins}:{secs:02d})",
                callback_data=f"play_{entry['id']}",
            )
            teclado.append([btn])

        await msg.edit_text("🎵 Elige una canción:", reply_markup=InlineKeyboardMarkup(teclado))
    except Exception:
        logging.exception("playaudio error")
        await msg.edit_text("😢 No encontré nada. Intenta con otro nombre")


async def boton_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_id = query.data.split("_", 1)[1]
    link = f"https://www.youtube.com/watch?v={video_id}"
    await query.edit_message_text("📥 Descargando audio... ⏳")
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/song.%(ext)s",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            titulo = info.get("title", "Audio")

        with open("/tmp/song.mp3", "rb") as f:
            await query.message.reply_audio(audio=f, title=titulo, caption=f"🎵 {titulo}")
        os.remove("/tmp/song.mp3")
        await query.edit_message_text(f"✅ Enviado: {titulo}")
    except Exception:
        logging.exception("boton_play error")
        await query.edit_message_text("😢 Error al descargar. Intenta con otra canción")


# ─── Descargas ────────────────────────────────────────────────────────────────

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /video https://youtube.com/watch?v=...")
    link = context.args[0]
    msg = await update.message.reply_text("📥 Descargando video... ⏳ (puede tardar)")
    try:
        ydl_opts = {
            "format": "mp4[height<=720]/best[height<=720]/best",
            "outtmpl": "/tmp/video.%(ext)s",
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            titulo = info.get("title", "Video")
            filename = ydl.prepare_filename(info)

        # Find the downloaded file
        base = os.path.splitext(filename)[0]
        for ext in ["mp4", "mkv", "webm"]:
            path = f"{base}.{ext}" if not filename.endswith(ext) else filename
            if os.path.exists(path):
                break

        await msg.delete()
        with open(path, "rb") as f:
            await update.message.reply_video(video=f, caption=f"🎬 {titulo}", supports_streaming=True)
        os.remove(path)
    except Exception:
        logging.exception("video error")
        await msg.edit_text("😢 No pude descargar. El video puede ser muy largo o estar restringido")


async def ytmp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /ytmp3 https://youtube.com/watch?v=...")
    link = context.args[0]
    msg = await update.message.reply_text("🎵 Convirtiendo a MP3... ⏳")
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/audio.%(ext)s",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            titulo = info.get("title", "Audio")

        await msg.delete()
        with open("/tmp/audio.mp3", "rb") as f:
            await update.message.reply_audio(audio=f, title=titulo, caption=f"🎵 {titulo}")
        os.remove("/tmp/audio.mp3")
    except Exception:
        logging.exception("ytmp3 error")
        await msg.edit_text("😢 No pude convertir ese link")


async def yts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /yts nombre de la canción")
    nombre = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Buscando: {nombre}...")
    try:
        ydl_opts = {"quiet": True, "noplaylist": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{nombre}", download=False)

        lines = [f"🔎 Resultados para: {nombre}\n"]
        for i, entry in enumerate(info["entries"]):
            titulo = (entry.get("title") or "Sin título")[:50]
            dur = entry.get("duration") or 0
            mins, secs = divmod(int(dur), 60)
            vid_id = entry["id"]
            lines.append(f"{i+1}. {titulo} ({mins}:{secs:02d})\n   youtube.com/watch?v={vid_id}")

        await msg.edit_text("\n".join(lines))
    except Exception:
        logging.exception("yts error")
        await msg.edit_text("😢 No encontré resultados")


# ─── Entretenimiento ──────────────────────────────────────────────────────────

async def frase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frases = [
        "No me llores, facturame 💸",
        "Si no suma, resta",
        "Modo avión activado ✈️",
        "Dios proveerá 🙏",
        "El que persevera alcanza 🏆",
        "Arriba los que luchan 💪",
        "La envidia es de los mediocres 😎",
    ]
    await update.message.reply_text(f"💬 {random.choice(frases)}")


async def chiste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chistes = [
        "¿Qué le dice un techo a otro? Techo de menos 🏠",
        "¿Qué hace una abeja en el baño? Zum-bido 🐝",
        "¿Por qué las focas miran al cielo? Por las focas 🦭",
        "¿Cómo se llama el campeón de buceo? Agustín 🏊",
        "¿Qué le dice una iguana a su gemela? Somos iguanas 🦎",
    ]
    await update.message.reply_text(f"😂 {random.choice(chistes)}")


async def bola8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /bola8 ¿pasará algo?")
    respuestas = [
        "Sí ✅", "No ❌", "Tal vez 🤔", "Definitivamente 💯",
        "Pregunta después ⏳", "Las señales dicen no 🚫", "Todo indica que sí 🎯",
    ]
    await update.message.reply_text(f"🎱 {random.choice(respuestas)}")


async def dado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎲 Te salió: {random.randint(1, 6)}")


async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 Salió: {random.choice(['Cara 😎', 'Cruz ✝️'])}")


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Usa: /ship @persona1 @persona2")
    pct = random.randint(1, 100)
    emoji = "💘" if pct > 70 else ("💔" if pct < 30 else "💕")
    await update.message.reply_text(f"{emoji} {context.args[0]} x {context.args[1]} = {pct}% compatible")


async def ppt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opciones = ["piedra", "papel", "tijera"]
    bot_elec = random.choice(opciones)
    user_elec = " ".join(context.args).lower()
    if user_elec not in opciones:
        return await update.message.reply_text("Usa: /ppt piedra, papel o tijera")
    if bot_elec == user_elec:
        res = "¡Empate! 🤝"
    elif (
        (user_elec == "piedra" and bot_elec == "tijera")
        or (user_elec == "papel" and bot_elec == "piedra")
        or (user_elec == "tijera" and bot_elec == "papel")
    ):
        res = "¡Ganaste! 🏆"
    else:
        res = "¡Perdiste! 💀"
    await update.message.reply_text(f"Yo saqué {bot_elec}. {res}")


async def sorteo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ganadores = ["Tú 🎉", "El admin 👀", "Alguien del chat 🙈", "Nadie, está arreglado 😂"]
    await update.message.reply_text(f"🎉 El ganador es: {random.choice(ganadores)}")


async def gato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.thecatapi.com/v1/images/search", timeout=10).json()
        await update.message.reply_photo(r[0]["url"], caption="🐱 Miau")
    except Exception:
        await update.message.reply_text("No pude traer el gatito 😢")


async def perro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=10).json()
        await update.message.reply_photo(r["message"], caption="🐶 Guau")
    except Exception:
        await update.message.reply_text("No pude traer el perrito 😢")


async def cun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Tu CUN: {random.randint(1, 100)}% 😈")


async def preniar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waifus = [
        "https://media.giphy.com/media/3o7btPCcdNniyUOyWg/giphy.gif",
        "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "https://media.giphy.com/media/26FPYOZdztQlDbdDG/giphy.gif",
        "https://media.tenor.com/wHkYQ9Q9Q9EAAAAC/anime-belly.gif",
        "https://media.giphy.com/media/L1R1tvI9svkIW/giphy.gif",
    ]
    gif = random.choice(waifus)
    autor = update.effective_user.first_name

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        mention = target.mention_html()
        texto = (
            f"🤰 <b>WAIFU ALERT</b> 🤰\n\n"
            f"{mention} está embarazada de {autor}!!\n"
            f"Ya se viene el bebé uwu"
        )
    elif context.args:
        nombre = context.args[0]
        texto = (
            f"🤰 <b>WAIFU ALERT</b> 🤰\n\n"
            f"{nombre} está embarazada de {autor}!!\n"
            f"Ya se viene el bebé uwu"
        )
    else:
        return await update.message.reply_text("Usa: /preniar @usuario o responde a un mensaje")

    await update.message.reply_animation(animation=gif, caption=texto, parse_mode="HTML")


async def picante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frases = [
        "Eres fuego y yo gasolina 🔥",
        "Cuidado que muerdo 😈",
        "Ven que te cuento un secreto 🤫",
        "Modo diablo activado 😈",
        "Peligroso/a de noche 🌙",
    ]
    await update.message.reply_text(f"🔥 {random.choice(frases)}")


async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://meme-api.com/gimme", timeout=10).json()
        await update.message.reply_photo(photo=r["url"], caption=r["title"])
    except Exception:
        await update.message.reply_text("No pude traer el meme ahora 😢")


async def calcular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /calcular 10 * 3 + 2")
    expr = " ".join(context.args)
    try:
        if not all(c in "0123456789+-*/.() " for c in expr):
            raise ValueError("Caracteres no permitidos")
        resultado = eval(expr, {"__builtins__": {}})
        await update.message.reply_text(f"🧮 {expr} = {resultado}")
    except Exception:
        await update.message.reply_text("Expresión inválida. Ejemplo: /calcular 10 * 3")


async def imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /imagine un gato astronauta")
    await update.message.reply_text("🎨 Imagen con IA próximamente...")


async def sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Responde a una foto con `/sticker texto redondo emoji`", parse_mode="Markdown")

    msg = update.message.reply_to_message
    args = context.args  # lista de palabras

    # Detectar opciones
    texto = ""
    redondo = False
    emoji = ""

    for arg in args:
        if arg.lower() == "redondo":
            redondo = True
        elif arg.startswith(("😀","😂","😎","❤️","😭","🥵","👑","🔥","💀","✨")):
            emoji = arg
        else:
            texto += arg + " "
    texto = texto.strip()

    await update.message.reply_text("⏳ Haciendo sticker...")

    # Detectar archivo
    if msg.photo:
        file = await msg.photo[-1].get_file()
    elif msg.animation:
        file = await msg.animation.get_file()
    elif msg.video:
        if msg.video.duration > 3:
            return await update.message.reply_text("❌ Max 3 segundos")
        file = await msg.video.get_file()
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/"):
        file = await msg.document.get_file()
    else:
        return await update.message.reply_text("❌ Solo foto, gif, video < 3s")

    file_bytes = BytesIO()
    await file.download_to_memory(out=file_bytes)
    file_bytes.seek(0)

    try:
        img = Image.open(file_bytes).convert("RGBA")
        img.thumbnail((500, 500), Image.LANCZOS)

        # BORDE BLANCO
        borde = Image.new("RGBA", (img.width + 12, img.height + 12), (255, 255, 255, 255))
        borde.paste(img, (6, 6), img)
        img = borde

        # CANVAS 512x512
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

        # SI ES REDONDO
        if redondo:
            mask = Image.new("L", (512, 512), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 512, 512), fill=255)
            canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)
            canvas.putalpha(mask)
        else:
            canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)

        # TEXTO + EMOJI ABAJO
        if texto or emoji:
            draw = ImageDraw.Draw(canvas)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
            except Exception:
                font = ImageFont.load_default()

            final_text = f"{texto} {emoji}".strip()
            text_w, text_h = draw.textbbox((0, 0), final_text, font=font)[2:]
            x = 256 - text_w // 2
            y = 512 - text_h - 10

            # Contorno
            for adj in [-2, -1, 0, 1, 2]:
                draw.text((x + adj, y + adj), final_text, font=font, fill="black")
            draw.text((x, y), final_text, font=font, fill="white")

        output = BytesIO()
        canvas.save(output, format="WEBP")
        output.seek(0)

        await update.message.reply_sticker(sticker=output)
        await update.message.reply_text("✅ Listo rey 😎")

    except Exception as e:
        logging.exception("sticker error")
        await update.message.reply_text(f"❌ Error: {e}")


# ─── Economía ─────────────────────────────────────────────────────────────────

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    user = get_user(data, str(update.effective_user.id))
    nombre = update.effective_user.first_name
    items_str = ", ".join(user["items"]) if user["items"] else "ninguno"
    await update.message.reply_text(
        f"💰 Balance de {nombre}\nDinero: ${user['dinero']}\nItems: {items_str}"
    )


COOLDOWN_TRABAJO = 3600

async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    ahora = time.time()
    restante = COOLDOWN_TRABAJO - (ahora - user.get("trabajo_ts", 0))
    if restante > 0:
        mins = int(restante // 60)
        return await update.message.reply_text(f"⏳ Espera {mins} min para volver a trabajar")
    trabajos = ["limpiaste ventanas", "repartiste volantes", "cocinaste", "programaste", "vendiste memes"]
    ganancia = random.randint(50, 300)
    user["dinero"] += ganancia
    user["trabajo_ts"] = ahora
    guardar_datos(data)
    await update.message.reply_text(f"💼 {random.choice(trabajos).capitalize()} y ganaste ${ganancia} 💰")


COOLDOWN_DIARIO = 86400

async def diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    ahora = time.time()
    restante = COOLDOWN_DIARIO - (ahora - user.get("diario_ts", 0))
    if restante > 0:
        horas = int(restante // 3600)
        mins = int((restante % 3600) // 60)
        return await update.message.reply_text(f"⏳ Vuelve en {horas}h {mins}m")
    user["dinero"] += 500
    user["diario_ts"] = ahora
    guardar_datos(data)
    await update.message.reply_text("🎁 Recompensa diaria: +$500 💰")


async def robar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje de quien quieres robar")
    data = cargar_datos()
    ladron_id = str(update.effective_user.id)
    victima_id = str(update.message.reply_to_message.from_user.id)
    if ladron_id == victima_id:
        return await update.message.reply_text("No puedes robarte a ti mismo 😂")
    ladron = get_user(data, ladron_id)
    victima = get_user(data, victima_id)
    if "escudo" in victima.get("items", []):
        return await update.message.reply_text("🛡️ ¡La víctima tiene escudo! El robo falló")
    if victima["dinero"] <= 0:
        return await update.message.reply_text("Esa persona no tiene nada que robar 😂")
    if random.random() < 0.55:
        robo = min(random.randint(20, 150), victima["dinero"])
        if "espada" in ladron.get("items", []):
            robo = int(robo * 1.2)
        victima["dinero"] -= robo
        ladron["dinero"] += robo
        guardar_datos(data)
        nombre_v = update.message.reply_to_message.from_user.first_name
        await update.message.reply_text(f"🦹 ¡Robaste ${robo} a {nombre_v}!")
    else:
        multa = random.randint(20, 80)
        ladron["dinero"] = max(0, ladron["dinero"] - multa)
        guardar_datos(data)
        await update.message.reply_text(f"👮 ¡Te cacharon! Pagas multa de ${multa}")


async def tiendaeco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🛒 TIENDA DEL BOT\n"]
    for item, info in TIENDA_ITEMS.items():
        lines.append(f"{info['desc']} — ${info['precio']}\n/comprar {item}")
    await update.message.reply_text("\n".join(lines))


async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /comprar espada")
    item = context.args[0].lower()
    if item not in TIENDA_ITEMS:
        return await update.message.reply_text(f"Item '{item}' no existe. Ve /tiendaeco")
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    precio = TIENDA_ITEMS[item]["precio"]
    if item in user["items"]:
        return await update.message.reply_text("Ya tienes ese item 🤔")
    if user["dinero"] < precio:
        return await update.message.reply_text(
            f"Sin dinero. Necesitas ${precio}, tienes ${user['dinero']}"
        )
    user["dinero"] -= precio
    user["items"].append(item)
    guardar_datos(data)
    await update.message.reply_text(f"✅ Compraste {TIENDA_ITEMS[item]['desc']} por ${precio}")


async def inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    user = get_user(data, str(update.effective_user.id))
    if not user["items"]:
        return await update.message.reply_text("🎒 Inventario vacío. Compra algo en /tiendaeco")
    lines = ["🎒 TU INVENTARIO\n"] + [TIENDA_ITEMS[i]["desc"] for i in user["items"] if i in TIENDA_ITEMS]
    await update.message.reply_text("\n".join(lines))


async def gacha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    costo = 300
    if user["dinero"] < costo:
        return await update.message.reply_text(
            f"💸 Necesitas ${costo} para gacha. Tienes ${user['dinero']}"
        )
    user["dinero"] -= costo
    nombre_p, valor_p = random.choices(GACHA_PREMIOS, weights=GACHA_PESO, k=1)[0]
    user["dinero"] += valor_p
    guardar_datos(data)
    resultado = "¡GANASTE! 🎉" if valor_p > costo else "Mala suerte... 😢"
    await update.message.reply_text(
        f"🎰 GACHA\nGastaste: ${costo}\nObtuviste: {nombre_p}\nGanaste: ${valor_p}\n{resultado}"
    )


# ─── Admin ────────────────────────────────────────────────────────────────────

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje del usuario a expulsar")
    try:
        user = update.message.reply_to_message.from_user
        await update.effective_chat.ban_member(user.id)
        await update.effective_chat.unban_member(user.id)
        await update.message.reply_text(f"👟 {user.first_name} fue expulsado/a")
    except Exception as e:
        await update.message.reply_text(f"No pude expulsar: {e}")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje del usuario a banear")
    try:
        user = update.message.reply_to_message.from_user
        await update.effective_chat.ban_member(user.id)
        await update.message.reply_text(f"🔨 {user.first_name} fue baneado/a")
    except Exception as e:
        await update.message.reply_text(f"No pude banear: {e}")


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje del usuario a advertir")
    data = cargar_datos()
    uid = str(update.message.reply_to_message.from_user.id)
    user = get_user(data, uid)
    user["warns"] = user.get("warns", 0) + 1
    guardar_datos(data)
    nombre = update.message.reply_to_message.from_user.first_name
    warns = user["warns"]
    await update.message.reply_text(f"⚠️ {nombre} tiene advertencia #{warns}")
    if warns >= 3:
        try:
            await update.effective_chat.ban_member(int(uid))
            await update.message.reply_text(f"🔨 {nombre} baneado/a por {warns} advertencias")
        except Exception:
            pass


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins")
    try:
        inv = await update.effective_chat.create_invite_link()
        await update.message.reply_text(f"🔗 Link del grupo:\n{inv.invite_link}")
    except Exception as e:
        await update.message.reply_text(f"No pude crear el link: {e}")


# ─── Negocio ──────────────────────────────────────────────────────────────────

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 COMPRAR VIP — $5 soles\n\n"
        "Beneficios:\n- Música ilimitada\n- Sin espera en /trabajar\n- Prioridad en soporte\n\n"
        "Yapea 999-999-999 y manda captura"
    )


async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛒 TIENDA\n\nAudios $1 c/u\nVIP Mensual $5\nYapea 999-999-999")


async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 SOPORTE\n\nWhatsApp: 999-999-999\nHorario: 9am — 10pm")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(token).build()

    # Callback para botones inline de música
    app.add_handler(CallbackQueryHandler(boton_play, pattern=r"^play_"))

    handlers = [
        ("start", start), ("help", help_cmd), ("ping", ping),
        # Música y descargas
        ("playaudio", playaudio), ("video", video), ("ytmp3", ytmp3), ("yts", yts),
        # Entretenimiento
        ("frase", frase), ("chiste", chiste), ("bola8", bola8), ("dado", dado),
        ("coin", coin), ("ship", ship), ("ppt", ppt), ("sorteo", sorteo),
        ("gato", gato), ("perro", perro), ("cun", cun), ("preniar", preniar),
        ("picante", picante), ("meme", meme), ("calcular", calcular), ("imagine", imagine), ("sticker", sticker),
        # Economía
        ("balance", balance), ("trabajar", trabajar), ("diario", diario),
        ("robar", robar), ("tiendaeco", tiendaeco), ("comprar", comprar),
        ("inventario", inventario), ("gacha", gacha),
        # Admin
        ("kick", kick), ("ban", ban), ("warn", warn), ("link", link),
        # Negocio
        ("premium", premium), ("tienda", tienda), ("soporte", soporte),
    ]

    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    logging.info("DANTE BOT iniciado ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
