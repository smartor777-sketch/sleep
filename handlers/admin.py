from aiogram import Router, F
from aiogram.types import Message
from fluentogram import TranslatorRunner

from utils import db
from config import get_config, Admin

admin = get_config(Admin, 'admin')
admin_id = admin.id

admin_router = Router()

@admin_router.message(F.text == "/stats")
async def show_stats(message: Message):
    
    user_id = message.from_user.id
    
    # Проверка, является ли пользователь администратором
    if str(user_id) != str(admin_id):
        return

    # Если пользователь — админ, показываем статистику
    stats = await db.get_service_stats()
    response = (
        f"📊 Статистика сервиса:\n\n"
        f"👥 Пользователей: {stats['users_count']}\n"
        f"💤 Снов: {stats['dreams_count']}\n"
        f"💳 Оплаченных заказов: {stats['orders_count']}\n"
        f"💰 Сумма оплат: {stats['total_amount']}"
    )
    await message.answer(response)

@admin_router.message(F.text.startswith("/analyze_reset_"))
async def analyze_reset(message: Message):

    _, _, user_id = message.text.split('_')
    await db.reset_last_analyze_date(user_id)
    await message.answer(f"Последняя дата анализа пользователя {user_id} - сброшена")