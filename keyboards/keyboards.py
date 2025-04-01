from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from fluentogram import TranslatorRunner

from utils import day_emoji, get_cache
from config import get_config, Channel

channel_url = get_config(Channel, "channel")

def account_menu(i18n: TranslatorRunner, is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # builder.row(InlineKeyboardButton(text=i18n.sub.button(), callback_data="subscription"))
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="main_menu"))
    builder.row(InlineKeyboardButton(text=i18n.ticket.button(), callback_data="ticket"))

    if is_admin:
        builder.row(InlineKeyboardButton(text=i18n.stats.button(), callback_data="stats"))
        builder.row(InlineKeyboardButton(text=i18n.analyze.reset.button(), callback_data='analyze_reset'))
        
    return builder.as_markup()

# Клавиатура для совершения подписки и передачи payload, если он есть
def subscribe(i18n: TranslatorRunner, payload='none') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.sub.offer.button(), url=str(channel_url.url)))
    builder.row(InlineKeyboardButton(text=i18n.sub.check.button(), callback_data=f"check_subscribe_{payload}"))
    return builder.as_markup()


# Клавиатура главного меню
def main_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.dreams.button(), callback_data="dreams"))
    builder.row(InlineKeyboardButton(text=i18n.analyze.button(), callback_data="analyze"))
    builder.row(InlineKeyboardButton(text=i18n.account.button(), callback_data="account"))
    return builder.as_markup()

def dreams_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.dreams.pages.button(), callback_data="dreams_pages"))
    builder.row(InlineKeyboardButton(text=i18n.calendar.button(), callback_data="calendar"))
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="main_menu"))
    return builder.as_markup()

def first_analyze(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.analyze.button(), callback_data="first_analyze"))
    return builder.as_markup()

def start_use(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.start.use.button(), callback_data="main_menu"))
    return builder.as_markup()


def create_dreams_keyboard(dreams: list, page: int, total_dreams: int, i18n: TranslatorRunner):
    """
    Создаёт клавиатуру с 10 снами, кнопками "Назад" и "Вперёд", а также "Поиск" и "Назад в меню".
    :param dreams: список снов на текущей странице
    :param page: текущая страница (начиная с 0)
    :param total_dreams: общее количество снов пользователя
    :param i18n: объект для локализации
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с номерами и содержимым снов
    for idx, dream in enumerate(dreams, start=page * 10 + 1):
        # Обрезаем длинные сны для отображения
        short_dream = (dream[:30] + "...") if len(dream) > 30 else dream
        builder.button(text=f"{idx}. {short_dream}", callback_data=f"dream_{idx}")
    
    # Кнопки навигации ("Назад" и "Вперёд")
    dreams_per_page = 10
    has_prev = page > 0
    has_next = (page + 1) * dreams_per_page < total_dreams
    
    nav_buttons = []
    if has_prev:
        nav_buttons.append(InlineKeyboardButton(text=i18n.button.prev(), callback_data=f"dreams_page_{page - 1}"))
    if has_next:
        nav_buttons.append(InlineKeyboardButton(text=i18n.button.next(), callback_data=f"dreams_page_{page + 1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Кнопка "Поиск" и "Назад в меню"
    builder.row(
        InlineKeyboardButton(text=i18n.search.button(), callback_data="search"),
        InlineKeyboardButton(text=i18n.back.button(), callback_data="main_menu")
    )
    
    return builder.as_markup()


def calendar(year: int, 
             month: int, 
             i18n: TranslatorRunner, 
             user_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру календаря с эмодзи для дней, если они есть.
    """
    builder = InlineKeyboardBuilder()

    # Кнопки для переключения месяцев
    prev_month = (datetime(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_month = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)
    builder.row(
        InlineKeyboardButton(text="◀️", callback_data=f"calendar_{prev_month.year}_{prev_month.month}"),
        InlineKeyboardButton(text=f"{year}-{month:02d}", callback_data="ignore"),  # Заголовок месяца
        InlineKeyboardButton(text="▶️", callback_data=f"calendar_{next_month.year}_{next_month.month}")
    )

    # Получаем первый и последний день месяца
    first_day_of_month = datetime(year, month, 1)
    last_day_of_month = (first_day_of_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    # Собираем все кнопки в список
    buttons = []

    # Пустые кнопки для дней предыдущего месяца
    for _ in range(first_day_of_month.weekday()):
        buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Кнопки для дней текущего месяца
    for day in range(1, last_day_of_month.day + 1):
        cache_object = get_cache(user_id)
        emoji = day_emoji(user_id, str(day), cache_object)  # Предполагается, что функция day_emoji определена
        button_text = f"{day}{emoji}" if emoji else str(day)
        buttons.append(InlineKeyboardButton(text=button_text, callback_data=f"day_{year}_{month}_{day}"))

    # Пустые кнопки для дней следующего месяца (дополняем до полной недели)
    while len(buttons) % 7 != 0:
        buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Добавляем кнопки в builder с разбивкой по 7 (недели)
    for i in range(0, len(buttons), 7):
        builder.row(*buttons[i:i + 7])

    # Кнопка "Поиск" и "Назад"
    builder.row(
        InlineKeyboardButton(text=i18n.search.button(), callback_data="search"),
        InlineKeyboardButton(text=i18n.back.button(), callback_data="dreams")
    )

    return builder.as_markup()


def dreams_list(i18n: TranslatorRunner, dreams: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for dream in dreams:
        dream_id, title, emoji, = dream[0], dream[1], dream[3]
        button_text = f"{emoji} - {title}"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"dream_{dream_id}"))
    
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="calendar"))
    return builder.as_markup()


def dream_edit(i18n: TranslatorRunner, dream_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.edit.title.button(), callback_data=f"edit_tit_{dream_id}"),
                InlineKeyboardButton(text=i18n.edit.comment.button(), callback_data=f"edit_com_{dream_id}"))
    builder.row(InlineKeyboardButton(text=i18n.edit.content.button(), callback_data=f"edit_con_{dream_id}"))
    builder.row(InlineKeyboardButton(text=i18n.edit.cover.button(), callback_data=f"edit_cov_{dream_id}"),
                InlineKeyboardButton(text=i18n.edit.emoji.button(), callback_data=f"edit_emo_{dream_id}"))
    builder.row(InlineKeyboardButton(text=i18n.delete.button(), callback_data=f'delete_{dream_id}'),
                InlineKeyboardButton(text=i18n.back.button(), callback_data="calendar"))
    return builder.as_markup()

def delete_dream(i18n: TranslatorRunner, dream_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.confirm.button(), callback_data=f'confirm_{dream_id}'))
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data=f"dream_{dream_id}"))
    return builder.as_markup()

def analyze_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.analyze.process1.button(), callback_data="analyze_process_1"),
                InlineKeyboardButton(text=i18n.analyze.process3.button(), callback_data="analyze_process_3"),
                InlineKeyboardButton(text=i18n.analyze.process7.button(), callback_data="analyze_process_7"))
    builder.row(InlineKeyboardButton(text=i18n.getlast.analyze.button(), callback_data="get_last_analyze"))
    builder.row(InlineKeyboardButton(text=i18n.edit.self.description.button(), callback_data="edit_self_description"),
                InlineKeyboardButton(text=i18n.gpt.role.button(), callback_data="select_role"))
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="main_menu"))            
    return builder.as_markup()

def gpt_role(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.psychological.button(), callback_data="role_psychological"))
    builder.row(InlineKeyboardButton(text=i18n.esoteric.button(), callback_data="role_esoteric"))
    # builder.row(InlineKeyboardButton(text=i18n.psychonaut.button(), callback_data="role_psychonaut"))
    return builder.as_markup()

def subscription_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.month1.sub.button(), callback_data="sub_1"))
    builder.row(InlineKeyboardButton(text=i18n.month3.sub.button(), callback_data="sub_3"))
    builder.row(InlineKeyboardButton(text=i18n.month6.sub.button(), callback_data="sub_6"))
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="account"))
    return builder.as_markup()

def reply_keyboard(user_id: int, i18n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.answer.button(), callback_data=f"reply_ticket_{user_id}")
    return builder.as_markup()

def back_to_dream(i18n: TranslatorRunner, dream_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data=f"dream_{dream_id}"))
    return builder.as_markup()

def back_to_calendar(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data=f"calendar"))
    return builder.as_markup()

def back_to_search(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data=f"search"))
    return builder.as_markup()

def back_to_analyze(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="analyze"))
    return builder.as_markup()

def back_to_account(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="account"))
    return builder.as_markup()

def back_to_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.back.button(), callback_data="main_menu"))
    return builder.as_markup()