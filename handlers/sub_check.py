import logging

from aiogram import Router, Bot, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db, get_config, Channel, SubCheckSG, MainSG

start_router = Router()
channel_id = get_config(Channel, "channel")
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@start_router.message(CommandStart(deep_link_encoded=True))
async def command_start_getter(message: Message,
                               command: CommandObject,
                               state: FSMContext,
                               i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    logger.info(f'Referral data: {command}')
    await state.set_state(SubCheckSG.sub_check)

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
        await message.answer(i18n.main.menu(), reply_markup=kb.main_menu(i18n))


@start_router.callback_query(SubCheckSG.sub_check, F.data[:16] == "check_subscribe_")
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
        await callback.answer(text=i18n.error.generic())
        return

    if user_channel_status.status != 'left':
        username = callback.from_user.username
        first_name = callback.from_user.first_name
        
        await state.set_state(MainSG.main_menu)
        await db.add_user(payload, user_id, username, first_name)
        await callback.answer(i18n.main.menu(), reply_markup=kb.main_menu())
    else:
        await callback.answer(text=i18n.need.subscribe())
