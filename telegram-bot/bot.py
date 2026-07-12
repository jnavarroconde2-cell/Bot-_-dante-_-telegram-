import os
import random
import json
import logging
import aiohttp
from io import BytesIO
from telegram.ext import ApplicationBuilder as A, CommandHandler as C, CallbackQueryHandler, filters as F
from telegram import InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont
import yt_dlp

logging.basicConfig(level=logging.INFO)

T = os.getenv("Token")
os.makedirs("/tmp/downloads", exist_ok=True)
memes_vistos = set()
CATEGORIAS = ["meme", "memes", "dankmemes", "wholesomememes", "programmingmemes", "dogmemes", "catmemes"]
DB_FILE = "/tmp/economia.json"

# --- BASE DE DATOS SIMPLE ---
def cargar_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)
def guardar_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

db = cargar_db()

def get_user(uid):
    if str(uid) not in db: db[str(uid)] = {"balance": 100, "inventario": []}
    return db[str(uid)]

# --- COMANDOS BÁSICOS ---
async def start(u,c):
    caption = (
        "👋 **Hola Soy DANTE** 😈\n\n"
        "**Comandos Disponibles:**\n"
        "`/playaudio nombre` → Buscar música MP3\n"
        "`/video nombre/link` → Buscar/Descargar video\n"
        "`/meme` → Meme random\n"
        "`/gato` → Foto de gato random\n"
        "`/perro` → Foto de perro random\n\n"
        "💙💗 **Team Rem y Ram**"
    )
    foto_url = "https://imgur.com/a/pkG2AUY"
    try:
        await u.message.reply_photo(photo=foto_url, caption=caption, parse_mode='Markdown')
    except Exception:
        await u.message.reply_text(caption, parse_mode='Markdown')

async def help(u,c): await start(u,c)

async def ping(u,c): await u.message.reply_text("Pong! Bot vivo ✅")
async def dado(u,c): await u.message.reply_text(f"🎲 Salió: {random.randint(1,6)}")
async def coin(u,c): await u.message.reply_text(f"🪙 Salió: {random.choice(['Cara','Cruz'])}")
async def chiste(u,c): await u.message.reply_text(random.choice(["¿Qué le dice un techo a otro? Techo de menos","¿Por qué los pájaros no usan twitter? Porque ya tienen facebook"]))
async def frase(u,c): await u.message.reply_text(random.choice(["Cree en ti","El que persevera alcanza","Hoy es tu dia"]))
async def picante(u,c): await u.message.reply_text(random.choice(["Tus ojos me prenden 🔥","Eres un peligro"]))
async def bola8(u,c): await u.message.reply_text(f"🎱 {random.choice(['Si','No','Tal vez','Pregunta despues'])}")
async def calcular(u,c):
    expr = " ".join(c.args) if c.args else ""
    allowed = set("0123456789+-*/.() ")
    if not expr or not all(ch in allowed for ch in expr):
        return await u.message.reply_text("Usa: /calcular 2+2  (solo números y operadores básicos)")
    try: await u.message.reply_text(f"Resultado: {eval(expr, {'__builtins__': {}}, {})}")
    except: await u.message.reply_text("Expresión inválida")
async def ppt(u,c):
    opciones = ["piedra","papel","tijera"]
    bot = random.choice(opciones)
    user = c.args[0].lower() if c.args else ""
    if user not in opciones: return await u.message.reply_text("Usa: /ppt piedra|papel|tijera")
    res = "Empate" if user==bot else "Ganaste" if (user=="piedra" and bot=="tijera") or (user=="papel" and bot=="piedra") or (user=="tijera" and bot=="papel") else "Perdiste"
    await u.message.reply_text(f"Tú: {user} | Yo: {bot}\n{res}")

# --- DIVERSIÓN ---
async def ship(u,c): await u.message.reply_text(f"💘 Compatibilidad: {random.randint(1,100)}%")
async def cun(u,c): await u.message.reply_text(f"Tu % de cun: {random.randint(1,100)}%")
async def preniar(u,c): await u.message.reply_text(f"Hoy preño a: @{random.choice(['usuario1','usuario2','tu crush'])}")
async def sorteo(u,c): await u.message.reply_text(f"🎉 Ganador del sorteo: @{random.choice(['user1','user2'])}")
async def enviar_meme(c, categoria, chat_id):
    msg = await c.bot.send_message(chat_id=chat_id, text=f"Buscando meme de r/{categoria} 😂 ⏳")

    for _ in range(10):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://meme-api.com/gimme/{categoria}") as resp:
                data = await resp.json()
                meme_id = data.get("postLink")
                if meme_id and meme_id not in memes_vistos:
                    memes_vistos.add(meme_id)
                    if len(memes_vistos) > 200:
                        memes_vistos.pop()
                    keyboard = [[InlineKeyboardButton("➡️ Siguiente meme", callback_data=f"nextmeme_{categoria}")]]
                    await msg.delete()
                    await c.bot.send_photo(
                        chat_id=chat_id,
                        photo=data["url"],
                        caption=f"🤣 {data['title']}\n👍 {data['ups']} upvotes | r/{data['subreddit']}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    return

    await msg.edit_text("❌ Me quedé sin memes nuevos. Prueba: /meme programación")

async def meme(u,c):
    categoria = c.args[0] if c.args else random.choice(CATEGORIAS)
    await enviar_meme(c, categoria, u.message.chat_id)

async def next_meme_handler(u, c):
    query = u.callback_query
    await query.answer()
    categoria = query.data.split("_")[1]
    await query.message.delete()
    await enviar_meme(c, categoria, query.message.chat_id)

async def gato(u,c):
    msg = await u.message.reply_text("Buscando michi 🐱 ⏳")
    async with aiohttp.ClientSession() as session:
        async with session.get("https://cataas.com/cat?json=true") as resp:
            data = await resp.json()
            url = f"https://cataas.com{data['url']}"
    await msg.delete()
    await u.message.reply_photo(photo=url, caption="😼 Otro michi para ti")

async def perro(u,c):
    msg = await u.message.reply_text("Buscando perrito 🐶 ⏳")
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
            data = await resp.json()
    await msg.delete()
    await u.message.reply_photo(photo=data["message"], caption="🐕 Woof! Aquí tienes")
async def stickerpreniar(u,c): await u.message.reply_text("Waifu embarazada sticker ✨ proximamente")

# --- STICKER ---
async def sticker(u,c):
    if not u.message.reply_to_message:
        return await u.message.reply_text("❌ Responde a una foto con `/sticker texto redondo emoji`", parse_mode="Markdown")

    msg = u.message.reply_to_message
    args = c.args

    texto = ""
    redondo = False
    emoji = ""

    for arg in args:
        if arg.lower() == "redondo":
            redondo = True
        elif any(char in arg for char in "😀😂😎❤️😭🥵👑🔥💀✨😃"):
            emoji = arg
        else:
            texto += arg + " "
    texto = texto.strip()

    await u.message.reply_text("⏳ Haciendo sticker...")

    if msg.photo: file = await msg.photo[-1].get_file()
    elif msg.animation: file = await msg.animation.get_file()
    elif msg.video:
        if msg.video.duration > 3: return await u.message.reply_text("❌ Max 3 segundos")
        file = await msg.video.get_file()
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/"):
        file = await msg.document.get_file()
    else: return await u.message.reply_text("❌ Solo foto, gif, video < 3s")

    file_bytes = BytesIO()
    await file.download_to_memory(out=file_bytes)
    file_bytes.seek(0)

    try:
        img = Image.open(file_bytes).convert("RGBA")
        img.thumbnail((500, 500), Image.LANCZOS)

        # Borde blanco
        borde = Image.new("RGBA", (img.width + 12, img.height + 12), (255, 255, 255, 255))
        borde.paste(img, (6, 6), img)
        img = borde

        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

        if redondo:
            mask = Image.new("L", (512, 512), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 512, 512), fill=255)
            canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)
            canvas.putalpha(mask)
        else:
            canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)

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
            for adj in [-2, -1, 0, 1, 2]:
                draw.text((x + adj, y + adj), final_text, font=font, fill="black")
            draw.text((x, y), final_text, font=font, fill="white")

        output = BytesIO()
        canvas.save(output, format="WEBP")
        output.seek(0)
        await u.message.reply_sticker(sticker=output)
        await u.message.reply_text("✅ Listo rey 😎")

    except Exception as e:
        logging.exception("sticker error")
        await u.message.reply_text(f"❌ Error: {e}")

# --- MEDIA ---
async def yts(u,c):
    if not c.args: return await u.message.reply_text("Usa: /yts nombre")
    await u.message.reply_text(f"Buscando: {' '.join(c.args)} en YouTube...")

async def playaudio(u,c):
    if not c.args:
        await u.message.reply_text("Usa: /playaudio nombre de la canción")
        return

    query = " ".join(c.args)
    msg = await u.message.reply_text(f"Buscando opciones de: {query} ⏳")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch5',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']

        keyboard = []
        for i, video in enumerate(videos[:5]):
            title = video['title']
            keyboard.append([InlineKeyboardButton(f"{i+1}. {title[:50]}", callback_data=f"dl_{video['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(f"Elige una opción para: *{query}*", reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logging.exception("playaudio error")
        await msg.edit_text(f"❌ Error buscando: {e}")


async def button_handler(u,c):
    query = u.callback_query
    await query.answer()
    data = query.data.split("_")

    if data[0] == "dl": tipo = "audio"
    elif data[0] == "vdl": tipo = "video"
    else: return

    video_id = data[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    await query.edit_message_text(f"Descargando {tipo} ⏳")

    if tipo == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/file.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
        }
        ext = 'mp3'
    else:
        ydl_opts = {
            'format': 'best[height<=480]',
            'outtmpl': '/tmp/file.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
        }
        ext = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', tipo.capitalize())
            duration = info.get('duration', 0)

        filesize = os.path.getsize(f'/tmp/file.{ext}')
        if tipo == "video" and filesize > 50 * 1024 * 1024:
            os.remove(f'/tmp/file.{ext}')
            await query.edit_message_text(url)
            return

        await query.edit_message_text(f"✅ Subiendo: {title}")

        if tipo == "audio":
            artist = info.get('uploader', 'Artista desconocido')
            await c.bot.send_audio(chat_id=query.message.chat_id, audio=open(f'/tmp/file.{ext}', 'rb'), title=title, performer=artist, duration=duration)
        else:
            await c.bot.send_video(chat_id=query.message.chat_id, video=open(f'/tmp/file.{ext}', 'rb'), caption=f"📹 {title}", duration=duration, supports_streaming=True)

        os.remove(f'/tmp/file.{ext}')

    except Exception as e:
        logging.exception("button_handler error")
        await query.edit_message_text(f"❌ Error: {e}")

async def video(u,c):
    if not c.args:
        await u.message.reply_text("Usa: /video link o /video nombre del video")
        return

    query = " ".join(c.args)
    msg = await u.message.reply_text(f"Buscando opciones de: {query} ⏳")

    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']

        keyboard = []
        for i, v in enumerate(videos[:5]):
            title = v['title'][:40]
            duration = v.get('duration', 0)
            mins, secs = divmod(duration, 60)
            size_mb = round(v.get('filesize_approx', 0) / 1024 / 1024)
            label = f"{i+1}. {title} [{mins}:{secs:02d}]" + (f" ~{size_mb}MB" if size_mb else "")
            keyboard.append([InlineKeyboardButton(label, callback_data=f"vdl_{v['id']}")])

        await msg.edit_text(f"Elige un video para: *{query}*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    except Exception as e:
        logging.exception("video error")
        await msg.edit_text(f"❌ Error buscando: {e}")

async def ytmp3(u,c): await playaudio(u,c)

# --- ECONOMÍA ---
async def balance(u,c):
    user = get_user(u.effective_user.id)
    await u.message.reply_text(f"💰 Tu balance: {user['balance']} monedas")

async def trabajar(u,c):
    user = get_user(u.effective_user.id)
    ganancia = random.randint(10,50)
    user['balance'] += ganancia; guardar_db(db)
    await u.message.reply_text(f"Trabajaste y ganaste {ganancia} monedas!")

async def diario(u,c):
    user = get_user(u.effective_user.id)
    user['balance'] += 100; guardar_db(db)
    await u.message.reply_text("Reclamaste tu recompensa diaria: 100 monedas!")

async def robar(u,c):
    user = get_user(u.effective_user.id)
    robo = random.randint(5,30)
    user['balance'] += robo; guardar_db(db)
    await u.message.reply_text(f"Robaste {robo} monedas! 😈")

async def tiendaeco(u,c): await u.message.reply_text("Tienda: 1. Espada - 500\n2. Escudo - 300")
async def gacha(u,c): await u.message.reply_text(f"Te tocó: {random.choice(['Común','Raro','Épico','Legendario'])}")
async def inventario(u,c):
    user = get_user(u.effective_user.id)
    await u.message.reply_text(f"Inventario: {user['inventario']}")

# --- ADMIN ---
async def kick(u,c): await u.message.reply_text("Kickeado... necesitas darme admin")
async def ban(u,c): await u.message.reply_text("Baneado... necesitas darme admin")
async def warn(u,c): await u.message.reply_text("Advertencia enviada ⚠️")
async def link(u,c): await u.message.reply_text("Link del grupo: pide a un admin")

# --- SHOP / IA ---
async def premium(u,c): await u.message.reply_text("VIP: 10 soles al mes. Contacta a /soporte")
async def tienda(u,c): await u.message.reply_text("Tienda de productos: Proximamente")
async def soporte(u,c): await u.message.reply_text("Habla con @tu_usuario para soporte humano")
async def imagine(u,c): await u.message.reply_text("Generar imagen con IA: Necesitas API Key. Te ayudo a ponerla")

# --- REGISTRO ---
app = A().token(T).build()

CMDS = {
    "start": start, "help": help, "ping": ping, "dado": dado, "coin": coin,
    "chiste": chiste, "frase": frase, "picante": picante, "bola8": bola8,
    "calcular": calcular, "ppt": ppt, "ship": ship, "cun": cun, "preniar": preniar,
    "sorteo": sorteo, "meme": meme, "gato": gato, "perro": perro,
    "stickerpreniar": stickerpreniar, "sticker": sticker,
    "yts": yts, "playaudio": playaudio, "video": video, "ytmp3": ytmp3,
    "balance": balance, "trabajar": trabajar, "diario": diario, "robar": robar,
    "tiendaeco": tiendaeco, "gacha": gacha, "inventario": inventario,
    "kick": kick, "ban": ban, "warn": warn, "link": link,
    "premium": premium, "tienda": tienda, "soporte": soporte, "imagine": imagine,
}

for cmd, fn in CMDS.items():
    app.add_handler(C(cmd, fn))

app.add_handler(CallbackQueryHandler(next_meme_handler, pattern="^nextmeme_"))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(dl_|vdl_)"))

print(f"Bot DANTE iniciado con {len(CMDS)} comandos")
app.run_polling()
