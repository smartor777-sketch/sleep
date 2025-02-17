import logging 

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import CalendarSG, db, cache, clear_cache, get_cache, update_cache

calendar = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@calendar.callback_query(F.data =='calendar')
async def calendar_inline(callback: CallbackQuery,
                          state: FSMContext): 

    _, year, month = callback.data.split('_')
    user_id = callback.from_user.id
    await state.set_state(CalendarSG.calendar)

    logger.info(f"Current month: {year}-{month}")

    await db.load_month(user_id)
    keyboard = kb.calendar(int(year), int(month))
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@calendar.callback_query(CalendarSG.calendar, F.data[:5] == 'day_')
async def day_inline(callback: CallbackQuery,
                     state: FSMContext,
                     i18n: TranslatorRunner):

    _, year, month, day = callback.data.split('_')
    selected_date = f"{year}-{month}-{day}"
    user_id = callback.from_user.id
    await state.set_state(CalendarSG.day)
    
    logger.info(f"Selected day: {selected_date}")

    # Получаем записи за выбранный день
    dreams = await db.get_dreams(user_id, selected_date)
    
    if not dreams:
        await callback.message.answer(i18n.no.dreams(selected_date))
        return

    # Создаем клавиатуру с записями
    keyboard = kb.dreams_list(i18n, dreams)
    
    # Отправляем сообщение с клавиатурой
    await callback.message.answer(i18n.dreams.day(selected_date), reply_markup=keyboard)


@calendar.callback_query(CalendarSG.Day, F.data[:5] == 'dream_')
async def dream_inline(callback: CallbackQuery,
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    dream_id = callback.data[5:]