import os
import yt_dlp
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# IMPORTANTE: En Render pones el token como "Variable de entorno" llamada TOKEN
T = os.getenv("TOKEN")

memes_vistos = set()
CATEGORIAS = ["meme", "memes", "dankmemes", "wholesomememes", "programmingmemes", "dogmemes", "catmemes"]

# ===== /START Y /HELP CON TEXTO =====
def start(update: Update, context: CallbackContext):
    caption = (
        "👋 **Hola Soy DANTE** 😈\n\n"
        "**Comandos Disponibles:**\n"
        "`/playaudio nombre` → Buscar música MP3\n"
        "`/video nombre/link` → Buscar/Descargar video\n"
        "`/meme` → Meme random\n"
        "`/gato` → Foto de gato random\n"
        "`/perro` → Foto de perro random\n"
        "`/receta ingrediente1 ingrediente2` → Buscar recetas\n"
        "`/que_tengo ingrediente1 ingrediente2` → Qué puedo cocinar\n"
        "💙💗 **Team Rem y Ram**"
    )
    update.message.reply_text(caption, parse_mode='Markdown')

# ===== COMANDOS NUEVOS DE INGREDIENTES =====
def receta(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usa: `/receta pollo tomate arroz`", parse_mode='Markdown')
        return
    ingredientes = ", ".join(context.args)
    respuesta = f"🔍 **Recetas con: {ingredientes}**\n\n"
    respuesta += f"1. **Salteado rápido**: Fríe todo junto con ajo, cebolla y sillao\n"
    respuesta += f"2. **Sopa casera**: Hierve con agua, sal, orégano y lo que tengas\n"
    respuesta += f"3. **Arroz chaufa**: Si tienes arroz de ayer queda perfecto"
    update.message.reply_text(respuesta)

def que_tengo(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usa: `/que_tengo huevo leche pan`", parse_mode='Markdown')
        return
    cosas = [i.lower() for i in context.args]
    respuesta = f"🍳 **Con {', '.join(cosas)} puedes hacer:**\n\n"
    if 'huevo' in cosas: respuesta += "• Tortilla\n• Huevos revueltos\n"
    if 'leche' in cosas and 'pan' in cosas: respuesta += "• Leche con pan\n• French toast\n"
    if 'pollo' in cosas: respuesta += "• Pollo frito\n• Saltado\n"
    if 'arroz' in cosas: respuesta += "• Arroz chaufa\n• Arroz con huevo\n"
    if len(respuesta) < 50: respuesta += "• Algo improvisado jaja\n"
    respuesta += "\nMándame más ingredientes para más ideas"
    update.message.reply_text(respuesta)

# ===== EL RESTO DE TU CODIGO =====
def playaudio(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usa: /playaudio nombre de la canción")
        return
    query = " ".join(context.args)
    msg = update.message.reply_text(f"Buscando opciones de: {query} ⏳")
    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']
        keyboard = []
        for i, video in enumerate(videos[:5]):
            title = video['title']
            keyboard.append([InlineKeyboardButton(f"{i+1}. {title[:50]}", callback_data=f"dl_{video['id']}")])
        msg.edit_text(f"Elige una opción para: **{query}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        msg.edit_text(f"❌ Error buscando: {e}")

def video(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usa: /video link o /video nombre del video")
        return
    query = " ".join(context.args)
    msg = update.message.reply_text(f"Buscando opciones de: {query} ⏳")
    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']
        keyboard = []
        for i, video in enumerate(videos[:5]):
            title = video['title'][:40]
            duration = video.get('duration', 0)
            mins, secs = divmod(duration, 60)
            size_mb = round(video.get('filesize_approx', 0) / 1024 / 1024)
            keyboard.append([InlineKeyboardButton(f"{i+1}. {title} [{mins}:{secs:02d}] ~{size_mb}MB", callback_data=f"vdl_{video['id']}")])
        msg.edit_text(f"Elige un video para: **{query}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        msg.edit_text(f"❌ Error buscando: {e}")

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split("_")
    if data[0] == "dl": tipo = "audio"
    elif data[0] == "vdl": tipo = "video"
    else: return
    video_id = data[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    query.edit_message_text(f"Descargando {tipo} ⏳")
    if tipo == "audio":
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'file.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]}
        ext = 'mp3'
    else:
        ydl_opts = {'format': 'best[height<=480]', 'outtmpl': 'file.%(ext)s', 'merge_output_format': 'mp4'}
        ext = 'mp4'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title')
            duration = info.get('duration', 0)
        filesize = os.path.getsize(f'file.{ext}')
        if tipo == "video" and filesize > 50 * 1024 * 1024:
            os.remove(f'file.{ext}')
            query.edit_message_text(f"{url}")
            return
        query.edit_message_text(f"✅ Subiendo: {title}")
        if tipo == "audio":
            context.bot.send_audio(chat_id=query.message.chat_id, audio=open(f'file.{ext}', 'rb'), title=title, duration=duration)
        else:
            context.bot.send_video(chat_id=query.message.chat_id, video=open(f'file.{ext}', 'rb'), caption=f"📹 {title}", duration=duration, supports_streaming=True)
        os.remove(f'file.{ext}')
    except Exception as e:
        query.edit_message_text(f"❌ Error: {e}")

def enviar_meme(context: CallbackContext, categoria, chat_id):
    msg = context.bot.send_message(chat_id=chat_id, text=f"Buscando meme de r/{categoria} 😂 ⏳")
    for _ in range(10):
        try:
            import requests
            resp = requests.get(f"https://meme-api.com/gimme/{categoria}")
            data = resp.json()
            meme_id = data.get("postLink")
            if meme_id and meme_id not in memes_vistos:
                memes_vistos.add(meme_id)
                if len(memes_vistos) > 200: memes_vistos.clear()
                keyboard = [[InlineKeyboardButton("➡️ Siguiente meme", callback_data=f"nextmeme_{categoria}")]]
                msg.delete()
                context.bot.send_photo(chat_id=chat_id, photo=data["url"], caption=f"🤣 {data['title']}\n👍 {data['ups']} upvotes | r/{data['subreddit']}", reply_markup=InlineKeyboardMarkup(keyboard))
                return
        except: pass
    msg.edit_text("❌ Me quedé sin memes nuevos. Prueba: /meme programación")

def meme(update: Update, context: CallbackContext):
    categoria = context.args[0] if context.args else random.choice(CATEGORIAS)
    enviar_meme(context, categoria, update.message.chat_id)

def next_meme_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    categoria = query.data.split("_")[1]
    query.message.delete()
    enviar_meme(context, categoria, query.message.chat_id)

def gato(update: Update, context: CallbackContext):
    msg = update.message.reply_text("Buscando michi 🐱 ⏳")
    try:
        import requests
        resp = requests.get("https://cataas.com/cat?json=true")
        data = resp.json()
        url = f"https://cataas.com{data['url']}"
        msg.delete()
        update.message.reply_photo(photo=url, caption="😼 Otro michi para ti")
    except: msg.edit_text("❌ Error")

def perro(update: Update, context: CallbackContext):
    msg = update.message.reply_text("Buscando perrito 🐶 ⏳")
    try:
        import requests
        resp = requests.get("https://dog.ceo/api/breeds/image/random")
        data = resp.json()
        msg.delete()
        update.message.reply_photo(photo=data["message"], caption="🐕 Woof! Aquí tienes")
    except: msg.edit_text("❌ Error")

def main():
    updater = Updater(T, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("playaudio", playaudio))
    dp.add_handler(CommandHandler("video", video))
    dp.add_handler(CommandHandler("meme", meme))
    dp.add_handler(CommandHandler("gato", gato))
    dp.add_handler(CommandHandler("perro", perro))
    dp.add_handler(CommandHandler("receta", receta))
    dp.add_handler(CommandHandler("que_tengo", que_tengo))
    dp.add_handler(CallbackQueryHandler(next_meme_handler, pattern="^nextmeme_"))
    dp.add_handler(CallbackQueryHandler(button_handler, pattern="^(dl_|vdl_)"))

    print("DANTE V3.9.1 iniciado - Con Recetas 💙💗")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
