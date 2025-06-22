import os
import asyncio
import logging
from typing import Callable, Awaitable, Dict
from dotenv import load_dotenv
from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


from bot.fetcher import fetch_messages_from_channel
from bot.database import (
    search_messages_by_keywords,
    save_messages,
    get_last_fetched,
    update_last_fetched,
    get_all_channels,
    add_channel,
    remove_channel,
    get_stats_per_channel,
    get_recent_messages,
    get_unsummarized_messages, 
    update_last_summarized,
)
from bot.processor import extract_keywords, summarize

LIMIT = 1000
class AddChannelState(StatesGroup):
    waiting_for_channel_name = State()
    
class RemoveChannelState(StatesGroup):
    waiting_for_channel_name = State()

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USERS = set(map(int, os.getenv("AUTHORIZED_USER_IDS", "").split(",")))

router = Router()
last_keywords_per_user = {}

@router.startup()
async def notify_startup(dispatcher: Dispatcher, bot: Bot):
    for uid in AUTHORIZED_USERS:
        try:
            await bot.send_message(uid, "✅ הבוט הופעל מחדש ומוכן לשימוש.")
        except Exception:
            pass

def check_access(message: Message) -> bool:
    return message.from_user.id in AUTHORIZED_USERS

@router.message(Command("start"))
async def handle_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/latest")],
            [KeyboardButton(text="/sync"), KeyboardButton(text="/stats")],
            [KeyboardButton(text="/add"), KeyboardButton(text="/remove")],
            [KeyboardButton(text="/debug"), KeyboardButton(text="/help")],
        ],
        resize_keyboard=True
    )
    await message.answer("👋 ברוך הבא! בחר פעולה מהתפריט:", reply_markup=keyboard)

@router.message(Command("help"))
async def handle_help(message: Message):
    help_text = (
        "<b>📌 רשימת פקודות:</b>\n\n"
        "/start – התחל שימוש בבוט\n"
        "/sync – סנכרון הודעות חדשות מכל הערוצים\n"
        "/latest – סיכום חכם של העדכונים האחרונים\n"
        "/add – הוסף ערוץ חדשות לרשימה\n"
        "/remove – הסר ערוץ מרשימת המעקב\n"
        "/debug – הצג את מילות המפתח האחרונות שזוהו\n"
        "/stats – סטטיסטיקה של ההודעות בערוצים\n"
        "/help – הסבר על הפקודות"
    )
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("channels"))
async def handle_channels(message: Message):
    if not check_access(message): return
    channels = get_all_channels()
    if not channels:
        await message.answer("📭 אין ערוצים ברשימה כרגע.")
    else:
        await message.answer("📡 ערוצים פעילים:\n" + "\n".join(channels))

@router.message(Command("add"))
async def handle_add_start(message: Message, state: FSMContext):
    if not check_access(message): return
    await state.set_state(AddChannelState.waiting_for_channel_name)
    await message.answer("📥 אנא שלח את שם הערוץ שברצונך להוסיף (כולל @)")

@router.message(AddChannelState.waiting_for_channel_name)
async def handle_add_channel_name(message: Message, state: FSMContext):
    if not check_access(message): return
    name = message.text.strip()
    channels = get_all_channels()
    if not name.startswith("@"):
        await message.answer("❌ שם הערוץ צריך להתחיל ב־@. נסה שוב.")
        return
    if name in channels:
        await message.answer("⚠️ הערוץ כבר קיים.")
    else:
        add_channel(name)
        await message.answer(f"✅ הערוץ {name} נוסף לרשימה.")
        logging.info(f"[{message.from_user.id}] ➕ הוסיף ערוץ: {name}")
    await state.clear()

@router.message(Command("remove"))
async def handle_remove_start(message: Message, state: FSMContext):
    if not check_access(message): return
    await state.set_state(RemoveChannelState.waiting_for_channel_name)
    await message.answer("🗑️ אנא שלח את שם הערוץ שברצונך להסיר (כולל @)")

@router.message(RemoveChannelState.waiting_for_channel_name)
async def handle_remove_channel_name(message: Message, state: FSMContext):
    if not check_access(message): return
    name = message.text.strip()
    channels = get_all_channels()
    if name not in channels:
        await message.answer("⚠️ הערוץ לא נמצא ברשימה.")
    else:
        remove_channel(name)
        await message.answer(f"🗑️ הערוץ {name} הוסר מהרשימה.")
        logging.info(f"[{message.from_user.id}] 🗑️ מחק ערוץ: {name}")
    await state.clear()

@router.message(Command("debug"))
async def handle_debug(message: Message):
    user_id = message.from_user.id
    keywords = last_keywords_per_user.get(user_id)

    if not keywords:
        await message.answer("אין מילות מפתח זמינות כרגע.")
        return

    messages = search_messages_by_keywords(keywords, limit=1)
    count = len(search_messages_by_keywords(keywords, limit=1000))

    if messages:
        latest = messages[0]
        summary = latest["text"][:100] + "..." if len(latest["text"]) > 100 else latest["text"]
        date = latest["date"]
    else:
        summary = "לא נמצאו הודעות."
        date = "-"

    await message.answer(
        f"""🛠️ Debug:
- מילות מפתח: {', '.join(keywords)}
- נמצאו {count} הודעות רלוונטיות
- תאריך הודעה אחרונה: {date}
- דוגמה: {summary}"""
    )

@router.message(Command("stats"))
async def handle_stats(message: Message):
    if not check_access(message): return
    stats = get_stats_per_channel()
    if not stats:
        await message.answer("📭 אין נתונים זמינים.")
        return
    lines = [f"{channel}: {count} הודעות" for channel, count in stats]
    await message.answer("📊 מספר הודעות שמורות לפי ערוץ:\n" + "\n".join(lines))

@router.message(Command("sync"))
async def handle_sync(message: Message):
    if not check_access(message): return
    try:
        logging.info(f"[{message.from_user.id}] 🔄 התחיל סנכרון ערוצים.")
        status_msg = await message.answer("🔄 מתחיל סנכרון ערוצים...")
        report = []
        channels = get_all_channels()
        total_channels = len(channels)
        total_expected = total_channels * LIMIT
        last_percent_displayed = -1
        all_new_messages = []

        if not channels:
            await status_msg.edit_text("📭 אין ערוצים פעילים לסנכרון. השתמש ב־/add כדי להוסיף.")
            return

        for index, channel in enumerate(channels):
            async def progress_callback(_, count):
                nonlocal last_percent_displayed
                total_progress = (index * LIMIT) + count
                percent = min(int((total_progress / total_expected) * 100), 100)
                if percent != last_percent_displayed:
                    last_percent_displayed = percent
                    bar = "▓" * (percent // 10) + "░" * ((100 - percent) // 10)
                    await status_msg.edit_text(f"📡 סורק... {percent}%\n{bar}")

            last_id = get_last_fetched(channel)
            messages = await fetch_messages_from_channel(
                channel,
                limit=LIMIT,
                min_id=last_id,
                progress_callback=progress_callback
            )
            inserted = save_messages(messages)
            if inserted > 0:
                all_new_messages.extend(messages)
                update_last_fetched(channel, messages[-1]['id'])
            report.append(f"{channel}: ⬆️ {inserted} הודעות חדשות")
            logging.info(f"[{message.from_user.id}] 📡 {channel}: {inserted} הודעות חדשות נשמרו.")

        final_text = "✅ עדכון הסתיים:\n\n" + "\n".join(report)
        if status_msg.text != final_text:
            await status_msg.edit_text(final_text)

    except Exception as e:
        await message.answer(f"❌ שגיאה בסנכרון.\n{e}")
        logging.error(f"[{message.from_user.id}] ❌ שגיאה בסנכרון: {e}")
        
@router.message(Command("latest"))
async def handle_latest(message: Message):
    if not check_access(message): return
    try:
        logging.info(f"[{message.from_user.id}] 📥 ביקש סיכום של העדכונים האחרונים.")

        user_id = message.from_user.id
        channels = get_all_channels()

        all_messages = []
        latest_per_channel = {}

        for channel in channels:
            messages = get_unsummarized_messages(user_id, channel)
            if messages:
                all_messages.extend(messages)
                latest_per_channel[channel] = max(m["id"] for m in messages)

        if not all_messages:
            await message.answer("לא נמצאו הודעות חדשות לסיכום.")
            return

        summary = summarize("סכם לי את החדשות של ההודעות.", all_messages)
        await message.answer(f"🗞️ סיכום עדכונים אחרונים:\n\n{summary}")

        # עדכן נקודת הסיכום האחרונה לכל ערוץ
        for channel, last_id in latest_per_channel.items():
            update_last_summarized(user_id, channel, last_id)

    except Exception as e:
        await message.answer(f"❌ שגיאה בעת שליפת הסיכום.\n{e}")
        logging.error(f"[{message.from_user.id}] ❌ שגיאה ב־/latest: {e}")

@router.message(F.text)
async def handle_message(message: Message):
    if not check_access(message): return
    question = message.text
    logging.info(f"[{message.from_user.id}] ❓ שאלה: {question}")
    await message.answer("בודק...")
    
    try:
        keywords = extract_keywords(question)
        logging.info(f"[{message.from_user.id}] 🔑 מילות מפתח: {keywords}")
        last_keywords_per_user[message.from_user.id] = keywords

        messages = search_messages_by_keywords(keywords, limit=20)

        if not messages:
            await message.answer("לא נמצאו תוצאות רלוונטיות.")
            return

        answer = summarize(question, messages)
        logging.info(f"[{message.from_user.id}] ✅ תשובה נשלחה.")
        await message.answer(answer)
    except Exception as e:
        logging.error(f"[{message.from_user.id}] ❌ שגיאה בטיפול בשאלה: {e}")
        await message.answer(f"שגיאה בטיפול בשאלה:\n{e}", message.bot)      

async def run_telegram_bot():
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(ErrorLoggingMiddleware())
    dp.include_router(router)
    await dp.start_polling(bot)

class ErrorLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict], Awaitable],
        event: Update,
        data: Dict
    ):
        try:
            return await handler(event, data)
        except Exception as e:
            logging.exception(f"[ERROR] {e}")
            admin_id = int(os.getenv("ADMIN_ID", ""))
            if admin_id:
                try:
                    await event.bot.send_message(admin_id, f"❌ שגיאה לא צפויה:\n{e}")
                except Exception as notify_err:
                    logging.warning(f"[ERROR notifying admin]: {notify_err}")
            raise