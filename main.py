import runpy
import threading
from pathlib import Path

from keep_alive import run_keep_alive


ROOT_DIR = Path(__file__).resolve().parent


def main():
    thread = threading.Thread(
        target=run_keep_alive,
        name="dante-health-server",
        daemon=True,
    )
    thread.start()
    runpy.run_path(
        str(ROOT_DIR / "telegram-bot" / "bot.py"),
        run_name="__main__",
    )


if __name__ == "__main__":
    main()
