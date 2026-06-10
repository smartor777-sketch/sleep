"""InnerCore auth bot: handles `/start <token>` deep-links from the web app.

Single-purpose: forward the Telegram user identity to the backend's
/auth/telegram/confirm endpoint, which fulfils the pending session.
"""

import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message


BOT_TOKEN = os.environ["BOT_TOKEN"]
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000").rstrip("/")
BACKEND_BOT_SECRET = os.environ["BACKEND_BOT_SECRET"]
WEB_URL = os.environ.get("WEB_URL", "https://app.innercore.art")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
TELEGRAM_PROXY = os.environ.get("TELEGRAM_PROXY") or None

CONFIRM_URL = f"{BACKEND_URL}/api/v1/auth/telegram/confirm"

logger = logging.getLogger("innercore.bot_auth")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=AiohttpSession(proxy=TELEGRAM_PROXY) if TELEGRAM_PROXY else None,
)
dp = Dispatcher()


def _greeting() -> str:
    return (
        "Привет! Это бот авторизации <b>InnerCore</b>.\n\n"
        f"Чтобы войти — открой <a href=\"{WEB_URL}\">{WEB_URL}</a> "
        "и нажми «Войти через Telegram»."
    )


@dp.message(CommandStart(deep_link=True))
async def on_start_with_token(message: Message, command: CommandObject) -> None:
    auth_token = (command.args or "").strip()
    user = message.from_user
    if not auth_token or not user:
        await message.answer(_greeting())
        return

    payload = {
        "auth_token": auth_token,
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                CONFIRM_URL,
                json=payload,
                headers={"Authorization": f"Bot {BACKEND_BOT_SECRET}"},
            )
    except httpx.HTTPError as e:
        logger.warning("backend unreachable: %s", e)
        await message.answer("⚠️ Не получилось связаться с сервером. Попробуй ещё раз через минуту.")
        return

    if r.status_code == 200:
        await message.answer(
            "✅ <b>Готово!</b>\nВернись в браузер — ты уже залогинен."
        )
        return

    if r.status_code == 404:
        await message.answer(
            "⌛ Сессия авторизации устарела. Открой сайт ещё раз и нажми «Войти через Telegram»."
        )
        return

    logger.error("confirm failed: %s %s", r.status_code, r.text)
    await message.answer(
        "⚠️ Внутренняя ошибка авторизации. Попробуй ещё раз с сайта."
    )


@dp.message(CommandStart())
async def on_plain_start(message: Message) -> None:
    await message.answer(_greeting(), disable_web_page_preview=True)


async def main() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logger.info("Starting InnerCore auth bot, backend=%s", BACKEND_URL)
    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    asyncio.run(main())
