from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove
from datetime import datetime, timedelta
from fluentogram import TranslatorRunner

from utils import get_config, day_emoji, Channel

channel_url = get_config(Channel, "channel")


# Клавиатура для совершения подписки и передачи payload, если он есть
def subscribe(i18n: TranslatorRunner, 
              payload='none') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(i18n.subscription.offer(), url=str(channel_url.url)),
        InlineKeyboardButton(i18n.subscription.check(), callback_data=f"check_subscribe_{payload}")
    )


# Клавиатура главного меню
def main_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(i18n.calendar.button(), callback_data="calendar"),
        InlineKeyboardButton(i18n.account.button(), callback_data='account')
    )


def calendar(year: int, 
             month: int, 
             i18n: TranslatorRunner,
             user_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру календаря с эмодзи для дней, если они есть.
    """
    keyboard = InlineKeyboardMarkup(row_width=7)
    
    # Кнопки для переключения месяцев
    prev_month = (datetime(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
    
    keyboard.row(
        InlineKeyboardButton(text="◀️", callback_data=f"calendar_{prev_month.year}_{prev_month.month}"),
        InlineKeyboardButton(text="▶️", callback_data=f"calendar_{next_month.year}_{next_month.month}")
    )
    
    # Получаем первый и последний день месяца
    first_day_of_month = datetime(year, month, 1)
    last_day_of_month = (first_day_of_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    # Пустые кнопки для дней предыдущего месяца
    for _ in range(first_day_of_month.weekday()):
        keyboard.insert(InlineKeyboardButton(text=" ", callback_data="ignore"))
    
    # Кнопки для дней текущего месяца
    for day in range(1, last_day_of_month.day + 1):
        emoji = day_emoji(user_id, day)  # Получаем эмодзи для дня
        button_text = f"{day} {emoji}" if emoji else str(day)  # Добавляем эмодзи к тексту кнопки
        keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=f"day_{year}_{month}_{day}"))
    
    # Пустые кнопки для дней следующего месяца
    while len(keyboard.inline_keyboard[-1]) < 7:
        keyboard.insert(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Кнопка "Назад"
    keyboard.add(
        InlineKeyboardButton(i18n.search.button(), callback_data="search"),
        InlineKeyboardButton(i18n.back.button(), callback_data="main_menu")
        )
    
    return keyboard


def dreams_list(i18n: TranslatorRunner, 
                dreams: list) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(row_width=1)
    for dream in dreams:
        dream_id, title, emoji, create_time = dream[0], dream[1], dream[3], dream[4]
        button_text = f"{emoji}{create_time.strftime('%H:%M')} - {title}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"dream_{dream_id}"))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton(i18n.back.button(), callback_data="calendar"))
    return keyboard


def dream_edit(i18n: TranslatorRunner,
               dream_id: int) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(i18n.edit.title.button(), callback_data=f"edit_tit_{dream_id}"),
        InlineKeyboardButton(i18n.edit.title.button(), callback_data=f"edit_tit_{dream_id}"),
    )

    keyboard.add(
        InlineKeyboardButton(i18n.edit.content.button(), callback_data=f'edit_con_{dream_id}')
    )

    keyboard.add(
        InlineKeyboardButton(i18n.edit.cover.button(), callback_data=f'edit_cov_{dream_id}'),
        InlineKeyboardButton(i18n.edit.emoji.button(), callback_data=f'edit_emo_{dream_id}'),
    )

    keyboard.add(InlineKeyboardButton(i18n.back.button(), callback_data="calendar"))
    return keyboard


def back_to_dream(i18n: TranslatorRunner,
                  dream_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(i18n.back.button(), callback_data=f"dream_{dream_id}")
    )


def back_to_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(i18n.back.button(), callback_data=f"main_menu")
    )