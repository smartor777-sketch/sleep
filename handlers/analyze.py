import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner
from datetime import datetime, timedelta, timezone

from keyboards import keyboards as kb
from utils import db, analyze_dreams, AnalyzeSG
from aiogram.exceptions import TelegramAPIError
from config import get_config, Yandex


analyze_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


MAX_MESSAGE_LENGTH = 4096  # Максимальная длина сообщения для Telegram


@analyze_router.callback_query(F.data == 'analyze')
async def analyze_menu(callback: CallbackQuery,
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    await state.clear()
    
    try:
        await callback.message.edit_text(i18n.analyze.menu(), 
                                         reply_markup=kb.analyze_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()
    

@analyze_router.callback_query(F.data == 'select_role')
async def role_menu(callback: CallbackQuery,
                    i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    user_data = await db.get_user(user_id)
    gpt_role = user_data['gpt_role']

    try:
        await callback.message.edit_text(i18n.role.menu(gpt_role=gpt_role),
                                         reply_markup=kb.gpt_role(i18n))
    except TelegramBadRequest:
        await callback.answer()

    
@analyze_router.callback_query(F.data.startswith('role_'))
async def select_role(callback: CallbackQuery,
                      i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    _, new_role = callback.data.split('_')
    await db.update_role(new_role, user_id)
    try:
        await callback.message.edit_text(i18n.role.updated(),
                                         reply_markup=kb.analyze_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()   
             

@analyze_router.callback_query(F.data == 'edit_self_description')
async def self_description_process(callback: CallbackQuery,
                                   state: FSMContext,
                                   i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    try:
        user_data = await db.get_user(user_id)
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        await callback.message.edit_text(i18n.error.db_error(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return
    
    user_description = i18n.nodescription() if user_data['self_description'] == 'none' else user_data['self_description']
    
    await state.set_state(AnalyzeSG.edit_des)
    await callback.message.answer(user_description)
    await callback.message.answer(i18n.newdescription(),
                                  reply_markup=kb.back_to_analyze(i18n))
    await callback.answer()
    

@analyze_router.message(AnalyzeSG.edit_des)
async def edit_description(message: Message,
                           state: FSMContext,
                           i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_description = message.text

    if len(new_description) > 512:
        await message.answer(i18n.toolong.description())
        return
    
    await db.update_self_description(new_description, user_id)
    await state.clear()
    await message.answer(i18n.description.updated(),
                         reply_markup=kb.analyze_menu(i18n))


@analyze_router.callback_query(F.data == 'analyze_process')
async def analyze_process(callback: CallbackQuery,
                          i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    user_data = await db.get_user(user_id)
    last_use = user_data['last_analyze']
    if last_use is not None:  # Проверяем, что значение не NULL
        last_use = last_use.replace(tzinfo=timezone.utc)  # Добавляем UTC
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - last_use

    user_description = '' if user_data['self_description'] == 'none' else user_data['self_description']
    gpt_role = user_data['gpt_role']

    if time_difference < timedelta(hours=24):
        await callback.message.edit_text(i18n.error.timedelta(),
                                         reply_markup=kb.main_menu(i18n))
        return

    # Получаем последние 10 записей снов
    dreams = await db.get_last_10_dreams(user_id)
    if not dreams or len(dreams) == 0:
        try:
            await callback.message.edit_text(i18n.nodreams(), 
                                             reply_markup=kb.main_menu(i18n))
        except TelegramBadRequest:
            await callback.answer()
        return

    # Объединяем записи в один текст
    combined_text = "\n\n".join(dreams)
    await callback.message.edit_text(i18n.wait.result())

    # Анализируем текст с помощью YandexGPT
    yandex = get_config(Yandex, 'yandex')
    folder_id = yandex.folder_id
    api_key = yandex.api_key.get_secret_value()

    psychological_prompt = (
        "Ты — профессиональный психолог, специализирующийся на анализе снов. "
        "Твоя задача — интерпретировать сны пользователя, опираясь на психологические теории "
        "(например, Фрейд, Юнг). Ищи в снах отражение эмоций, скрытых желаний, страхов или "
        "внутренних конфликтов. Дай развёрнутый анализ, объясняя, как сны могут быть связаны "
        "с текущим состоянием пользователя или его жизненным опытом. "
        f"Описание пользователя: {user_description}. Вот список снов пользователя:\n"
    )

    esoteric_prompt = (
        "Ты — проводник в мир эзотерической философии и духовного самосовершенствования. "
        "Твоя задача — анализировать сны пользователя как проявления внутренней магии души "
        "и её пути к осознанию. Опирайся на идеи Карлоса Кастанеды (сновидения как врата к силе), "
        "Кибалиона (законы вселенной в отражении снов) и психоделический взгляд Теренса Маккенны "
        "(сны как диалог с иным измерением). Ищи в снах символы духовного роста, скрытые энергии "
        "и связь с магией реальности. Дай глубокий и вдохновляющий анализ."
        f"Описание пользователя: {user_description}. Вот список снов пользователя:\n"
    )

    intro_prompt = psychological_prompt if gpt_role == 'psychological' else esoteric_prompt

    try:
        # Логируем анализ
        logger.info(f"Analyzing dreams for user {user_id}, combined text length: {len(combined_text)}")
        
        analysis_result = await analyze_dreams(combined_text, intro_prompt, folder_id, api_key)
        if not analysis_result:
            raise ValueError("Empty analysis result from YandexGPT")
    except (TelegramAPIError, ValueError) as e:
        logger.error(f"Error during dream analysis for user {user_id}: {e}")
        await callback.message.edit_text(i18n.error.analysis_failed(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return

    logger.info(analysis_result.text)
    result_text = analysis_result.text

    # Если результат слишком длинный, отправляем несколькими сообщениями
    while len(result_text) > MAX_MESSAGE_LENGTH:
        await callback.message.answer(result_text[:MAX_MESSAGE_LENGTH])
        result_text = result_text[MAX_MESSAGE_LENGTH:]

    # Отправляем оставшийся результат
    await callback.message.answer(result_text, 
                                  reply_markup=kb.back_to_menu(i18n))
