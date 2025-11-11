from aiogram.fsm.state import State, StatesGroup

class MainSG(StatesGroup):
    ready_for_dream = State()

class StartSG(StatesGroup):
    sub_check = State()
    edit_des = State()
    first_dream = State()
    first_analyze = State()

class CalendarSG(StatesGroup):
    edit_con = State()
    edit_tit = State()
    edit_com = State()
    edit_cov = State()
    edit_emo = State()

class SearchSG(StatesGroup):
    search = State()

class AnalyzeSG(StatesGroup):
    edit_des = State()

class AccountSG(StatesGroup):
    buy_sub = State()
    ticket = State()

class AdminSG(StatesGroup):
    reply_ticket = State()
    enter_user_id = State()