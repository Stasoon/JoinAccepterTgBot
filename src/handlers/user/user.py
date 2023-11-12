from aiogram import Dispatcher
from aiogram.types import ChatJoinRequest
from aiogram.utils import markdown
from aiogram.utils.exceptions import BadRequest

from src.database.user import create_user
from src.database.channel import get_channel_or_none
from src.create_bot import bot
from src.utils import logger


def get_join_request_approved(user_name: str, channel_title: str, channel_url: str) -> str:
    return (
        f'<b>👋 Привет, {markdown.quote_html(user_name)}!</b> \n\n'
        f'✅ Заявка на вступление в канал <a href="{channel_url}">{channel_title}</a> принята.'
    )


def get_join_request_will_be_approved_soon(user_name: str, channel_title: str) -> str:
    return (
        f'<b>👋 Привет, {markdown.quote_html(user_name)}!</b> \n\n'
        f'⏰ Ваша на вступление в канал <b>{channel_title}</b> скоро будет одобрена.'
    )


# region Handlers

async def handle_chat_join_request(chat_join: ChatJoinRequest):
    channel = get_channel_or_none(channel_id=chat_join.chat.id)

    if not channel:
        logger.exception(f'Канал {chat_join.chat.id} - {chat_join.chat.title} не добавлен в список')
        return

    if chat_join.invite_link.invite_link[:20] != channel.url[:20]:
        print('ссылка не добавлена в список')
        return

    user_id = chat_join.from_user.id

    # сохраняем пользователя в БД
    create_user(
        telegram_id=user_id,
        name=chat_join.from_user.username or chat_join.from_user.full_name,
        reflink=f'{chat_join.invite_link},{chat_join.chat.title}'
    )

    user_first_name = markdown.quote_html(f"{chat_join.from_user.first_name}")

    if channel.auto_accept:
        try:
            await chat_join.approve()
        except BadRequest as e:
            logger.exception(f'Ошибка при одобрении запроса: {e}')
            return

        msg_text = get_join_request_approved(
            user_name=user_first_name, channel_title=chat_join.chat.title, channel_url=channel.url
        )
    else:
        msg_text = get_join_request_will_be_approved_soon(user_name=user_first_name, channel_title=chat_join.chat.title)

    await bot.send_message(chat_id=user_id, text=msg_text)

# endregion


def register_user_handlers(dp: Dispatcher) -> None:
    # обработчик запроса в канале
    dp.register_chat_join_request_handler(handle_chat_join_request)

