import os
import json
import random
import logging
import time

import requests
import yt_dlp
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

ARCHIVO = "/tmp/economia.json"

TIENDA_ITEMS = {
    "espada":   {"precio": 500,  "desc": "⚔️ Espada del robo +20%"},
    "escudo":   {"precio": 400,  "desc": "🛡️ Escudo anti-robo"},
    "amuleto":  {"precio": 300,  "desc": "🧿 Amuleto de la suerte"},
    "varita":   {"precio": 600,  "desc": "🪄 Varita mágica"},
    "corona":   {"precio": 1000, "desc": "👑 Corona de DANTE"},
}

GACHA_PREMIOS = [
    ("💎 Diamante", 2000),
    ("⭐ Estrella", 800),
    ("🎖️ Medalla", 500),
    ("🍀 Trébol", 300),
    ("🪨 Piedra", 50),
]
GACHA_PESO = [5, 15, 25, 30, 25]


# ─── Economía helpers ────────────────────────────────────────────────────────

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


# ─── Verificar admin ─────────────────────────────────────────────────────────

async def es_admin(update: Update) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    try:
        member = await chat.get_member(user.id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception:
        return False


# ─── Básicos ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 DANTE BOT ON\nEscribe /help para ver todo")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👑 COMANDOS DANTE BOT 👑\n\n"
        "📌 Básicos\n"
        "/start  /ping  /help\n\n"
        "🎵 Música\n"
        "/playaudio nombre\n\n"
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
        "/robar (responde a un mensaje)\n"
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


# ─── Música ──────────────────────────────────────────────────────────────────

async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /playaudio nombre de la canción")
    nombre = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Buscando: {nombre}... ⏳")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/song.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{nombre}", download=True)
            titulo = info["entries"][0]["title"]
        await msg.delete()
        with open("/tmp/song.mp3", "rb") as audio_file:
            await update.message.reply_audio(audio=audio_file, title=titulo, caption=f"🎵 {titulo}")
        os.remove("/tmp/song.mp3")
    except Exception:
        logging.exception("playaudio error")
        await msg.edit_text("😢 No encontré esa canción. Prueba con menos palabras")


# ─── Entretenimiento ─────────────────────────────────────────────────────────

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
    porcentaje = random.randint(1, 100)
    emoji = "💘" if porcentaje > 70 else "💔" if porcentaje < 30 else "💕"
    await update.message.reply_text(
        f"{emoji} {context.args[0]} x {context.args[1]} = {porcentaje}% compatible"
    )


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
    await update.message.reply_text(f"🎉 El ganador del sorteo es: {random.choice(ganadores)}")


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
    victima = random.choice(["tu ex", "al admin", "a tu crush", "al grupo entero"])
    await update.message.reply_text(f"Hoy preño a {victima} 🤰")


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
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expr):
            raise ValueError("Caracteres no permitidos")
        resultado = eval(expr, {"__builtins__": {}})
        await update.message.reply_text(f"🧮 {expr} = {resultado}")
    except Exception:
        await update.message.reply_text("Expresión inválida. Ejemplo: /calcular 10 * 3")


async def imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /imagine un gato astronauta")
    await update.message.reply_text("🎨 Imagen con IA próximamente...")


# ─── Economía ─────────────────────────────────────────────────────────────────

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    user = get_user(data, str(update.effective_user.id))
    nombre = update.effective_user.first_name
    items_str = ", ".join(user["items"]) if user["items"] else "ninguno"
    await update.message.reply_text(
        f"💰 Balance de {nombre}\n"
        f"Dinero: ${user['dinero']}\n"
        f"Items: {items_str}"
    )


COOLDOWN_TRABAJO = 3600  # 1 hora

async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    ahora = time.time()
    restante = COOLDOWN_TRABAJO - (ahora - user.get("trabajo_ts", 0))
    if restante > 0:
        mins = int(restante // 60)
        return await update.message.reply_text(f"⏳ Ya trabajaste. Espera {mins} min para volver a trabajar")
    trabajos = ["limpiaste ventanas", "repartiste volantes", "cocinaste", "programaste", "vendiste memes"]
    ganancia = random.randint(50, 300)
    user["dinero"] += ganancia
    user["trabajo_ts"] = ahora
    guardar_datos(data)
    await update.message.reply_text(f"💼 {random.choice(trabajos).capitalize()} y ganaste ${ganancia} 💰")


COOLDOWN_DIARIO = 86400  # 24 horas

async def diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    ahora = time.time()
    restante = COOLDOWN_DIARIO - (ahora - user.get("diario_ts", 0))
    if restante > 0:
        horas = int(restante // 3600)
        mins = int((restante % 3600) // 60)
        return await update.message.reply_text(f"⏳ Ya recibiste tu diario. Vuelve en {horas}h {mins}m")
    user["dinero"] += 500
    user["diario_ts"] = ahora
    guardar_datos(data)
    await update.message.reply_text("🎁 Recompensa diaria recibida: +$500 💰")


async def robar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje de la persona que quieres robar")
    data = cargar_datos()
    ladron_id = str(update.effective_user.id)
    victima_id = str(update.message.reply_to_message.from_user.id)
    if ladron_id == victima_id:
        return await update.message.reply_text("No puedes robarte a ti mismo 😂")
    ladron = get_user(data, ladron_id)
    victima = get_user(data, victima_id)
    # Escudo anti-robo
    if "escudo" in victima.get("items", []):
        return await update.message.reply_text("🛡️ ¡La víctima tiene escudo! El robo falló")
    if victima["dinero"] <= 0:
        return await update.message.reply_text("Esa persona no tiene nada que robar 😂")
    exito = random.random() < 0.55
    if exito:
        robo = min(random.randint(20, 150), victima["dinero"])
        if "espada" in ladron.get("items", []):
            robo = int(robo * 1.2)
        victima["dinero"] -= robo
        ladron["dinero"] += robo
        guardar_datos(data)
        nombre_v = update.message.reply_to_message.from_user.first_name
        await update.message.reply_text(f"🦹 ¡Robaste ${robo} a {nombre_v}! 💰")
    else:
        multa = random.randint(20, 80)
        ladron["dinero"] = max(0, ladron["dinero"] - multa)
        guardar_datos(data)
        await update.message.reply_text(f"👮 ¡Te cacharon robando! Pagas multa de ${multa}")


async def tiendaeco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🛒 TIENDA DEL BOT\n"]
    for item, info in TIENDA_ITEMS.items():
        lines.append(f"{info['desc']} — ${info['precio']}\nComando: /comprar {item}")
    await update.message.reply_text("\n".join(lines))


async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usa: /comprar espada")
    item = context.args[0].lower()
    if item not in TIENDA_ITEMS:
        return await update.message.reply_text(f"Item '{item}' no existe. Usa /tiendaeco para ver la lista")
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    precio = TIENDA_ITEMS[item]["precio"]
    if item in user["items"]:
        return await update.message.reply_text("Ya tienes ese item 🤔")
    if user["dinero"] < precio:
        return await update.message.reply_text(f"No tienes suficiente dinero. Necesitas ${precio}, tienes ${user['dinero']}")
    user["dinero"] -= precio
    user["items"].append(item)
    guardar_datos(data)
    await update.message.reply_text(f"✅ Compraste {TIENDA_ITEMS[item]['desc']} por ${precio}")


async def inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    user = get_user(data, str(update.effective_user.id))
    if not user["items"]:
        return await update.message.reply_text("🎒 Tu inventario está vacío. Compra algo en /tiendaeco")
    lines = ["🎒 TU INVENTARIO\n"]
    for item in user["items"]:
        lines.append(TIENDA_ITEMS[item]["desc"])
    await update.message.reply_text("\n".join(lines))


async def gacha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = cargar_datos()
    uid = str(update.effective_user.id)
    user = get_user(data, uid)
    costo = 300
    if user["dinero"] < costo:
        return await update.message.reply_text(f"💸 Necesitas ${costo} para tirar gacha. Tienes ${user['dinero']}")
    user["dinero"] -= costo
    premio_nombre, premio_dinero = random.choices(GACHA_PREMIOS, weights=GACHA_PESO, k=1)[0]
    user["dinero"] += premio_dinero
    guardar_datos(data)
    await update.message.reply_text(
        f"🎰 GACHA\nGastaste: ${costo}\nObtuviste: {premio_nombre}\nGanaste: ${premio_dinero}\n"
        f"{'¡GANASTE!' if premio_dinero > costo else 'Mala suerte...'}"
    )


# ─── Admin ────────────────────────────────────────────────────────────────────

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins pueden usar esto")
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
        return await update.message.reply_text("🚫 Solo admins pueden usar esto")
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
        return await update.message.reply_text("🚫 Solo admins pueden usar esto")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Responde al mensaje del usuario a advertir")
    data = cargar_datos()
    uid = str(update.message.reply_to_message.from_user.id)
    user = get_user(data, uid)
    user["warns"] = user.get("warns", 0) + 1
    guardar_datos(data)
    nombre = update.message.reply_to_message.from_user.first_name
    warns = user["warns"]
    await update.message.reply_text(f"⚠️ {nombre} recibió advertencia #{warns}")
    if warns >= 3:
        try:
            await update.effective_chat.ban_member(int(uid))
            await update.message.reply_text(f"🔨 {nombre} fue baneado/a por {warns} advertencias")
        except Exception:
            pass


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update):
        return await update.message.reply_text("🚫 Solo admins pueden usar esto")
    try:
        inv = await update.effective_chat.create_invite_link()
        await update.message.reply_text(f"🔗 Link del grupo:\n{inv.invite_link}")
    except Exception as e:
        await update.message.reply_text(f"No pude crear el link: {e}")


# ─── Negocio ──────────────────────────────────────────────────────────────────

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 COMPRAR VIP — $5 soles\n\n"
        "Beneficios:\n"
        "- Música ilimitada\n"
        "- Sin espera en /trabajar\n"
        "- Prioridad en soporte\n\n"
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

    handlers = [
        # Básicos
        ("start", start),
        ("help", help_cmd),
        ("ping", ping),
        # Música
        ("playaudio", playaudio),
        # Entretenimiento
        ("frase", frase),
        ("chiste", chiste),
        ("bola8", bola8),
        ("dado", dado),
        ("coin", coin),
        ("ship", ship),
        ("ppt", ppt),
        ("sorteo", sorteo),
        ("gato", gato),
        ("perro", perro),
        ("cun", cun),
        ("preniar", preniar),
        ("picante", picante),
        ("meme", meme),
        ("calcular", calcular),
        ("imagine", imagine),
        # Economía
        ("balance", balance),
        ("trabajar", trabajar),
        ("diario", diario),
        ("robar", robar),
        ("tiendaeco", tiendaeco),
        ("comprar", comprar),
        ("inventario", inventario),
        ("gacha", gacha),
        # Admin
        ("kick", kick),
        ("ban", ban),
        ("warn", warn),
        ("link", link),
        # Negocio
        ("premium", premium),
        ("tienda", tienda),
        ("soporte", soporte),
    ]

    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    logging.info("DANTE BOT iniciado ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
