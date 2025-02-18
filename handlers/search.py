import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import SearchSG, get_cache

search_router = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


MAX_RESULTS = 5  # Ограничение на количество результатов поиска

@search_router.callback_query(F.data == 'search')
async def search_menu(callback: CallbackQuery,
                      state: FSMContext,
                      i18n: TranslatorRunner):
    await state.set_state(SearchSG.search)
    await callback.message.answer(i18n.search.menu(), reply_markup=kb.back_to_menu())


@search_router.message(SearchSG.search)
async def process_search(message: Message, 
                         state: FSMContext, 
                         i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    query = message.text.strip().lower()  # Приводим запрос к нижнему регистру и убираем лишние пробелы

    # Если запрос пустой, завершаем выполнение
    if not query:
        await message.answer(i18n.search.empty_query())
        await state.finish()
        return

    try:
        cache = get_cache(user_id)
    except Exception as e:
        logger.error(f"Error retrieving cache for user {user_id}: {e}")
        await message.answer(i18n.search.cache_error())
        await state.finish()
        return

    # Если нет данных в кэше
    if not cache:
        await message.answer(i18n.search.no_data())
        await state.finish()
        return

    # Ищем совпадения в записях
    results = []
    dreams_list = []
    for day, dreams in cache.items():
        for dream in dreams:
            dream_id, title, content, emoji, comment, cover, create_time = dream

            # Ищем совпадения в заголовке и содержимом
            if (query in title.lower()) or (query in content.lower()):
                # Формируем результат
                result = (
                    f"📅 {create_time.strftime('%Y-%m-%d')}\n"
                    f"📌 {title}\n"
                    f"📝 {content[:64]}..."  # Первые 64 символа текста
                )
                results.append(result)
                dreams_list.append(dream)

    # Проверяем, есть ли результаты
    if not results:
        await message.answer(i18n.search.noresults())
        await state.finish()
        return

    # Ограничиваем количество результатов
    if len(results) > MAX_RESULTS:
        results = results[:MAX_RESULTS]
        await message.answer(i18n.search.too_many_results())

    # Логируем результат поиска
    logger.info(f"User {user_id} searched for: {query}. Found {len(results)} results.")

    # Отправляем результаты пользователю
    response = i18n.search.results_header() + "\n\n" + "\n\n".join(results)
    await message.answer(response, reply_markup=kb.dreams_list(dreams_list))

    # Завершаем состояние поиска
    await state.clear()
