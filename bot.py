import os
import yt_dlp
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

T = os.getenv("TOKEN")

memes_vistos = set()
CATEGORIAS = ["meme", "memes", "dankmemes", "wholesomememes", "programmingmemes", "dogmemes", "catmemes"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(caption, parse_mode='Markdown')

async def receta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: `/receta pollo tomate arroz`", parse_mode='Markdown')
        return
    ingredientes = ", ".join(context.args)
    respuesta = f"🔍 **Recetas con: {ingredientes}**\n\n1. **Salteado rápido**\n2. **Sopa casera**\n3. **Arroz chaufa**"
    await update.message.reply_text(respuesta)

async def que_tengo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: `/que_tengo huevo leche pan`", parse_mode='Markdown')
        return
    cosas = [i.lower() for i in context.args]
    respuesta = f"🍳 **Con {', '.join(cosas)} puedes hacer:**\n\n"
    if 'huevo' in cosas: respuesta += "• Tortilla\n"
    if 'leche' in cosas and 'pan' in cosas: respuesta += "• Leche con pan\n"
    if 'pollo' in cosas: respuesta += "• Pollo frito\n"
    if 'arroz' in cosas: respuesta += "• Arroz chaufa\n"
    await update.message.reply_text(respuesta)

async def playaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /playaudio nombre de la canción")
        return
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"Buscando opciones de: {query} ⏳")
    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']
        keyboard = [[InlineKeyboardButton(f"{i+1}. {v['title'][:50]}", callback_data=f"dl_{v['id']}")] for i,v in enumerate(videos[:5])]
        await msg.edit_text(f"Elige una opción para: **{query}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /video link o /video nombre")
        return
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"Buscando opciones de: {query} ⏳")
    ydl_opts = {'default_search': 'ytsearch5', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            videos = info['entries']
        keyboard = []
        for i, v in enumerate(videos[:5]):
            duration = v.get('duration', 0)
            mins, secs = divmod(duration, 60)
            keyboard.append([InlineKeyboardButton(f"{i+1}. {v['title'][:40]} [{mins}:{secs:02d}]", callback_data=f"vdl_{v['id']}")])
        await msg.edit_text(f"Elige un video para: **{query}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    tipo = "audio" if data[0] == "dl" else "video"
    video_id = data[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    await query.edit_message_text(f"Descargando {tipo} ⏳")
    
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'file.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]} if tipo == "audio" else {'format': 'best[height<=480]', 'outtmpl': 'file.%(ext)s', 'merge_output_format': 'mp4'}
    ext = 'mp3' if tipo == "audio" else 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title')
        await query.edit_message_text(f"✅ Subiendo: {title}")
        if tipo == "audio":
            await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(f'file.{ext}', 'rb'), title=title)
        else:
            await context.bot.send_video(chat_id=query.message.chat_id, video=open(f'file.{ext}', 'rb'), caption=f"📹 {title}")
        os.remove(f'file.{ext}')
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = context.args[0] if context.args else random.choice(CATEGORIAS)
    await enviar_meme(context, categoria, update.message.chat_id)

async def enviar_meme(context: ContextTypes.DEFAULT_TYPE, categoria, chat_id):
    msg = await context.bot.send_message(chat_id=chat_id, text=f"Buscando meme de r/{categoria} 😂 ⏳")
    try:
        import requests
        resp = requests.get(f"https://meme-api.com/gimme/{categoria}")
        data = resp.json()
        keyboard = [[InlineKeyboardButton("➡️ Siguiente meme", callback_data=f"nextmeme_{categoria}")]]
        await msg.delete()
        await context.bot.send_photo(chat_id=chat_id, photo=data["url"], caption=f"🤣 {data['title']}", reply_markup=InlineKeyboardMarkup(keyboard))
    except: await msg.edit_text("❌ Error")

async def next_meme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categoria = query.data.split("_")[1]
    await query.message.delete()
    await enviar_meme(context, categoria, query.message.chat_id)

async def gato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Buscando michi 🐱 ⏳")
    try:
        import requests
        resp = requests.get("https://cataas.com/cat?json=true").json()
        url = f"https://cataas.com{resp['url']}"
        await msg.delete()
        await update.message.reply_photo(photo=url, caption="😼 Michi")
    except: await msg.edit_text("❌ Error")

async def perro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Buscando perrito 🐶 ⏳")
    try:
        import requests
        resp = requests.get("https://dog.ceo/api/breeds/image/random").json()
        await msg.delete()
        await update.message.reply_photo(photo=resp["message"], caption="🐕 Woof!")
    except: await msg.edit_text("❌ Error")

def main():
    app = ApplicationBuilder().token(T).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("playaudio", playaudio))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("meme", meme))
    app.add_handler(CommandHandler("gato", gato))
    app.add_handler(CommandHandler("perro", perro))
    app.add_handler(CommandHandler("receta", receta))
    app.add_handler(CommandHandler("que_tengo", que_tengo))
    app.add_handler(CallbackQueryHandler(next_meme_handler, pattern="^nextmeme_"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(dl_|vdl_)"))
    print("DANTE V4.0 iniciado - Con Recetas 💙💗")
    app.run_polling()

if __name__ == '__main__':
    main()
