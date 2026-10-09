import os

from flask import Flask, jsonify
from waitress import serve


app = Flask(__name__)


@app.get("/")
@app.get("/healthz")
@app.get("/dante/healthz")
def health():
    return jsonify({"service": "DANTE Telegram Bot", "status": "ok"}), 200


def run_keep_alive():
    port = int(
        os.environ.get("DANTE_HEALTH_PORT")
        or os.environ.get("PORT")
        or "5000"
    )
    serve(app, host="0.0.0.0", port=port)
