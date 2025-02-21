import logging
import tempfile
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from fluentogram import TranslatorRunner

from utils import db, voice_to_text, clear_cache, MainSG, remove_file
from keyboards import keyboards as kb

main_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@main_router.callback_query(F.data == "main_menu")
async def any_text(callback: CallbackQuery,
                   state: FSMContext,
                   i18n: TranslatorRunner):
                   
    user_id = callback.from_user.id
    clear_cache(user_id)

    await state.set_state(MainSG.ready_for_dream)
    try:
        await callback.message.edit_text(i18n.main.menu(), reply_markup=kb.main_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()


@main_router.message(MainSG.ready_for_dream, F.content_type == ContentType.TEXT)
async def any_text(message: Message,
                   i18n: TranslatorRunner):
                   
    user_id = message.from_user.id
    dream_text = message.text
    
    # Если текст слишком короткий
    if len(dream_text) > 32:
        dream_text = dream_text[32:]
    logger.info(f"New Dream by user {user_id}: {dream_text}...")

    await db.create_dream(user_id, dream_text)
    await message.answer(i18n.dream.writed(), reply_markup=kb.edit_dream())


@main_router.message(MainSG.ready_for_dream, F.content_type == ContentType.VOICE)
async def any_voice(message: Message,
                    i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    try:
        file_info = await message.bot.get_file(message.voice.file_id)
        file_path = file_info.file_path
        file = await message.bot.download_file(file_path)
    except TelegramAPIError as e:
        logger.error(f"Error downloading voice file for user {user_id}: {e}")
        await message.answer(i18n.error.voice_download())
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_ogg_file:
        temp_ogg_file.write(file.getbuffer())
        temp_ogg_path = temp_ogg_file.name
    
    text = voice_to_text(temp_ogg_path)
    
    # Асинхронно удаляем файл
    asyncio.create_task(remove_file(temp_ogg_path))

    await db.create_dream(user_id, text)
    await message.answer(i18n.dream.writed(), reply_markup=kb.main_menu(i18n))
