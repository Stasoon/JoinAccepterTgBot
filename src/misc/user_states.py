from aiogram.dispatcher.filters.state import State, StatesGroup


class SubscriptionChecking(StatesGroup):
    wait_for_check_button = State()
