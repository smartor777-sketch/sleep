from aiogram.fsm.state import State, StatesGroup

class SubCheckSG(StatesGroup):
    sub_check = State()

class CalendarSG(StatesGroup):
    edit_con = State()
    edit_tit = State()
    edit_com = State()
    edit_cov = State()
    edit_emo = State()

class SearchSG(StatesGroup):
    search = State()

class AccountSG(StatesGroup):
    buy_sub = State()