import logging 

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from keyboards import keyboards as kb
from utils import db

account = Router()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@account.callback_query(F.data == 'account')
async def account_menu(callback: CallbackQuery,
                       i18n: TranslatorRunner):
    
    user_id = callback.from_user.id