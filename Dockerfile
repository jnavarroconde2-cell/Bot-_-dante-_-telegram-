FROM python:3.11-slim
WORKDIR /app
COPY telegram-bot/ /app/
RUN pip install --no-cache-dir python-telegram-bot openai Flask waitress Pillow aiohttp sympy yt-dlp qrcode
EXPOSE 5000
CMD ["python", "bot.py"]
