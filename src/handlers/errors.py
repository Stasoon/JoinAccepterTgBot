import traceback

from aiogram import Dispatcher
from aiogram.types import Update

from src.utils import logger


async def handle_errors(update: Update, error: Exception):
    traceback_str = traceback.format_exc()
    logger.error(f'Update: {update} \nError: {error} \nTraceback: {traceback_str}')


def register_errors_handlers(dp: Dispatcher):
    dp.register_errors_handler(handle_errors)
