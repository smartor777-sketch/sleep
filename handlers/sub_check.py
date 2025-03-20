import logging

from aiogram import Router, Bot, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import CallbackQuery, Message, ContentType
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db, StartSG, MainSG, analyze_dreams
from config import get_config, Channel, Yandex

start_router = Router()
channel_id = get_config(Channel, "channel")
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

MAX_MESSAGE_LENGTH = 4096

@start_router.message(CommandStart(deep_link_encoded=True))
async def command_start_getter(message: Message,
                               command: CommandObject,
                               state: FSMContext,
                               i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    logger.info(f'Referral data: {command}')
    await state.set_state(StartSG.sub_check)

    if command.args:
        logger.info(f'CommandObject is {command}')
        args = command.args
        payload = decode_payload(args)
    else:
        payload = None

    user = await db.get_user(user_id)
    logger.info(f'User from database {user}')

    if user is None:
        await message.answer(i18n.channel.subscription(), reply_markup=kb.subscribe(i18n, payload))
    else:
        await state.set_state(MainSG.ready_for_dream)
        await message.answer(i18n.main.menu(), reply_markup=kb.main_menu(i18n))


@start_router.callback_query(StartSG.sub_check, F.data[:16] == "check_subscribe_")
async def check_subscribe(callback: CallbackQuery,
                          state: FSMContext,
                          i18n: TranslatorRunner,
                          bot: Bot):
    
    user_id = callback.from_user.id
    payload = callback.data.split("_")[-1]
    
    try:
        user_channel_status = await bot.get_chat_member(chat_id=str(channel_id.id), user_id=user_id)
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        await callback.message.answer(text=i18n.error.generic())
        return

    if user_channel_status.status != 'left':
        username = callback.from_user.username
        first_name = callback.from_user.first_name
        
        await state.set_state(MainSG.ready_for_dream)
        await db.add_user(payload, user_id, username, first_name)
        try:
            await state.set_state(StartSG.edit_des)
            await callback.message.edit_text(i18n.first.newdescription())
        except TelegramBadRequest:
            await callback.answer()
    
    else:
        await callback.message.answer(text=i18n.need.subscribe())


@start_router.message(StartSG.edit_des)
async def first_edit_description(message: Message,
                                 state: FSMContext,
                                 i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_description = message.text

    if len(new_description) > 512:
        await message.answer(i18n.toolong.description())
        return
    
    await db.update_self_description(new_description, user_id)
    await state.set_state(StartSG.first_dream)
    await message.answer(i18n.first.dream())


@start_router.message(StartSG.first_dream, F.content_type == ContentType.TEXT)
async def first_any_text(message: Message,
                         state: FSMContext,
                         i18n: TranslatorRunner):
                   
    user_id = message.from_user.id
    dream_text = message.text

    try:
        await db.create_dream(user_id, dream_text)
        await state.set_state(StartSG.first_analyze)
        await message.answer(
            i18n.first.analyze(),
            reply_markup=kb.first_analyze(i18n)
        )
    except Exception as e:
        logger.error(f"Failed to create dream for user {user_id}: {e}")
        await message.answer(
            i18n.error.dream_save(),
            reply_markup=kb.first_analyze(i18n)
        )

@start_router.callback_query(StartSG.first_analyze, F.data == 'first_analyze')
async def first_analyze(callback: CallbackQuery,
                        state: FSMContext,
                        i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    try:
        user_data = await db.get_user(user_id)
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        await callback.message.edit_text(i18n.error.db_error(), 
                                         reply_markup=kb.back_to_menu(i18n))
    
    user_description = '' if user_data['self_description'] == 'none' else user_data['self_description']

    dreams = await db.get_last_dreams(user_id, 1)
    if not dreams or len(dreams) == 0:
        try:
            await callback.message.edit_text(i18n.nodreams(), 
                                             reply_markup=kb.main_menu(i18n))
        except TelegramBadRequest:
            await callback.answer()
        return
    
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

    logger.info(dreams)

    try:
        analysis_result = await analyze_dreams(dreams, psychological_prompt, 0.4, folder_id, api_key)
        if not analysis_result:
            raise ValueError("Empty analysis result from YandexGPT")
    except (TelegramAPIError, ValueError) as e:
        logger.error(f"Error during dream analysis for user {user_id}: {e}")
        await callback.message.answer(i18n.error.analysis_failed(), 
                                      reply_markup=kb.start_use(i18n))
        return

    try:
        # Проверяем, что analysis_result и text доступны
        if not hasattr(analysis_result, 'text') or not analysis_result.text:
            logger.error(f"Invalid analysis_result for user {user_id}: {analysis_result}")
            await callback.message.answer(
                i18n.error.analysis_failed(),
                reply_markup=kb.start_use(i18n)
            )
            return
        
        if analysis_result.status.name == 'CONTENT_FILTER':
            logger.error(f"CONTENT_FILTER error for user {user_id}: {analysis_result.status}")
            await callback.message.answer(
                i18n.error.content_filter(),
                reply_markup=kb.start_use(i18n)
            )
            return

        result_text = analysis_result.text

        # Обновляем last_analyze в базе
        try:
            await db.update_last_analyze_data(result_text, user_id)
            await db.update_last_analyze(user_id)
        except Exception as db_error:
            logger.error(f"Failed to update last_analyze for user {user_id}: {db_error}")
            await callback.message.answer(
                i18n.error.db_update(),
                reply_markup=kb.start_use(i18n)
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
                    reply_markup=kb.start_use(i18n)
                )
                return

        # Отправляем оставшийся результат
        try:
            await callback.message.answer(
                result_text,
                reply_markup=kb.start_use(i18n)
            )
        except TelegramBadRequest as telegram_error:
            logger.error(f"Failed to send final message for user {user_id}: {telegram_error}")
            await callback.message.answer(
                i18n.error.message_send(),
                reply_markup=kb.start_use(i18n)
            )

    except Exception as e:
        # Общая обработка непредвиденных ошибок
        logger.error(f"Unexpected error in analysis for user {user_id}: {e}")
        await callback.message.answer(
            i18n.error.unexpected(),
            reply_markup=kb.start_use(i18n)
        )

    finally:
        # Подтверждаем callback, чтобы убрать "часики"
        try:
            await callback.answer()
        except TelegramBadRequest:
            logger.warning(f"Failed to answer callback for user {user_id}")

