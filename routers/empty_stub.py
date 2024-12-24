import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery

empty_stub_router = Router(name=__name__)


@empty_stub_router.message()
async def unhandled_message(message: Message) -> None:
    logging.critical(message)
    raise RuntimeError(f"Unhandled message")


@empty_stub_router.callback_query()
async def unhandled_callback(callback_query: CallbackQuery) -> None:
    logging.critical(callback_query)
    raise RuntimeError(f"Unhandled callback: {callback_query.data}")
