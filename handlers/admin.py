import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db, AdminSG
from config import get_config, Admin


admin = get_config(Admin, 'admin')
admin_id = admin.id
admin_router = Router()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@admin_router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery,
                     i18n: TranslatorRunner):
    user_id = callback.from_user.id
    
    # Проверка, является ли пользователь администратором
    if str(user_id) != str(admin_id):
        return

    try:
        # Получение статистики из базы данных
        stats = await db.get_service_stats()
        response = (
            f"📊 Статистика сервиса:\n\n"
            f"👥 Пользователей: {stats['users_count']}\n"
            f"💤 Снов: {stats['dreams_count']}\n"
            f"💳 Оплаченных заказов: {stats['orders_count']}\n"
            f"💰 Сумма оплат: {stats['total_amount']}"
        )
        # Отправка сообщения
        await callback.message.edit_text(response, reply_markup=kb.back_to_account(i18n))
    except Exception as e:
        # Обработка любых ошибок (например, проблемы с БД или Telegram API)
        await callback.message.edit_text(
            i18n.error.stats.failed(),  # Предполагаю, что у тебя есть перевод для ошибки
            reply_markup=kb.back_to_account(i18n)
        )
        logger.info(f"Ошибка в show_stats: {e}")  # Логирование для отладки


@admin_router.callback_query(F.data == "analyze_reset")
async def analyze_reset(callback: CallbackQuery,
                        i18n: TranslatorRunner,
                        state: FSMContext):
    try:
        await state.set_state(AdminSG.enter_user_id)
        await callback.message.edit_text(
            i18n.enter.userid(),
            reply_markup=kb.back_to_menu(i18n)
        )
    except Exception as e:
        # Если редактирование сообщения не удалось
        await callback.message.answer(
            i18n.error.db_error(),  # Универсальное сообщение об ошибке
            reply_markup=kb.back_to_menu(i18n)
        )
        logger.info(f"Ошибка в analyze_reset: {e}")


@admin_router.message(AdminSG.enter_user_id)
async def user_id_handler(message: Message,
                          i18n: TranslatorRunner,
                          state: FSMContext):
    try:
        # Парсинг user_id из текста
        try:
            _, _, user_id = message.text.split('_')
            user_id = int(user_id)  # Проверяем, что user_id — число
        except (ValueError, IndexError):
            await message.answer(i18n.error.invalid.userid())
            return

        # Сброс даты анализа в базе данных
        await db.reset_last_analyze_date(str(user_id))
        await state.clear()
        await message.answer(i18n.analyze.reset.complete(user_id=user_id))
    except Exception as e:
        # Обработка ошибок базы данных или Telegram API
        await message.answer(i18n.error.db_error())
        await state.clear()  # Очищаем состояние, чтобы не застрять
        logger.info(f"Ошибка в user_id_handler: {e}")