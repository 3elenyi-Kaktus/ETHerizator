import logging

from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message

from storage.storage import storage
from state_holders.states import state_holder, State
from state_holders.messages import message_holder

initializer_router = Router(name=__name__)


@initializer_router.message(Command("start"))
async def start(message: Message) -> None:
    logging.info(f"start")
    user_id: int = message.from_user.id

    if not user_id in state_holder.states.keys():
        state_holder.set_state(user_id, State.NONE)
        storage.balances[user_id] = 0

    answer = await message.answer(f"Welcome to ETHerizator bot, {html.bold(message.from_user.full_name)}!", reply_markup=None)
    message_holder.set_message(user_id, answer)
