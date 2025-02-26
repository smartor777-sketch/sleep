import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db

account_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@account_router.callback_query(F.data == 'account')
async def account_menu(callback: CallbackQuery,
                       i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    try:
        stats = await db.get_user_stats(user_id)
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        await callback.message.edit_text(i18n.error.db_error(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return

    if not stats:
        logger.error(f"User {user_id} has no stats in database.")
        await callback.message.edit_text(i18n.account.no_stats(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return

    message_text = i18n.account.title() + "\n\n"

    # Составляем сообщение динамически
    stat_fields = {
        'name': stats['first_name'],
        'reg_time': stats['reg_time'],
        'inviter': '🤷‍♂️' if stats['inviter'] == 'none' else stats['inviter'],
        'sub_type': '🤷‍♂️' if stats['sub_type'] == 'none' else stats['sub_type'],
        'sub_time': '🤷‍♂️' if stats['sub_time'] is None else stats['sub_time'],
        'dreams_count': stats['dreams_count'],
        'orders_count': stats['orders_count'],
        'orders_total': stats['orders_total'],
    }

    for key, value in stat_fields.items():
        message_text += getattr(i18n.account, key)(**{key: value}) + "\n"

    # Отправляем сообщение
    try:
        await callback.message.edit_text(message_text, reply_markup=kb.account_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()

    
@account_router.callback_query(F.data == 'subscription')
async def subscription_handler(callback: CallbackQuery,
                               i18n: TranslatorRunner):

    try:
        await callback.message.edit_text(i18n.subscription.types(), reply_markup=kb.subscription_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()


@account_router.callback_query(F.data.startswith('sub_'))
async def process_sub_button(callback: CallbackQuery,
                             i18n: TranslatorRunner):
    await callback.answer()