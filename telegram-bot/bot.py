import os
import random
import json
import base64
import hashlib
import glob
import logging
import time
import subprocess
import re
import asyncio
import aiohttp
import sympy
from io import BytesIO
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from openai import OpenAI
from telegram.ext import (
    ApplicationBuilder as A,
    CommandHandler as C,
    CallbackQueryHandler,
    MessageHandler as M,
    filters as F,
)
from telegram import InputFile, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from PIL import Image, ImageDraw, ImageFont
import yt_dlp

logging.basicConfig(level=logging.INFO)

T = os.getenv("Token")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
ELEVENLABS_API_KEY = (
    os.getenv("ELEVENLABS_KEY")
    or os.getenv("ELEVENLABS_API_KEY")
)
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
MATH_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
os.makedirs("/tmp/downloads", exist_ok=True)
SONIDOS_CACHE_FILE = "/tmp/sonidos_cache.json"

def cargar_cache_sonidos():
    try:
        with open(SONIDOS_CACHE_FILE, "r") as f:
            cache = json.load(f)
            return cache if isinstance(cache, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def guardar_cache_sonidos(cache):
    try:
        with open(SONIDOS_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        logging.exception("No se pudo guardar la caché de sonidos")

cache_sonidos = cargar_cache_sonidos()
CATEGORIAS = {
    "random":   ["memes", "dankmemes", "SpanishMemes"],
    "anime":    ["AnimeMemes", "Animemes"],
    "gacha":    ["gachamemes"],
    "otaku":    ["Animemes", "manga"],
    "shitpost": ["shitposting", "dankmemes"],
}
DB_FILE = "/tmp/economia.json"
EXAMS_FILE = "/tmp/examenes.json"


def cargar_examenes():
    try:
        with open(EXAMS_FILE, "r") as f:
            datos = json.load(f)
            return datos if isinstance(datos, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def guardar_examenes(datos):
    try:
        with open(EXAMS_FILE, "w") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        logging.exception("No se pudieron guardar los exámenes")


examenes_guardados = cargar_examenes()

# --- BASE DE DATOS SIMPLE ---
def cargar_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)
def guardar_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

db = cargar_db()

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {"balance": 100, "tickets": 0, "inventario": [], "waifus": [],
                   "racha_daily": 0, "ultimo_daily": 0, "ultimo_daily_coins": 0,
                   "vip": False}
        guardar_db(db)
    user = db[uid]
    # migrar campos viejos
    for k, v in [("tickets", 0), ("waifus", []), ("racha_daily", 0),
                 ("ultimo_daily", 0), ("ultimo_daily_coins", 0), ("vip", False)]:
        user.setdefault(k, v)
    return user

# --- GACHA POOL ---
WAIFUS = {
    "R":    ["Rin - Cat Fantasy","Miyu - Cat Fantasy","Shiro - Cat Fantasy",
             "Nobara Kugisaki - JJK","Maki Zenin - JJK","Miwa - JJK"],
    "SR":   ["Aisha - Cat Fantasy","Yukari - Cat Fantasy","Luna - Cat Fantasy",
             "Megumi Fushiguro - JJK","Kento Nanami - JJK","Toge Inumaki - JJK"],
    "SSR":  ["Lilith - Cat Fantasy","Meia - Cat Fantasy","Nyaru - Cat Fantasy",
             "Satoru Gojo - JJK","Yuta Okkotsu - JJK","Suguru Geto - JJK"],
    "SSSR": ["Mashiro - Cat Fantasy","Selena - Cat Fantasy",
             "Ryomen Sukuna - JJK","Toji Fushiguro - JJK"],
}
EMOJIS_R = {"R": "⚪", "SR": "🔵", "SSR": "🟡", "SSSR": "🌈"}

# --- COMANDOS BÁSICOS ---
async def start(u,c):
    await u.message.reply_text(
        "🤖 DANTE BOT ACTIVO\n\n"
        "/resolver - Resuelve ejercicios paso a paso\n"
        "/examen <tema> - Crea examen + clave al toque\n"
        "/respuestas <área> - Muestra la clave del último examen\n"
        "/explicar <tema> - Explica un tema\n"
        "/meme <tema> - Genera ideas para memes\n"
        "/ttmp3 <enlace> - Extrae audio de TikTok\n"
        "/soporte - Chat con IA\n\n"
        "Usa /help para ver todos los comandos."
    )

async def help(u,c):
    texto = (
        "DANTE BOT - COMANDOS\n"
        "General: /start /help /ping /calcular /resolver /explicar /examen /respuestas /frase /chiste /8ball /dado /coin /ppt /sorteo\n"
        "Diversion: /ship /cun /preniar /stickerpreniar /sticker /meme /picante /gato /perro /imagine\n"
        "Media: /playaudio /video /ytmp3 /yts /tt /ttmp3 /fbmp3 /sonidos /creditos\n"
        "Economia: /balance /trabajar /diario /daily /robar /tiendaeco /tienda /comprar /gacha /tickets /inventario\n"
        "Admin: /kick /ban /warn /link\n"
        "Shop: /premium /tienda /soporte /salirsoporte"
    )
    await u.message.reply_text(texto)

async def ping(u,c): await u.message.reply_text("🏓 Pong! Bot vivo ✅")
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

def es_operacion(texto):
    return bool(re.fullmatch(r"[0-9+\-*/^()×÷.= ]+", texto.strip()))

async def auto_resolver(u, c):
    texto = (u.message.text or "").strip()
    if not texto or not es_operacion(texto):
        return

    texto_limpio = (
        texto.replace("×", "*")
        .replace("÷", "/")
        .replace("^", "**")
    )
    try:
        resultado = parse_expr(
            texto_limpio,
            transformations=MATH_TRANSFORMATIONS,
            evaluate=True,
        )
        resultado = sympy.simplify(resultado)
        await u.message.reply_text(f"「✿」 **{texto} = {resultado}**", parse_mode="Markdown")
    except Exception:
        # Los textos que parecen operaciones, pero no son válidos, se ignoran.
        return

async def resolver(u, c):
    if (
        not c.args
        and u.message.reply_to_message
        and u.message.reply_to_message.photo
    ):
        await resolver_foto(u, c, u.message.reply_to_message)
        return

    if not c.args:
        await u.message.reply_text(
            "「✿」 Uso: `/resolver 2x+5=15`\n\n"
            "También puedes responder a una foto de un ejercicio con /resolver.",
            parse_mode="Markdown",
        )
        return

    try:
        ejercicio = " ".join(c.args).strip()
        msg = await u.message.reply_text("「✿」 ⏳ Resolviendo paso a paso...")
        respuesta = await _ai_completion(
            "Eres un profesor experto en matemáticas. Responde en español, "
            "usa lenguaje sencillo y no inventes datos.",
            (
                "Resuelve correctamente este ejercicio paso a paso:\n"
                f"{ejercicio}\n\n"
                "Comprueba el resultado y usa este formato:\n"
                "🧮 EJERCICIO\n📚 PROCEDIMIENTO\n"
                "Paso 1:\nPaso 2:\nPaso 3:\n✅ RESPUESTA FINAL:"
            ),
            image_bytes=None,
            max_tokens=900,
        )
        await msg.edit_text(respuesta[:3900])
    except Exception:
        logging.exception("resolver IA error")
        await u.message.reply_text("「✿」 No pude resolver ese ejercicio.")


async def resolver_foto(u, c, mensaje_foto):
    estado = await u.message.reply_text("「✿」 ⏳ Analizando la foto...")
    try:
        foto = mensaje_foto.photo[-1]
        archivo = await c.bot.get_file(foto.file_id)
        imagen_bytes = bytes(await archivo.download_as_bytearray())
        respuesta = await _ai_completion(
            "Eres un profesor experto en matemáticas. Responde en español.",
            (
                "Analiza cuidadosamente esta imagen. Lee el ejercicio, identifica "
                "los datos, resuélvelo paso a paso, comprueba el resultado y da "
                "la respuesta final. Si no contiene un ejercicio matemático, "
                "indícalo. No inventes números.\n\n"
                "Formato:\n🧮 EJERCICIO DETECTADO:\n📚 PROCEDIMIENTO:\n"
                "Paso 1:\nPaso 2:\nPaso 3:\n✅ RESPUESTA FINAL:"
            ),
            image_bytes=imagen_bytes,
            max_tokens=1200,
        )
        await estado.edit_text(respuesta[:3900])
    except Exception:
        logging.exception("resolver foto error")
        await estado.edit_text(
            "❌ No pude analizar la foto. Para imágenes necesitas configurar "
            "OPENROUTER_API_KEY."
        )

def _openai_completion(system_prompt, user_prompt, max_tokens):
    if not openai_client:
        raise RuntimeError("OPENAI_API_KEY no está configurada en los secretos")
    response = openai_client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=max_tokens,
    )
    return response.choices[0].message.content or "No recibí una respuesta."


async def _openrouter_completion(system_prompt, user_prompt, image_bytes=None):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY no está configurada")

    contenido = user_prompt
    if image_bytes is not None:
        imagen_base64 = base64.b64encode(image_bytes).decode("ascii")
        contenido = [
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{imagen_base64}",
                },
            },
        ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://replit.com",
        "X-Title": "DANTE Telegram Bot",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": contenido},
        ],
    }
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            OPENROUTER_URL,
            json=payload,
            timeout=timeout,
        ) as response:
            if response.status != 200:
                logging.warning(
                    "OpenRouter respondió HTTP %s",
                    response.status,
                )
                raise RuntimeError(f"OpenRouter HTTP {response.status}")
            datos = await response.json(content_type=None)

    try:
        contenido_respuesta = datos["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Respuesta inválida de OpenRouter") from exc
    if isinstance(contenido_respuesta, list):
        contenido_respuesta = " ".join(
            item.get("text", "")
            for item in contenido_respuesta
            if isinstance(item, dict)
        )
    return contenido_respuesta or "No recibí una respuesta."


async def _ai_completion(
    system_prompt,
    user_prompt,
    image_bytes=None,
    max_tokens=900,
):
    if OPENROUTER_API_KEY:
        return await _openrouter_completion(
            system_prompt,
            user_prompt,
            image_bytes=image_bytes,
        )
    if image_bytes is not None:
        raise RuntimeError("OPENROUTER_API_KEY no está configurada")
    if openai_client:
        return await asyncio.to_thread(
            _openai_completion,
            system_prompt,
            user_prompt,
            max_tokens,
        )
    raise RuntimeError(
        "Configura OPENROUTER_API_KEY u OPENAI_API_KEY en los secretos"
    )


async def explicar(u, c):
    tema = " ".join(c.args).strip()
    if not tema:
        await u.message.reply_text("「✿」 Uso: `/explicar derivadas`", parse_mode="Markdown")
        return
    msg = await u.message.reply_text(f"「✿」 ⏳ Explicando {tema}...")
    try:
        respuesta = await _ai_completion(
            "Eres un profesor. Explica simple en español con ejemplos.",
            f"Explica: {tema}",
            max_tokens=700,
        )
        await msg.edit_text(f"「✿」 Explicación de {tema}:\n\n{respuesta[:3900]}")
    except Exception as e:
        logging.exception("explicar error")
        await msg.edit_text(f"「✿」 Error al explicar: {e}")

def clave_examen(chat_id, user_id, area):
    area_normalizada = " ".join(area.lower().split())
    return f"{chat_id}:{user_id}:{area_normalizada}"


def extraer_json(texto):
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio < 0 or fin <= inicio:
        raise ValueError("La IA no devolvió JSON")
    return json.loads(texto[inicio:fin + 1])


def formatear_examen(datos, area):
    preguntas = datos.get("questions") or datos.get("preguntas")
    respuestas = datos.get("answers") or datos.get("respuestas")
    if not isinstance(preguntas, list) or not isinstance(respuestas, list):
        raise ValueError("Faltan preguntas o respuestas")
    if len(preguntas) != 5 or len(respuestas) != 5:
        raise ValueError("El examen no tiene exactamente 5 preguntas")

    lineas = [
        "CONCURSO DE CONOCIMIENTOS",
        f"ÁREA: {area.upper()}",
        "",
    ]
    for indice, pregunta in enumerate(preguntas, start=1):
        numero = pregunta.get("number", pregunta.get("numero", indice))
        enunciado = pregunta.get("question", pregunta.get("pregunta", ""))
        opciones = pregunta.get("options", pregunta.get("opciones", {}))
        if not enunciado or not isinstance(opciones, dict):
            raise ValueError("Pregunta con formato inválido")
        lineas.append(f"{numero}. {enunciado}")
        for letra in ("a", "b", "c", "d"):
            valor = opciones.get(letra) or opciones.get(f"{letra})")
            if not valor:
                raise ValueError("Faltan alternativas")
            lineas.append(f"{letra}) {valor}")
        lineas.append("")
    lineas.extend([
        "🔑 CLAVE DE RESPUESTAS",
        "",
    ])
    for indice, respuesta in enumerate(respuestas, start=1):
        numero = respuesta.get("number", respuesta.get("numero", indice))
        letra = respuesta.get("letter", respuesta.get("respuesta", "?"))
        explicacion = respuesta.get("explanation", respuesta.get("explicacion", ""))
        lineas.append(
            f"{numero}. {str(letra).lower()}) - {explicacion}".rstrip()
        )
    lineas.append("")
    lineas.append(f"También puedes usar /respuestas {area}.")
    return "\n".join(lineas), respuestas


async def examen(u, c):
    area = " ".join(c.args).strip()
    if not area:
        await u.message.reply_text(
            "❌ Usa: /examen <tema>\n\n"
            "Ejemplos:\n"
            "/examen Matemáticas\n"
            "/examen Arte la buena salud\n"
            "/examen Los gatos\n"
            "/examen Historia WWI"
        )
        return

    msg = await u.message.reply_text(
        f"「✿」 ⏳ Generando examen de {area}..."
    )
    try:
        respuesta = await _ai_completion(
            (
                "Eres un profesor experto. Devuelve ÚNICAMENTE JSON válido, "
                "sin Markdown ni texto adicional. Crea un examen en español."
            ),
            (
                f"Crea exactamente 5 preguntas tipo test SOLO del área "
                f'"{area}". Deben ser nuevas y de dificultad variada. '
                "Cada una debe tener exactamente cuatro alternativas a, b, c y d. "
                "Usa este esquema JSON exacto:\n"
                '{"questions":[{"number":1,"question":"...","options":'
                '{"a":"...","b":"...","c":"...","d":"..."}}],'
                '"answers":[{"number":1,"letter":"b","explanation":"..."}]}'
            ),
            max_tokens=1800,
        )
        datos = extraer_json(respuesta)
        texto_examen, respuestas = formatear_examen(datos, area)
        registro = {
            "area": area,
            "text": texto_examen,
            "answers": respuestas,
            "created_at": time.time(),
        }
        clave = clave_examen(
            u.effective_chat.id,
            u.effective_user.id,
            area,
        )
        examenes_guardados[clave] = registro
        guardar_examenes(examenes_guardados)
        await msg.edit_text(texto_examen[:3900])
    except Exception:
        logging.exception("examen error")
        await msg.edit_text(
            "❌ No pude generar el examen. Intenta nuevamente con /examen <tema>."
        )


async def respuestas(u, c):
    area = " ".join(c.args).strip()
    if not area:
        await u.message.reply_text("Usa: /respuestas Matemáticas")
        return

    clave = clave_examen(
        u.effective_chat.id,
        u.effective_user.id,
        area,
    )
    registro = examenes_guardados.get(clave)
    if not registro:
        await u.message.reply_text(
            f"❌ No encontré un examen reciente de {area} para ti.\n"
            f"Primero usa /examen {area}"
        )
        return

    lineas = [f"✅ CLAVE DE RESPUESTAS: {area.upper()}", ""]
    for indice, respuesta in enumerate(registro.get("answers", []), start=1):
        numero = respuesta.get("number", respuesta.get("numero", indice))
        letra = respuesta.get("letter", respuesta.get("respuesta", "?"))
        explicacion = respuesta.get("explanation", respuesta.get("explicacion", ""))
        lineas.append(f"{numero}. {str(letra).lower()}) {explicacion}".rstrip())
    await u.message.reply_text("\n".join(lineas)[:3900])
async def ppt(u,c):
    opciones = ["piedra","papel","tijera"]
    bot = random.choice(opciones)
    user = c.args[0].lower() if c.args else ""
    if user not in opciones: return await u.message.reply_text("Usa: /ppt piedra|papel|tijera")
    res = "Empate" if user==bot else "Ganaste" if (user=="piedra" and bot=="tijera") or (user=="papel" and bot=="piedra") or (user=="tijera" and bot=="papel") else "Perdiste"
    await u.message.reply_text(f"Tú: {user} | Yo: {bot}\n{res}")

# --- DIVERSIÓN ---
async def ship(u,c): await u.message.reply_text(f"💘 Compatibilidad: {random.randint(1,100)}%")
async def cun(u,c): await u.message.reply_text(f"💘 Tu % de cun conmigo: {random.randint(1,100)}%")
async def preniar(u,c): await u.message.reply_text(f"Hoy preño a: @{random.choice(['usuario1','usuario2','tu crush'])}")
async def sorteo(u,c): await u.message.reply_text(f"🎉 Ganador del sorteo: @{random.choice(['user1','user2'])}")
async def meme(u,c):
    cat = c.args[0].lower() if c.args else "random"
    if c.args and cat not in CATEGORIAS:
        tema = " ".join(c.args).strip()
        msg = await u.message.reply_text("😂 ⏳ Generando ideas para memes...")
        try:
            respuesta = await _ai_completion(
                "Crea ideas de memes en español. Sé breve y creativo.",
                (
                    f"Tema: {tema}\n"
                    "Genera exactamente 3 ideas.\n"
                    "Para cada una incluye:\n"
                    "😂 IDEA DEL MEME:\n"
                    "📝 TEXTO SUPERIOR:\n"
                    "📝 TEXTO INFERIOR:\n"
                    "Usa textos cortos."
                ),
                max_tokens=900,
            )
            await msg.edit_text(respuesta[:3900])
        except Exception:
            logging.exception("meme IA error")
            await msg.edit_text("❌ No pude generar ideas para ese tema.")
        return

    sub = random.choice(CATEGORIAS[cat])
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://meme-api.com/gimme/{sub}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                res = await resp.json()
        keyboard = [[InlineKeyboardButton("➡️ Siguiente", callback_data=f"meme_{cat}")]]
        await u.message.reply_photo(
            photo=res["url"],
            caption=f"😂 **{res.get('title','')}**\n`r/{res.get('subreddit',sub)}` | Categoría: {cat}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await u.message.reply_text(f"❌ Fallo al cargar meme. Intenta de nuevo 😅\n{e}")

async def next_meme_handler(u, c):
    query = u.callback_query
    await query.answer()
    cat = query.data.split("_")[1]
    if cat not in CATEGORIAS: cat = "random"
    sub = random.choice(CATEGORIAS[cat])
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://meme-api.com/gimme/{sub}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                res = await resp.json()
        keyboard = [[InlineKeyboardButton("➡️ Siguiente", callback_data=f"meme_{cat}")]]
        from telegram import InputMediaPhoto
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=res["url"],
                caption=f"😂 **{res.get('title','')}**\n`r/{res.get('subreddit',sub)}` | Categoría: {cat}",
                parse_mode='Markdown'
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

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
        await u.message.reply_text("Responde a una foto, video o gif con /sticker bro")
        return

    msg = u.message.reply_to_message
    await u.message.reply_text("Procesando... espera 👀")

    try:
        # FOTO → WebP estático
        if msg.photo:
            file = await c.bot.get_file(msg.photo[-1].file_id)
            await file.download_to_drive("/tmp/sticker_in.jpg")
            subprocess.run([
                "ffmpeg", "-y", "-i", "/tmp/sticker_in.jpg",
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease",
                "-fs", "500KB",
                "/tmp/sticker_out.webp"
            ], capture_output=True)
            with open("/tmp/sticker_out.webp", "rb") as f:
                await u.message.reply_sticker(sticker=f)
            await u.message.reply_text("✅ Sticker estático listo 😎")

        # VIDEO / GIF / ANIMACIÓN → WebM animado
        elif msg.video or msg.animation or msg.document:
            file_id = msg.video.file_id if msg.video else msg.animation.file_id if msg.animation else msg.document.file_id
            file = await c.bot.get_file(file_id)
            await file.download_to_drive("/tmp/sticker_in.mp4")
            await u.message.reply_text("🎬 Convirtiendo a sticker animado... espera ~10 seg 👀")
            result = subprocess.run([
                "ffmpeg", "-y", "-i", "/tmp/sticker_in.mp4",
                "-vcodec", "libvpx-vp9", "-fs", "500KB",
                "-an", "-ss", "0", "-t", "3",
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease,fps=15",
                "/tmp/sticker_out.webm"
            ], capture_output=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode()[-300:])
            with open("/tmp/sticker_out.webm", "rb") as f:
                await u.message.reply_sticker(sticker=f)
            await u.message.reply_text("✅ Sticker animado listo 😎")

        else:
            await u.message.reply_text("Eso no es foto ni video bro. Responde a una imagen o video")

    except Exception as e:
        logging.exception("sticker error")
        await u.message.reply_text(f"❌ Error: {e}")
    finally:
        for p in ("/tmp/sticker_in.jpg", "/tmp/sticker_in.mp4",
                  "/tmp/sticker_out.webp", "/tmp/sticker_out.webm"):
            if os.path.exists(p): os.remove(p)

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
            'format': 'bestvideo[height<=480][vcodec^=avc]+bestaudio/best[height<=480]',
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
        await u.message.reply_text("Usa: `/video link` o `/video nombre del video`", parse_mode='Markdown')
        return

    query = " ".join(c.args)
    msg = await u.message.reply_text(f"Buscando opciones de: {query} ⏳")

    # Link directo de YouTube o Shorts
    if any(x in query for x in ("youtube.com", "youtu.be", "shorts")):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(query, download=False)
                title = info.get('title')
                video_id = info.get('id')
            keyboard = [[InlineKeyboardButton(f"📹 Descargar: {title[:40]}", callback_data=f"vdl_{video_id}")]]
            await msg.edit_text(f"Video encontrado: *{title}*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except Exception as e:
            await msg.edit_text(f"❌ Error con el link: {e}")
        return

    # Búsqueda por nombre
    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']

        keyboard = []
        for i, v in enumerate(videos[:5]):
            title = v['title']
            duration = v.get('duration', 0)
            mins, secs = divmod(duration, 60)
            tag = " [SHORT]" if duration <= 60 else ""
            keyboard.append([InlineKeyboardButton(f"{i+1}. {title[:35]}{tag} [{mins}:{secs:02d}]", callback_data=f"vdl_{v['id']}")])

        await msg.edit_text(f"Elige un video para: *{query}*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    except Exception as e:
        logging.exception("video error")
        await msg.edit_text(f"❌ Error buscando: {e}")

async def ytmp3(u,c): await playaudio(u,c)

def es_facebook(url):
    patrones = (
        r"https?://(?:www\.)?facebook\.com/",
        r"https?://fb\.watch/",
        r"https?://m\.facebook\.com/",
        r"https?://mbasic\.facebook\.com/",
    )
    return any(re.match(patron, url, re.IGNORECASE) for patron in patrones)

def descargar_audio_facebook(url):
    prefix = f"/tmp/dante_fbmp3_{int(time.time() * 1000)}"
    opciones = {
        "format": "bestaudio/best",
        "outtmpl": f"{prefix}.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(opciones) as ydl:
        informacion = ydl.extract_info(url, download=True)
        titulo = informacion.get("title", "Facebook Audio")
        archivo_original = ydl.prepare_filename(informacion)
        archivo_mp3 = os.path.splitext(archivo_original)[0] + ".mp3"
    return archivo_mp3, titulo

async def fbmp3(u,c):
    if not c.args:
        await u.message.reply_text(
            "❌ Debes colocar un enlace de Facebook.\n\n"
            "Ejemplo:\n/fbmp3 https://www.facebook.com/..."
        )
        return

    url = c.args[0].strip()
    if not es_facebook(url):
        await u.message.reply_text("❌ Ese enlace no parece ser de Facebook.")
        return

    mensaje = await u.message.reply_text("⏳ Descargando el audio de Facebook...")
    archivo = None
    try:
        archivo, titulo = await asyncio.to_thread(descargar_audio_facebook, url)
        if not os.path.exists(archivo):
            raise FileNotFoundError("No se encontró el archivo MP3")

        if os.path.getsize(archivo) > 50 * 1024 * 1024:
            raise ValueError("El audio supera el límite de Telegram")

        await mensaje.edit_text("✅ Audio descargado.\n📤 Enviándolo...")
        with open(archivo, "rb") as audio:
            await u.message.reply_audio(
                audio=audio,
                title=titulo[:64],
                performer="Facebook → MP3",
            )
        await mensaje.delete()
    except Exception:
        logging.exception("fbmp3 error")
        await mensaje.edit_text(
            "❌ No pude descargar ese enlace.\n\n"
            "Puede que el video sea privado, requiera iniciar sesión "
            "o que Facebook no permita acceder a él."
        )
    finally:
        if archivo and os.path.exists(archivo):
            os.remove(archivo)

async def descargar_audio_url(session, audio_url, timeout):
    async with session.get(audio_url, timeout=timeout) as response:
        if response.status != 200:
            return None
        return await response.read()

async def buscar_sonido_pixabay(texto):
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession() as session:
        params = {"q": texto, "per_page": 3}
        if PIXABAY_API_KEY:
            params["key"] = PIXABAY_API_KEY
        async with session.get(
            "https://pixabay.com/api/sound-effects/",
            params=params,
            timeout=timeout,
        ) as response:
            if response.status != 200:
                return None
            resultado = await response.json(content_type=None)

        hits = resultado.get("hits", [])
        if not hits:
            return None

        audio_url = hits[0].get("audiodownload") or hits[0].get("audio")
        if not audio_url:
            return None
        audio = await descargar_audio_url(session, audio_url, timeout)
        if not audio:
            return None
        return {"audio": audio, "fuente": "Pixabay", "url": audio_url}

def parsear_sonido(texto_completo):
    partes = texto_completo.strip().split()
    if not partes:
        return None

    estilos = {"cinematic", "cartoon", "realistic", "8bit"}
    estilo = "realistic"
    if partes and partes[-1].lower() in estilos:
        estilo = partes.pop().lower()

    duracion = 3.0
    if partes and re.fullmatch(r"\d+(?:\.\d+)?", partes[-1]):
        duracion = min(max(float(partes.pop()), 0.5), 10.0)

    texto = " ".join(partes).strip()
    if not texto:
        return None
    return texto, duracion, estilo


def clave_sonido(texto, duracion, estilo):
    return f"{texto}|{duracion:g}|{estilo}"


def token_sonido(cache_key):
    return hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:12]


def teclado_sonido(cache_key, duracion):
    token = token_sonido(cache_key)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🔄 Regenerar",
            callback_data=f"snd|regen|{token}|{duracion:g}",
        ),
        InlineKeyboardButton(
            "⏱️ +2 seg",
            callback_data=f"snd|more|{token}|{duracion:g}",
        ),
    ]])


def buscar_cache_sonido_por_token(token):
    for cache_key, registro in cache_sonidos.items():
        if cache_key.startswith("__"):
            continue
        if token_sonido(cache_key) == token and isinstance(registro, dict):
            return cache_key, registro
    return None, None


def decodificar_cache_sonido(registro):
    if not isinstance(registro, dict):
        return None
    contenido = registro.get("audio_base64")
    if not contenido:
        return None
    try:
        return base64.b64decode(contenido, validate=True)
    except (ValueError, TypeError):
        return None


async def crear_sonido_elevenlabs(prompt, duracion):
    if not ELEVENLABS_API_KEY:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            }
        ) as session:
            async with session.post(
                "https://api.elevenlabs.io/v1/sound-generation",
                json={
                    "text": prompt,
                    "duration_seconds": duracion,
                    "prompt_influence": 0.7,
                },
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    detalle = (await response.text())[:500]
                    logging.warning(
                        "ElevenLabs respondió HTTP %s: %s",
                        response.status,
                        detalle,
                    )
                    return None
                return await response.read(), "ElevenLabs"
    except Exception:
        logging.exception("ElevenLabs sound generation error")
        return None


async def procesar_sonido(message, bot, texto_completo, force_regenerate=False,
                          duracion_override=None, estilo_override=None):
    datos = parsear_sonido(texto_completo)
    if not datos:
        await message.reply_text(
            "Usa: /sonidos zombie grito 3 cinematic\n"
            "Estilos: realistic, cinematic, cartoon, 8bit"
        )
        return

    texto, duracion, estilo = datos
    if duracion_override is not None:
        duracion = min(max(float(duracion_override), 0.5), 10.0)
    if estilo_override:
        estilo = estilo_override

    cache_key = clave_sonido(texto, duracion, estilo)
    audio = None if force_regenerate else decodificar_cache_sonido(
        cache_sonidos.get(cache_key)
    )

    await bot.send_chat_action(
        chat_id=message.chat_id,
        action="upload_audio",
    )

    if audio:
        estado = await message.reply_text("✅ Encontrado en la caché")
        fuente = "Caché de DANTE"
    else:
        estado = await message.reply_text(
            f"🎙️ Creando «{texto}» con IA\n"
            f"Duración: {duracion:g}s | Estilo: {estilo}... ⏳"
        )
        resultado = await crear_sonido_elevenlabs(
            f"{texto}, {estilo} sound effect",
            duracion,
        )
        if not resultado:
            await estado.edit_text(
                "❌ Falló la generación con IA. Revisa la clave, los permisos "
                "y los créditos de ElevenLabs con /creditos."
            )
            return
        audio, fuente = resultado
        cache_sonidos[cache_key] = {
            "texto": texto,
            "duracion": duracion,
            "estilo": estilo,
            "audio_base64": base64.b64encode(audio).decode("ascii"),
        }
        guardar_cache_sonidos(cache_sonidos)

    nombre = re.sub(r"[^\w .-]", "_", texto)[:60].strip() or "sonido"
    audio_file = BytesIO(audio)
    audio_file.name = f"{nombre}.mp3"
    await message.reply_audio(
        audio=audio_file,
        title=nombre[:64],
        performer=fuente,
        caption=f"🔊 {texto}\nDuración: {duracion:g}s | Estilo: {estilo}",
        reply_markup=teclado_sonido(cache_key, duracion),
    )
    await estado.edit_text("✅ Sonido listo")


async def sonidos(u,c):
    texto = " ".join(c.args).strip()
    if not texto:
        await u.message.reply_text(
            "Usa: /sonidos zombie grito 3 cinematic\n"
            "Estilos: realistic, cinematic, cartoon, 8bit"
        )
        return
    await procesar_sonido(u.message, c.bot, texto)


async def sonidos_callback(u, c):
    query = u.callback_query
    partes = query.data.split("|")
    if len(partes) != 4:
        await query.answer()
        return

    accion, token, duracion_raw = partes[1], partes[2], partes[3]
    try:
        duracion = float(duracion_raw)
    except ValueError:
        await query.edit_message_text("❌ La duración indicada no es válida.")
        return

    cache_key, registro = buscar_cache_sonido_por_token(token)
    if not registro:
        await query.edit_message_text(
            "❌ Esta acción caducó. Genera un sonido nuevo con /sonidos."
        )
        return

    texto = registro.get("texto", "")
    estilo = registro.get("estilo", "realistic")
    if not texto:
        await query.edit_message_text("❌ No pude recuperar ese sonido.")
        return

    if accion == "more":
        duracion = min(duracion + 2.0, 10.0)
        await query.answer(f"Creando de {duracion:g} segundos...")
        await procesar_sonido(
            query.message,
            c.bot,
            texto,
            duracion_override=duracion,
            estilo_override=estilo,
        )
    elif accion == "regen":
        await query.answer("Regenerando con IA...")
        await procesar_sonido(
            query.message,
            c.bot,
            texto,
            force_regenerate=True,
            duracion_override=duracion,
            estilo_override=estilo,
        )
    else:
        await query.answer("Acción no reconocida.")

async def creditos(u,c):
    if not ELEVENLABS_API_KEY:
        await u.message.reply_text("❌ La API de ElevenLabs no está configurada.")
        return

    await c.bot.send_chat_action(
        chat_id=u.effective_chat.id,
        action="typing",
    )
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        ) as session:
            async with session.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                datos = await response.json(content_type=None)

        total = int(datos["character_limit"])
        usado = int(datos["character_count"])
        sobra = max(total - usado, 0)
        await u.message.reply_text(
            "💰 Créditos ElevenLabs\n\n"
            f"Total del mes: {total:,}\n"
            f"Usado: {usado:,}\n"
            f"Te sobra: {sobra:,} caracteres\n\n"
            "Se reinician el día 1 de cada mes"
        )
    except Exception:
        logging.exception("ElevenLabs credits error")
        await u.message.reply_text(
            "❌ No pude consultar los créditos de ElevenLabs. "
            "Revisa que la clave tenga permisos."
        )

async def tt(u,c):
    if not c.args:
        await u.message.reply_text(
            "「✿」 Uso: `/tt https://www.tiktok.com/...`",
            parse_mode="Markdown"
        )
        return

    url = c.args[0].strip()
    if not re.search(r"(?:^|//)(?:www\.)?(?:vm\.)?tiktok\.com(?:/|$)", url, re.IGNORECASE):
        await u.message.reply_text("「✿」 Manda un link de TikTok válido rata")
        return

    msg = await u.message.reply_text("「✿」 ⏳ Bajando video sin marca de agua...")
    data = await get_tiktok_video(url)
    if not data:
        await u.message.reply_text(
            "「✿」 No pude descargar ese video. Puede ser privado o el link está mal"
        )
        return

    try:
        await u.effective_chat.send_video(
            video=data["video"],
            caption=(
                f"「✿」 **{data['title']}**\n"
                f"👤 @{data['author']}\n\n"
                "Descargado por DANTE Bot"
            ),
            parse_mode="Markdown"
        )
        await msg.delete()
    except Exception as e:
        logging.exception("tt error")
        await u.message.reply_text(
            "「✿」 El video pesa mucho o Telegram no pudo enviarlo. "
            f"Toma el link directo:\n{data['video']}"
        )


def es_tiktok(url):
    return bool(re.search(
        r"(?:^|//)(?:www\.|vm\.|lite\.)?tiktok\.com(?:/|$)",
        url,
        re.IGNORECASE,
    ))


def descargar_audio_tiktok(url):
    prefijo = f"/tmp/dante_ttmp3_{time.time_ns()}"
    opciones = {
        "format": "bestaudio/best",
        "outtmpl": f"{prefijo}.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(opciones) as ydl:
        informacion = ydl.extract_info(url, download=True)
        titulo = informacion.get("title", "Audio TikTok")
        archivo_original = ydl.prepare_filename(informacion)
        archivo_mp3 = os.path.splitext(archivo_original)[0] + ".mp3"
    return archivo_mp3, titulo, prefijo


async def ttmp3(u,c):
    if not c.args:
        await u.message.reply_text(
            "Usa: `/ttmp3 https://www.tiktok.com/...`\n"
            "También acepta enlaces de TikTok Lite.",
            parse_mode="Markdown",
        )
        return

    url = c.args[0].strip()
    if not es_tiktok(url):
        await u.message.reply_text(
            "❌ Ese enlace no parece ser un TikTok válido."
        )
        return

    estado = await u.message.reply_text("⏳ Extrayendo audio de TikTok...")
    archivo = None
    prefijo = None
    try:
        await c.bot.send_chat_action(
            chat_id=u.effective_chat.id,
            action="upload_audio",
        )
        archivo, titulo, prefijo = await asyncio.to_thread(
            descargar_audio_tiktok,
            url,
        )
        if not os.path.exists(archivo):
            raise FileNotFoundError("yt-dlp no generó el MP3")
        if os.path.getsize(archivo) > 50 * 1024 * 1024:
            raise ValueError("El audio supera el límite de Telegram")

        await estado.edit_text("✅ Audio extraído. Enviándolo...")
        with open(archivo, "rb") as audio:
            await u.message.reply_audio(
                audio=audio,
                title=titulo[:64],
                performer="TikTok → MP3",
            )
        await estado.delete()
    except yt_dlp.utils.DownloadError:
        logging.exception("ttmp3 descarga error")
        await estado.edit_text(
            "❌ No se pudo descargar ese TikTok. Puede ser privado, "
            "estar restringido o tener un enlace inválido."
        )
    except Exception:
        logging.exception("ttmp3 error")
        await estado.edit_text(
            "❌ No pude extraer el audio. Intenta con otro enlace de TikTok."
        )
    finally:
        if prefijo:
            for temporal in glob.glob(f"{prefijo}*"):
                try:
                    os.remove(temporal)
                except OSError:
                    logging.warning("No se pudo borrar temporal: %s", temporal)


async def get_tiktok_video(url):
    apis = [
        ("https://api.tikwm.com/video/", "tikwm"),
        ("https://www.tikwm.com/api/", "tikwm"),
        ("https://api.tiktokio.com/video", "tiktokio"),
    ]
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(headers=headers) as session:
        for api_url, provider in apis:
            try:
                async with session.get(
                    api_url,
                    params={"url": url},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        continue
                    res = await response.json(content_type=None)

                if provider == "tikwm" and res.get("data", {}).get("play"):
                    item = res["data"]
                    author = item.get("author", {})
                    if isinstance(author, dict):
                        author = author.get("nickname", "Desconocido")
                    return {
                        "video": item["play"],
                        "title": item.get("title", "Video TikTok"),
                        "author": author or "Desconocido",
                    }

                if (
                    provider == "tiktokio"
                    and res.get("status") == "success"
                    and res.get("data", {}).get("video")
                ):
                    item = res["data"]
                    return {
                        "video": item["video"],
                        "title": item.get("title", "Video TikTok"),
                        "author": item.get("author", "Desconocido"),
                    }
            except Exception:
                logging.exception("TikTok API falló: %s", api_url)
                continue

    return None

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
    ahora = time.time()
    LIMITE = 1_000_000
    if ahora - user.get("ultimo_daily", 0) < 86400:
        resto = 86400 - (ahora - user["ultimo_daily"])
        h, m = int(resto // 3600), int((resto % 3600) // 60)
        await u.message.reply_text(f"⏰ Ya reclamaste hoy.\nVuelve en {h}h {m}m")
        return
    if user["racha_daily"] == 0:
        coins = 5000
        user["racha_daily"] = 1
    else:
        coins = min(user.get("ultimo_daily_coins", 5000) * 2, LIMITE)
        user["racha_daily"] += 1
    user["balance"] += coins
    user["tickets"] += 1
    user["ultimo_daily"] = ahora
    user["ultimo_daily_coins"] = coins
    guardar_db(db)
    extra = "\n🔥 **TOPE MÁXIMO** 🔥" if coins >= LIMITE else f"\nMañana: ${min(coins*2, LIMITE):,}"
    await u.message.reply_text(
        f"🎁 **RECOMPENSA DIARIA DÍA {user['racha_daily']}**{extra}\n\n"
        f"💰 Coins: ${coins:,}\n🎟️ Tickets: +1\n\n"
        f"Balance: ${user['balance']:,}\nTickets: {user['tickets']}",
        parse_mode='Markdown'
    )

async def daily(u,c): await diario(u,c)

async def robar(u,c):
    user = get_user(u.effective_user.id)
    robo = random.randint(5,30)
    user['balance'] += robo; guardar_db(db)
    await u.message.reply_text(f"Robaste {robo} monedas! 😈")

async def tiendaeco(u,c): await u.message.reply_text("Tienda: 1. Espada - 500\n2. Escudo - 300")
async def gacha(u,c):
    user = get_user(u.effective_user.id)
    if user.get("tickets", 0) < 1:
        await u.message.reply_text("❌ Te faltan tickets.\nUsa `/daily` para reclamar 1 ticket gratis", parse_mode='Markdown')
        return
    user["tickets"] -= 1
    suerte = random.uniform(0, 100)
    rareza = "SSSR" if suerte <= 0.5 else "SSR" if suerte <= 10.5 else "SR" if suerte <= 45.5 else "R"
    waifu = random.choice(WAIFUS[rareza])
    user["waifus"].append(f"{rareza} - {waifu}")
    guardar_db(db)
    caption = (
        f"{EMOJIS_R[rareza]} **TIRASTE EL GACHA** {EMOJIS_R[rareza]}\n\n"
        f"**Rareza:** {rareza}\n**Waifu:** {waifu}\n\n"
        f"🎟️ Tickets: {user['tickets']}\n💍 Waifus totales: {len(user['waifus'])}"
    )
    img_path = f"telegram-bot/waifus/{waifu}.jpg"
    if os.path.exists(img_path):
        await u.message.reply_photo(photo=open(img_path, 'rb'), caption=caption, parse_mode='Markdown')
    else:
        await u.message.reply_text(caption, parse_mode='Markdown')

async def tickets(u,c):
    user = get_user(u.effective_user.id)
    await u.message.reply_text(f"🎟️ Tienes: {user.get('tickets', 0)} tickets")

async def inventario(u,c):
    user = get_user(u.effective_user.id)
    waifus = user.get("waifus", [])
    texto = "🎒 **TU COLECCIÓN**\n\n" + ("\n".join(waifus) if waifus else "No tienes waifus aún. Usa /gacha")
    await u.message.reply_text(texto, parse_mode='Markdown')

# --- ADMIN ---
async def kick(u,c):
    chat = u.effective_chat
    user = u.effective_user
    msg = u.message
    try:
        member = await chat.get_member(user.id)
        if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            await msg.reply_text("Solo los admins pueden usar /kick 😒"); return
    except:
        await msg.reply_text("No pude verificar si eres admin"); return
    if not msg.reply_to_message and not c.args:
        await msg.reply_text("Responde al mensaje del wey o pon /kick @usuario"); return
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        try:
            cm = await c.bot.get_chat_member(chat.id, c.args[0])
            target = cm.user
        except:
            await msg.reply_text("No encontré a ese usuario"); return
    target_member = await chat.get_member(target.id)
    if target_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await msg.reply_text("No puedo kickear a un admin bro"); return
    if target.id == c.bot.id:
        await msg.reply_text("No me puedo kickear solo 😭"); return
    try:
        await chat.ban_member(target.id)
        await chat.unban_member(target.id)
        await msg.reply_text(f"👢 {target.first_name} fue eliminado del grupo")
    except Exception as e:
        await msg.reply_text(f"❌ Error: {e}")
async def ban(u,c): await u.message.reply_text("Baneado... necesitas darme admin")
async def warn(u,c): await u.message.reply_text("Advertencia enviada ⚠️")

async def link(u,c):
    try:
        invite_link = await c.bot.export_chat_invite_link(u.effective_chat.id)
        await u.message.reply_text(
            f"「✿」 **Link del grupo:**\n{invite_link}",
            parse_mode="Markdown",
        )
    except Exception:
        await u.message.reply_text("「✿」 No tengo permisos para crear links")

# --- SHOP / IA ---
usuarios_soporte = set()

async def premium(u,c):
    user = get_user(u.effective_user.id)
    if user.get("vip", False):
        await u.message.reply_text("「✿」 Ya eres **VIP** 👑", parse_mode="Markdown")
        return
    user["vip"] = True
    guardar_db(db)
    await u.message.reply_text("「✿」 Compraste **VIP** 👑", parse_mode="Markdown")

async def tienda(u,c): await u.message.reply_text("Tienda de productos: Proximamente")

async def soporte(u,c):
    usuarios_soporte.add(u.effective_user.id)
    await u.message.reply_text(
        "💬 SOPORTE IA ACTIVADO\n"
        "Escríbeme tu pregunta.\n"
        "Para salir: /salirsoporte"
    )


async def salirsoporte(u,c):
    usuarios_soporte.discard(u.effective_user.id)
    await u.message.reply_text("✅ Saliste del soporte IA.")


async def chat_soporte(u,c):
    pregunta = u.message.text.strip()
    estado = await u.message.reply_text("「✿」 ⏳ Pensando...")
    try:
        respuesta = await _ai_completion(
            "Eres el asistente de soporte de DANTE, un bot de Telegram. "
            "Responde amable, claro y útil en español.",
            f"Pregunta del usuario:\n{pregunta}",
            max_tokens=700,
        )
        await estado.edit_text(respuesta[:3900])
    except Exception:
        logging.exception("soporte IA error")
        await estado.edit_text(
            "❌ No pude responder en este momento. Revisa la configuración de IA."
        )


async def manejar_texto(u,c):
    if u.effective_user and u.effective_user.id in usuarios_soporte:
        await chat_soporte(u,c)
        return
    await auto_resolver(u,c)

async def imagine(u,c): await u.message.reply_text("Generar imagen con IA: Necesitas API Key. Te ayudo a ponerla")

# --- REGISTRO ---
app = A().token(T).build()

CMDS = {
    "start": start, "help": help, "ping": ping, "dado": dado, "coin": coin,
    "chiste": chiste, "frase": frase, "picante": picante, "bola8": bola8,
        "calcular": calcular, "resolver": resolver, "explicar": explicar,
        "examen": examen, "respuestas": respuestas,
    "ppt": ppt, "ship": ship, "cun": cun, "preniar": preniar,
    "sorteo": sorteo, "meme": meme, "gato": gato, "perro": perro,
    "stickerpreniar": stickerpreniar, "sticker": sticker,
    "yts": yts, "playaudio": playaudio, "video": video, "ytmp3": ytmp3,
    "tt": tt, "ttmp3": ttmp3,
    "fbmp3": fbmp3, "sonidos": sonidos, "creditos": creditos,
    "balance": balance, "trabajar": trabajar, "diario": diario, "daily": daily, "robar": robar,
    "tiendaeco": tiendaeco, "gacha": gacha, "tickets": tickets, "inventario": inventario,
    "kick": kick, "ban": ban, "warn": warn, "link": link,
    "premium": premium, "tienda": tienda, "soporte": soporte,
    "salirsoporte": salirsoporte, "imagine": imagine,
}

for cmd, fn in CMDS.items():
    app.add_handler(C(cmd, fn))

app.add_handler(M(F.TEXT & ~F.COMMAND, manejar_texto))
app.add_handler(CallbackQueryHandler(sonidos_callback, pattern=r"^snd\|"))
app.add_handler(CallbackQueryHandler(next_meme_handler, pattern="^meme_"))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(dl_|vdl_)"))

print(f"Bot DANTE iniciado con {len(CMDS)} comandos")
app.run_polling()
