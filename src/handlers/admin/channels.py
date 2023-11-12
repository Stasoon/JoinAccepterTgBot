from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils import markdown
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, CallbackQuery

from src.database.channel import get_all_channels, save_channel, delete_channel, get_channel_or_none, toggle_auto_accept
from src.misc.callback_data import channels_list_callback
from src.misc.admin_states import ChannelAdding


class Messages:
    @staticmethod
    def get_channel_description(channel_id: int) -> str:
        channel = get_channel_or_none(channel_id)
        result = (
            f'<b>{markdown.quote_html(channel.title)}</b> \n\n'
            f'<b>🆔 канала:</b> <code>{channel.channel_id}</code> \n'
            f'<b>🔗 Пригласительная ссылка:</b> \n{channel.url} \n\n'
            f'👌 Принимать заявки ботом: <b>{"Да" if channel.auto_accept else "Нет"}</b>'
        )
        return result


class Keyboards:
    reply_button_for_admin_menu = KeyboardButton('📋 Список каналов 📋')
    inline_cancel_button = InlineKeyboardButton(
        '🔙 Отменить', callback_data=channels_list_callback.new(action='cancel', channel_id='')
    )

    @staticmethod
    def get_edit_channel(channel_id):
        markup = InlineKeyboardMarkup()

        channel = get_channel_or_none(channel_id)
        auto_accept_button_text = '❌ Автоприём' if channel.auto_accept else '✅ Автоприём'
        markup.add(
            InlineKeyboardButton(
                text=auto_accept_button_text,
                callback_data=channels_list_callback.new(action='toggle_auto_accept', channel_id=channel_id)
            )
        )

        markup.row(Keyboards.inline_cancel_button)
        return markup

    @staticmethod
    def get_channels_list() -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()

        for channel in get_all_channels():
            markup.row(InlineKeyboardButton(
                text=channel.title,
                callback_data=channels_list_callback.new(action='show', channel_id=channel.channel_id))
            )

        markup.add(
            InlineKeyboardButton(text='➕', callback_data=channels_list_callback.new(action='add', channel_id='')),
            InlineKeyboardMarkup(text='➖', callback_data=channels_list_callback.new(action='delete', channel_id=''))
        )
        return markup

    @staticmethod
    def get_channels_to_delete() -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=1)

        for channel in get_all_channels():
            markup.add(InlineKeyboardButton(
                text=f'❌ {channel.title}',
                callback_data=channels_list_callback.new(action='delete', channel_id=channel.channel_id))
            )

        markup.add(Keyboards.inline_cancel_button)
        return markup

    @staticmethod
    def get_cancel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup().add(Keyboards.inline_cancel_button)


class Handlers:
    @staticmethod
    async def handle_channels_list_button(message: Message):
        await message.answer(text='📋 Список добавленных каналов:', reply_markup=Keyboards.get_channels_list())

    # Отмена
    @staticmethod
    async def handle_cancel_callback(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        await callback.answer('❌ Отменено')
        await callback.message.delete()
        await Handlers.handle_channels_list_button(callback.message)

    # Изменение и показ
    @staticmethod
    async def handle_show_channel_callback(callback: CallbackQuery, callback_data: dict):
        channel_id = callback_data.get('channel_id')
        await callback.message.edit_text(
            text=Messages.get_channel_description(channel_id),
            reply_markup=Keyboards.get_edit_channel(channel_id)
        )

    @staticmethod
    async def handle_toggle_auto_accept_callback(callback: CallbackQuery, callback_data: dict):
        channel_id = callback_data.get('channel_id')
        toggle_auto_accept(channel_id)

        await callback.message.edit_text(
            text=Messages.get_channel_description(channel_id),
            reply_markup=Keyboards.get_edit_channel(channel_id)
        )

    # Добавление
    @staticmethod
    async def handle_add_channel_to_list_callback(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            text='➕ <b>Добавление канала</b> ➕ \n\n'
                 '1) Добавьте бота в канал и дайте ему права: \n<b>Добавление участников - ✔</b> \n'
                 '2) Перешлите боту любой <b>текстовый пост</b> из канала, который хотите добавить:',
            reply_markup=Keyboards.get_cancel()
        )
        await state.set_state(ChannelAdding.wait_for_post)

    @staticmethod
    async def handle_channel_to_add_post_message(message: Message, state: FSMContext):
        if message.forward_from_chat.type not in ['group', 'channel']:
            await message.answer('Это не пост из канала! Попробуйте снова: ')
            return

        chat = message.forward_from_chat

        await state.update_data(chat_id=chat.id, chat_title=chat.title)
        await message.answer('Создайте пригласительную ссылку. \n'
                             '‼Поставьте <b>Заявки на вступление - ✔</b> \n\n'
                             'Пришлите созданную ссылку:')
        await state.set_state(ChannelAdding.wait_for_url)

    @staticmethod
    async def handle_channel_to_add_url(message: Message, state: FSMContext):
        if message.entities and message.entities[0].type == 'url':
            url = message.entities[0].get_text(message.text)
            url = markdown.quote_html(url)
        else:
            await message.answer('Это не ссылка! Попробуйте снова:')
            return

        data = await state.get_data()
        save_channel(channel_id=data.get('chat_id'), title=data.get('chat_title'), url=url)
        await message.answer('✅ Готово! Канал добавлен', reply_markup=Keyboards.get_channels_list())
        await state.finish()

    # Удаление
    @staticmethod
    async def handle_delete_channel_callbacks(callback: CallbackQuery, callback_data: dict):
        channel_id = callback_data.get('channel_id')

        if not channel_id:
            await callback.message.edit_text(
                'Какой канал вы хотите убрать?',
                reply_markup=Keyboards.get_channels_to_delete()
            )
            return

        delete_channel(channel_id)
        await callback.message.edit_text('Канал удалён из списка')
        await Handlers.handle_channels_list_button(callback.message)

    @classmethod
    def register_add_channel_handlers(cls, dp: Dispatcher) -> None:
        # список каналов
        dp.register_message_handler(cls.handle_channels_list_button, text=Keyboards.reply_button_for_admin_menu.text)

        # отмена
        dp.register_callback_query_handler(cls.handle_cancel_callback,
                                           channels_list_callback.filter(action='cancel'),
                                           state='*')

        # показать / изменить канал
        dp.register_callback_query_handler(cls.handle_show_channel_callback,
                                           channels_list_callback.filter(action='show'))

        dp.register_callback_query_handler(cls.handle_toggle_auto_accept_callback,
                                           channels_list_callback.filter(action='toggle_auto_accept'))

        # добавить канал
        dp.register_callback_query_handler(cls.handle_add_channel_to_list_callback,
                                           channels_list_callback.filter(action='add'))

        dp.register_message_handler(cls.handle_channel_to_add_post_message,
                                    lambda msg: msg.is_forward(),
                                    state=ChannelAdding.wait_for_post)

        dp.register_message_handler(cls.handle_channel_to_add_url,
                                    state=ChannelAdding.wait_for_url)

        # удалить канал
        dp.register_callback_query_handler(cls.handle_delete_channel_callbacks,
                                           channels_list_callback.filter(action='delete'))
