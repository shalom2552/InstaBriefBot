import asyncio
import logging
from bot.database import init_db
from bot.telegram_bot import run_telegram_bot

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs.txt", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    init_db()
    print("✅ Database initialized. Starting Telegram bot...")
    asyncio.run(run_telegram_bot())

if __name__ == "__main__":
    main()
