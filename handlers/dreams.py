import logging 

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from fluentogram import TranslatorRunner
from datetime import datetime

from keyboards import keyboards as kb
from utils import CalendarSG, db, cache_object, get_cache, is_emoji


dreams_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@dreams_router.callback_query(F.data == 'dreams')
async def dreams_menu(callback: CallbackQuery,
                      state: FSMContext,
                      i18n: TranslatorRunner):
    
    await state.clear()
    try:
        await callback.message.edit_text(i18n.dreams.menu(), reply_markup=kb.dreams_menu(i18n))
    except TelegramBadRequest:
        await callback.message.answer(i18n.dreams.menu(), reply_markup=kb.dreams_menu(i18n))


@dreams_router.callback_query(F.data == "dreams_pages")
async def show_dreams(callback: CallbackQuery, 
                      i18n: TranslatorRunner, 
                      state: FSMContext):
    
    await state.update_data(source='dreams_pages')
    user_id = callback.from_user.id
    page = 0  # Начинаем с первой страницы
    dreams_per_page = 10

    try:
        total_dreams = await db.count_total_dreams(user_id)

        # Получаем первые 10 снов с id и content
        dreams = await db.get_last_dreams(user_id, dreams_per_page, page * dreams_per_page)
        
        if not dreams:
            await callback.message.edit_text(i18n.dreams.empty())
            return
        
        # Сохраняем текущую страницу и общее количество в состоянии
        await state.update_data(page=page, total_dreams=total_dreams)
        
        # Создаём и отправляем клавиатуру
        keyboard = kb.create_dreams_keyboard(dreams, page, total_dreams, i18n)
        await callback.message.edit_text(i18n.dreams.list(), reply_markup=keyboard)
    
    except Exception as e:
        await callback.message.edit_text(i18n.error.generic())
        logger.error(f"Ошибка в show_dreams: {e}")


# Обработчик переключения страниц
@dreams_router.callback_query(F.data.startswith("dreams_page_"))
async def switch_dreams_page(callback: CallbackQuery, 
                             i18n: TranslatorRunner, 
                             state: FSMContext):
    
    user_id = callback.from_user.id
    dreams_per_page = 10
    
    # Получаем номер страницы из callback_data
    page = int(callback.data.split("_")[-1])
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        total_dreams = data.get("total_dreams", 0)
        
        # Получаем сны для текущей страницы
        dreams = await db.get_last_dreams(user_id, dreams_per_page, page * dreams_per_page)
        
        if not dreams:
            await callback.message.edit_text(i18n.nodreams())
            return
        
        # Обновляем страницу в состоянии
        await state.update_data(page=page)
        
        # Создаём и отправляем клавиатуру
        keyboard = kb.create_dreams_keyboard(dreams, page, total_dreams, i18n)
        await callback.message.edit_text(i18n.dreams.list(), reply_markup=keyboard)
    
    except Exception as e:
        await callback.message.edit_text(i18n.error.generic())
        logger.error(f"Ошибка в switch_dreams_page: {e}")


@dreams_router.callback_query(F.data == 'calendar')
async def calendar_inline(callback: CallbackQuery,
                          state: FSMContext,
                          i18n: TranslatorRunner):
    
    await state.clear()
    now = datetime.now()
    year, month = now.year, now.month  # Текущий год и месяц
    user_id = callback.from_user.id

    logger.info(f"Current month: {year}-{month}")

    try:
        await db.load_month(user_id, int(year), int(month))
    except Exception as e:
        logger.error(f"Error loading data for user {user_id}, year {year}, month {month}: {e}")
        await callback.message.edit_text(i18n.error.loading_data(), 
                                         reply_markup=kb.back_to_menu(i18n))
        return
    
    # Обновляем сообщение с календарем
    keyboard = kb.calendar(int(year), int(month), i18n, user_id)
    try:
        await callback.message.edit_text(i18n.calendar(), reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(i18n.calendar(), reply_markup=keyboard)


@dreams_router.callback_query(F.data.startswith('calendar_'))
async def calendar_inline(callback: CallbackQuery,
                          state: FSMContext,
                          i18n: TranslatorRunner):
    
    await state.clear()
    _, year, month = callback.data.split('_')
    user_id = callback.from_user.id

    logger.info(f"Current month: {year}-{month}")

    try:
        await db.load_month(user_id, int(year), int(month))
    except Exception as e:
        logger.error(f"Error loading data for user {user_id}, year {year}, month {month}: {e}")
        await callback.message.answer(i18n.error.loading_data())
        return
    
    # Обновляем сообщение с календарем
    keyboard = kb.calendar(int(year), int(month), i18n, user_id)

    try:
        await callback.message.edit_text(i18n.calendar(), reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.answer()


@dreams_router.callback_query(F.data.startswith('day_'))
async def day_inline(callback: CallbackQuery,
                     state: FSMContext,
                     i18n: TranslatorRunner):
    
    await state.clear()
    await state.update_data(source='calendar')
    _, year, month, day = callback.data.split('_')
    selected_date = f"{year}-{month}-{day}"
    user_id = callback.from_user.id 
    dreams_cache = get_cache(user_id)
    
    logger.info(f"USER: {user_id} - Selected day: {day}, month: {month}, year: {year}")

    try:
        dreams = dreams_cache[day]
    except KeyError:
        await callback.message.edit_text(i18n.no.dreams(selected_date=selected_date), 
                                         reply_markup=kb.back_to_calendar(i18n))
        return

    logger.info(f"Dreams of user {user_id}: {dreams}")

    if not dreams:
        try:
            await callback.message.edit_text(i18n.no.dreams(selected_date=selected_date), 
                                             reply_markup=kb.back_to_calendar(i18n))
        except TelegramBadRequest:
            await callback.answer()
        return

    # Создаем клавиатуру с записями
    keyboard = kb.dreams_list(i18n, dreams)
    
    # Отправляем сообщение с клавиатурой
    try:
        await callback.message.edit_text(i18n.dreams.day(selected_date=selected_date), reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.answer()


@dreams_router.callback_query(F.data.startswith('dream_'))
async def dream_inline(callback: CallbackQuery, 
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    state_data = await state.get_data()
    source = state_data['calendar']

    await state.clear()
    user_id = callback.from_user.id
    dream_id = callback.data[6:]
    user_cache = get_cache(user_id)

    logger.info(f"User {user_id} select dream {dream_id}")

    try:
        dreams_dict = {str(dream[0]): dream for day, dreams in user_cache.items() for dream in dreams}
    except KeyError:
        await callback.message.edit_text(i18n.dream.notfound(), 
                                         reply_markup=kb.back_to_calendar(i18n))
        return
    
    found_dream = dreams_dict.get(dream_id)

    if not found_dream:
        try:
            await callback.message.edit_text(i18n.dream.notfound(), 
                                             reply_markup=kb.back_to_calendar(i18n))
        except TelegramBadRequest:
            await callback.answer()
        return

    dream_id, title, content, emoji, comment, cover, create_time = found_dream
    message_text = (
        f"📅 {create_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"{emoji} {title} {emoji}\n\n"
        f"📝 {content}\n\n"
        f"{comment}"
    )

    if cover:
        await callback.message.answer_photo(cover, 
                                            caption=message_text, 
                                            reply_markup=kb.dream_edit(i18n, dream_id, source))
    else:
        await callback.message.answer(message_text, 
                                      reply_markup=kb.dream_edit(i18n, dream_id, source))
    await callback.answer()


@dreams_router.callback_query(F.data.startswith('edit_'))
async def edit_dream_menu(callback: CallbackQuery,
                          state: FSMContext,
                          i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    action = callback.data[:8]
    dream_id = callback.data[9:]

    logger.info(f'EDIT_ button. callback: {callback.data}; action: {action}')

    await state.update_data(dream_id=str(dream_id))
    await state.update_data(edit_action=action)

    # Получаем кэш для пользователя
    user_cache = get_cache(user_id)

    # Ищем запись по dream_id
    found_dream = None
    for day, dreams in user_cache.items():
        for dream in dreams:
            if str(dream[0]) == str(dream_id):  # dream[0] — это id записи
                found_dream = dream
                break
        if found_dream:
            break

    if not found_dream:
        try:
            await callback.message.edit_text(i18n.dream.notfound(), 
                                             reply_markup=kb.back_to_dream(i18n, dream_id))
        except TelegramBadRequest:
            await callback.answer()
        return

    # Формируем сообщение с деталями записи
    dream_id, title, content, emoji, comment, cover, create_time = found_dream

    # Переводим пользователя в соответствующее состояние
    if action == "edit_con":
        await state.set_state(CalendarSG.edit_con)
        await callback.message.answer(content)
        await callback.message.answer(i18n.newcontent(), 
                                      reply_markup=kb.back_to_dream(i18n, dream_id))

    elif action == "edit_tit":
        await state.set_state(CalendarSG.edit_tit)
        if title == "" or title is None:
            await callback.message.answer(i18n.notitle())
        else:
            await callback.message.answer(title)
        await callback.message.answer(i18n.newtitle(), 
                                      reply_markup=kb.back_to_dream(i18n, dream_id))

    elif action == "edit_com":
        await state.set_state(CalendarSG.edit_com)
        if comment == "" or comment is None:
            await callback.message.answer(i18n.nocomment())
        else:
            await callback.message.answer(comment)
        await callback.message.answer(i18n.newcomment(), 
                                      reply_markup=kb.back_to_dream(i18n, dream_id))

    elif action == "edit_cov":
        logger.info(f'EDIT_COVER ACTION')
        await state.set_state(CalendarSG.edit_cov)
        if cover == "" or cover is None:
            await callback.message.answer(i18n.nocover())
        else:
            await callback.message.answer_photo(cover)
        await callback.message.answer(i18n.newcover(), 
                                      reply_markup=kb.back_to_dream(i18n, dream_id))

    elif action == "edit_emo":
        await state.set_state(CalendarSG.edit_emo)
        if emoji == "" or emoji is None:
            await callback.message.answer(i18n.noemoji())
        else:
            await callback.message.answer(emoji)
        await callback.message.answer(i18n.newemoji(), 
                                      reply_markup=kb.back_to_dream(i18n, dream_id))

    await callback.answer()


@dreams_router.message(CalendarSG.edit_con)
async def edit_content(message: Message, 
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_content = message.text

    # Проверяем длину содержания
    if len(new_content) > 4096:
        await message.answer(i18n.toolong.content())
        return

    # Получаем данные из состояния (например, dream_id)
    data = await state.get_data()
    dream_id = data.get("dream_id")

    await db.update_content(new_content, int(dream_id), user_id)
    await state.clear()
    await message.answer(i18n.content.updated(), 
                         reply_markup=kb.back_to_dream(i18n, dream_id))


@dreams_router.message(CalendarSG.edit_tit)
async def edit_title(message: Message, 
                     state: FSMContext,
                     i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_title = message.text

    # Проверяем длину заголовка
    if len(new_title) > 64:
        await message.answer(i18n.toolong.title())
        return

    # Получаем данные из состояния (например, dream_id)
    data = await state.get_data()
    dream_id = data.get("dream_id")

    await db.update_title(new_title, int(dream_id), user_id)
    await state.clear()
    await message.answer(i18n.title.updated(), 
                         reply_markup=kb.back_to_dream(i18n, dream_id))


@dreams_router.message(CalendarSG.edit_com)
async def edit_comment(message: Message, 
                       state: FSMContext,
                       i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_comment = message.text

    # Проверяем длину комментария
    if len(new_comment) > 128:
        await message.answer(i18n.toolong.comment())
        return

    # Получаем данные из состояния (например, dream_id)
    data = await state.get_data()
    dream_id = data.get("dream_id")

    await db.update_comment(new_comment, int(dream_id), user_id)
    await state.clear()
    await message.answer(i18n.comment.updated(), 
                         reply_markup=kb.back_to_dream(i18n, dream_id))


@dreams_router.message(CalendarSG.edit_cov)
async def edit_image(message: Message, 
                     state: FSMContext,
                     i18n: TranslatorRunner):

    logger.info(f'EDIT COVER ROUTER')

    user_id = message.from_user.id
    image_url = message.text

    # Проверяем, что URL валидный (можно добавить более сложную проверку)
    if not image_url.startswith(("http://", "https://")):
        await message.answer(i18n.incorrect.url())
        return

    # Получаем данные из состояния (например, dream_id)
    data = await state.get_data()
    dream_id = data.get("dream_id")

    # Обновляем запись в базе данных
    await db.update_cover(image_url, int(dream_id), user_id)
    await state.clear()
    await message.answer(i18n.cover.updated(), 
                         reply_markup=kb.back_to_dream(i18n, dream_id))


@dreams_router.message(CalendarSG.edit_emo)
async def edit_emoji(message: Message, 
                     state: FSMContext,
                     i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    new_emoji = message.text

    # Проверяем длину эмодзи
    if len(new_emoji) > 4:
        await message.answer(i18n.toolong.emoji())
        return
    
    # Проверяем, что введенный текст — это эмодзи
    if not is_emoji(new_emoji):
        await message.answer(i18n.notemoji())
        return

    # Получаем данные из состояния (например, dream_id)
    data = await state.get_data()
    dream_id = data.get("dream_id")

    await db.update_emoji(new_emoji, int(dream_id), user_id)
    await state.clear()
    await message.answer(i18n.emoji.updated(), 
                         reply_markup=kb.back_to_dream(i18n, dream_id))
    

@dreams_router.callback_query(F.data.startswith('delete_'))
async def delete_handler(callback: CallbackQuery,
                         i18n: FSMContext):
    
    _, dream_id = callback.data.split('_')
    await callback.message.answer(i18n.confirm.delete(), 
                                  reply_markup=kb.delete_dream(i18n, dream_id))
    await callback.answer()


@dreams_router.callback_query(F.data.startswith('confirm_'))
async def delete_confirm_handler(callback: CallbackQuery,
                                 i18n: TranslatorRunner):
    try:
        _, dream_id = callback.data.split('_')
        dream_id = int(dream_id)

        # Удаляем запись
        await db.delete_dream(dream_id)
        await callback.message.edit_text(
            i18n.complete.delete(),
            reply_markup=kb.back_to_calendar(i18n)
        )

    except ValueError:
        await callback.message.edit_text(
            i18n.dream.notfound() or "Сон не найден!",
            reply_markup=kb.back_to_calendar(i18n)
        )
    except Exception as e:
        await callback.message.edit_text(
            i18n.dream.notfound() or "Сон не найден!",
            reply_markup=kb.back_to_calendar(i18n)
        )
    except TelegramBadRequest:
        await callback.answer("Не удалось обновить сообщение.")

    finally:
        await callback.answer()
    

@dreams_router.callback_query(F.data == 'ignore')
async def ignore_handler(callback: CallbackQuery):
    await callback.answer()
