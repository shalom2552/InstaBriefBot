import os
from dotenv import load_dotenv
from telethon import TelegramClient
from tqdm.asyncio import tqdm

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient("anon", api_id, api_hash)

async def fetch_messages_from_channel(channel, limit=100000, min_id=0, progress_callback=None):
    messages = []
    count = 0
    async with client:
        async for message in tqdm(client.iter_messages(channel, limit=limit, min_id=min_id)):
            if message.message:
                messages.append({
                    "id": message.id,
                    "channel": channel,
                    "date": str(message.date),
                    "text": message.message
                })
            count += 1
            if progress_callback and count % 500 == 0:
                await progress_callback(channel, count)

    return messages
