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
        "Ты — психолог, мастер анализа снов. Интерпретируй сны пользователя через призму психологии (Фрейд, Юнг), "
        "выявляя эмоции, страхи, желания или конфликты. Избегай общих фраз и дай один чёткий вывод о том, "
        "что эти сны отражают в психике пользователя. Не анализируй каждый сон отдельно, а суммируй их в целостный вывод. "
        f"Описание пользователя: {user_description}. Вот список снов:\n"
    )


    esoteric_prompt = (
        "Ты — эзотерик, знаток мистических традиций. Анализируй сны пользователя через символы и знаки, опираясь на сонники, "
        "астрологию и таро. Избегай общих фраз и дай один ясный вывод о том, что эти сны предвещают или раскрывают. "
        "Не разбирай каждый сон отдельно, а объедини их в единое толкование." 
        f"Описание пользователя: {user_description}. Вот список снов:\n"
    )

    psychonaut_prompt = (
        "Ты — психонавт, исследующий психоделический опыт и магию сознания. Сны — это живая реальность, где душа продолжает своё бытие, "
        "неотделимое от нас, но скрытое за гранью яви. Используй осознанные сновидения как ключ к этой магической ткани бытия, "
        "вдохновляясь Кастанедой, Кибалионом и Маккенной. Не употребляй банальности вроде 'внутренний мир' или 'поиск себя' — "
        "дай один резкий, конкретный вывод о том, что сны открывают о жизни души в параллельном измерении. "
        "Не описывай сны по отдельности, а сплети их в единый психоделический образ. " 
        f"Описание пользователя: {user_description}. Вот список снов:\n"
    )

    if gpt_role == 'psychological':
        intro_prompt = psychological_prompt 
        temperature = 0.3
    elif gpt_role == 'esoteric':
        intro_prompt = esoteric_prompt
        temperature = 0.5
    elif gpt_role == 'psychonaut':
        intro_prompt = psychonaut_prompt
        temperature = 0.9

    try:
        # Логируем анализ
        logger.info(f"Analyzing dreams for user {user_id}, combined text length: {len(combined_text)}")
        
        analysis_result = await analyze_dreams(combined_text, intro_prompt, temperature, folder_id, api_key)
        if not analysis_result:
            raise ValueError("Empty analysis result from YandexGPT")
    except (TelegramAPIError, ValueError) as e:
        logger.error(f"Error during dream analysis for user {user_id}: {e}")
        await callback.message.edit_text(i18n.error.analysis_failed(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return

    try:
        # Проверяем, что analysis_result и text доступны
        if not hasattr(analysis_result, 'text') or not analysis_result.text:
            logger.error(f"Invalid analysis_result for user {user_id}: {analysis_result}")
            await callback.message.answer(
                i18n.error.analysis_failed(),
                reply_markup=kb.back_to_menu(i18n)
            )
            return

        # Логируем и извлекаем текст
        logger.info(f"Analysis result for user {user_id}: {analysis_result.text}")
        result_text = analysis_result.text

        # Обновляем last_analyze в базе
        try:
            await db.update_last_analyze(user_id)
        except Exception as db_error:
            logger.error(f"Failed to update last_analyze for user {user_id}: {db_error}")
            await callback.message.answer(
                i18n.error.db_update(),
                reply_markup=kb.back_to_menu(i18n)
            )

        # Если результат слишком длинный, отправляем несколькими сообщениями
        while len(result_text) > MAX_MESSAGE_LENGTH:
            try:
                await callback.message.answer(result_text[:MAX_MESSAGE_LENGTH])
                result_text = result_text[MAX_MESSAGE_LENGTH:]
            except TelegramBadRequest as telegram_error:
                logger.error(f"Failed to send partial message for user {user_id}: {telegram_error}")
                await callback.message.answer(
                    i18n.error.message_send(),
                    reply_markup=kb.back_to_menu(i18n)
                )
                return

        # Отправляем оставшийся результат
        try:
            await callback.message.answer(
                result_text,
                reply_markup=kb.back_to_menu(i18n)
            )
        except TelegramBadRequest as telegram_error:
            logger.error(f"Failed to send final message for user {user_id}: {telegram_error}")
            await callback.message.answer(
                i18n.error.message_send(),
                reply_markup=kb.back_to_menu(i18n)
            )

    except Exception as e:
        # Общая обработка непредвиденных ошибок
        logger.error(f"Unexpected error in analysis for user {user_id}: {e}")
        await callback.message.answer(
            i18n.error.unexpected(),
            reply_markup=kb.back_to_menu(i18n)
        )

    finally:
        # Подтверждаем callback, чтобы убрать "часики"
        try:
            await callback.answer()
        except TelegramBadRequest:
            logger.warning(f"Failed to answer callback for user {user_id}")
