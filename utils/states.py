from aiogram.fsm.state import State, StatesGroup

class SubCheckSG(StatesGroup):
    sub_check = State()

class MainSG(StatesGroup):
    main_menu = State()

class CalendarSG(StatesGroup):
    calendar = State()
    day = State()
    dream = State()
    edit_content = State()
    edit_title = State()
    edit_dream_emoji = State()

class SearchSG(StatesGroup):
    search = State()

class AccountSG(StatesGroup):
    account = State()
    buy_sub = State()