from typing import Generator

from .models import Channel


# region Create

def save_channel(channel_id: str, title: str, url: str) -> None:
    if not is_channel_already_exist(channel_id):
        Channel.create(channel_id=channel_id, title=title, url=url)
    else:
        channel = Channel.get(Channel.channel_id == channel_id)
        channel.update(channel_id=channel_id, title=title, url=url)
        channel.save()

# endregion


# region Read

def is_channel_already_exist(channel_id: str) -> bool:
    return bool(Channel.get_or_none(Channel.channel_id == channel_id))


def get_channel_or_none(channel_id):
    return Channel.get_or_none(Channel.channel_id == channel_id)


def get_all_channels() -> Generator[Channel, None, None]:
    return (channel for channel in Channel.select())


def get_channel_ids() -> tuple:
    channel_ids = [channel.channel_id for channel in Channel.select()]
    return tuple(channel_ids)


# endregion


# region Update

def toggle_auto_accept(channel_id) -> None:
    channel = Channel.get(Channel.channel_id == channel_id)
    channel.auto_accept = not channel.auto_accept
    channel.save()

# endregion


# region Delete

def delete_channel(channel_id: str) -> None:
    channel = Channel.get(Channel.channel_id == channel_id)
    channel.delete_instance()

# endregion
