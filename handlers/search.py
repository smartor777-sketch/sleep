import logging 

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import SearchSG, get_cache

search = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@search.callback_query(F.data == 'search')
async def search_menu(callback: CallbackQuery,
                      state: FSMContext,
                      i18n: TranslatorRunner):
     
    await state.set_state(SearchSG.search)
    await callback.message.answer(i18n.search.menu(), reply_markup=kb.back_to_menu())


@search.message(SearchSG.search)
async def process_search(message: Message, 
                         state: FSMContext, 
                         i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    query = message.text.lower()  # Приводим запрос к нижнему регистру для удобства поиска
    cache = get_cache(user_id)

    # Проверяем, есть ли данные в кэше
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

            # Ищем совпадения в заголовке и содержании
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

    # Отправляем результаты пользователю
    response = i18n.search.results_header() + "\n\n" + "\n\n".join(results)
    await message.answer(response, reply_markup=kb.dreams_list(dreams))

    # Завершаем состояние поиска
    await state.finish()

