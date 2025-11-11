import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db, AccountSG, AdminSG
from config import get_config, Admin

admin = get_config(Admin, 'admin')
admin_id = admin.id
account_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@account_router.callback_query(F.data == 'account')
async def account_menu(callback: CallbackQuery,
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    await state.clear()
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
    '''
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
    '''

    stat_fields = {
        'name': stats['first_name'],
        'reg_time': stats['reg_time'],
        # 'inviter': '🤷‍♂️' if stats['inviter'] == 'none' else stats['inviter'],
        # 'sub_type': '🤷‍♂️' if stats['sub_type'] == 'none' else stats['sub_type'],
        # 'sub_time': '🤷‍♂️' if stats['sub_time'] is None else stats['sub_time'],
        'dreams_count': stats['dreams_count'],
        'gpt_role': stats['gpt_role']
        # 'orders_count': stats['orders_count'],
        # 'orders_total': stats['orders_total'],
    }

    for key, value in stat_fields.items():
        message_text += getattr(i18n.account, key)(**{key: value}) + "\n"

    # Отправляем сообщение
    try:
        is_admin = (int(admin_id) == int(user_id))
        await callback.message.edit_text(message_text, reply_markup=kb.account_menu(i18n, admin_id))
    except TelegramBadRequest:
        await callback.answer()

    
@account_router.callback_query(F.data == 'subscription')
async def subscription_handler(callback: CallbackQuery,
                               i18n: TranslatorRunner):

    try:
        await callback.message.edit_text(i18n.subscription.types(), reply_markup=kb.subscription_menu(i18n))
    except TelegramBadRequest:
        await callback.answer()

    
@account_router.callback_query(F.data == 'ticket')
async def ticket_menu(callback: CallbackQuery,
                      state: FSMContext,
                      i18n: TranslatorRunner):
    
    user_id = callback.from_user.id

    await state.set_state(AccountSG.ticket)
    user_data = await db.get_user(user_id)
    ticket = user_data['ticket']
    ticket = i18n.no.ticket() if ticket is None else str(ticket)
    await callback.message.edit_text(i18n.ticket.menu(ticket=ticket), reply_markup=kb.back_to_account(i18n))


@account_router.message(AccountSG.ticket)
async def ticket_handler(message: Message, 
                         bot: Bot, 
                         state: FSMContext, 
                         i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    ticket = message.text

    try:
        # Обновляем тикет в базе
        await db.update_ticket(ticket, user_id)
        
        # Отправляем сообщение админу с кнопкой "Ответить"
        await bot.send_message(
            admin_id,
            text=f'#{user_id}:\n\n{ticket}',
            reply_markup=kb.reply_keyboard(user_id, i18n)
        )
        
        # Подтверждаем пользователю
        await message.answer(
            i18n.ticket.sended() or "Обращение отправлено!",
            reply_markup=kb.account_menu(i18n)
        )
        
    except TelegramBadRequest as e:
        logger.error(f"Failed to send ticket from user {user_id} to admin: {e}")
        await message.answer(
            i18n.error.ticket_send(),
            reply_markup=kb.account_menu(i18n)
        )
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(
            i18n.error.unexpected(),
            reply_markup=kb.account_menu(i18n)
        )
    
    finally:
        await state.clear()


# Хэндлер для кнопки "Ответить"
@account_router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket_start(callback: CallbackQuery, 
                             i18n: TranslatorRunner,
                             state: FSMContext):

    if str(callback.from_user.id) != str(admin_id):
        await callback.answer(i18n.error.only_admin(), show_alert=True)
        return
    
    # Извлекаем user_id из callback_data
    user_id = int(callback.data.split("_")[2])
    
    await state.update_data(user_id=user_id)
    await state.set_state(AdminSG.reply_ticket)
    await callback.message.answer("Введите ответ для пользователя:")
    await callback.answer()


# Хэндлер для получения текста ответа
@account_router.message(AdminSG.reply_ticket)
async def process_ticket_reply(message: Message, 
                               bot: Bot, 
                               state: FSMContext, 
                               i18n: TranslatorRunner):
    
    if str(message.from_user.id) != str(admin_id):
        await message.answer(i18n.error.only_admin())
        return
    
    reply_text = message.text
    data = await state.get_data()
    user_id = data.get("user_id")
    
    try:
        # Отправляем ответ пользователю
        await bot.send_message(
            user_id,
            text=i18n.ticket.answer(reply_text=reply_text)
        )
        
        # Удаляем тикет из базы
        await db.delete_ticket(user_id)
        
        # Уведомляем админа
        await message.answer(i18n.admin.answer())
        
    except TelegramBadRequest as e:
        logger.error(f"Failed to send reply to user {user_id}: {e}")
        await message.answer(i18n.error.bot_blocked())
    except Exception as e:
        logger.error(f"Unexpected error while replying to user {user_id}: {e}")
        await message.answer(i18n.error.unexpected())
    
    finally:
        await state.clear()


@account_router.callback_query(F.data.startswith('sub_'))
async def process_sub_button(callback: CallbackQuery):
    await callback.answer()