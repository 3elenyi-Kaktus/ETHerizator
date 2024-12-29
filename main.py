def _default(self, obj):
    return getattr(obj.__class__, "__json__", _default.default)(obj)


from json import JSONEncoder

_default.default = JSONEncoder().default
JSONEncoder.default = _default

import os
import asyncio
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from routers.root import root_router
from routers.initialiser import initializer_router
from routers.polls.poll_creator import poll_creator_router
from routers.polls.bet_maker import bet_maker_router
from routers.empty_stub import empty_stub_router

dispatcher = Dispatcher()
dispatcher.include_routers(root_router, initializer_router, poll_creator_router, bet_maker_router, empty_stub_router)


class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.token: str = os.getenv("TELEGRAM_BOT_TOKEN")
        self.bot: Bot = Bot(token=self.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async def run(self) -> None:
        await dispatcher.start_polling(self.bot)


telegram_bot: TelegramBot = TelegramBot()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_until_complete(telegram_bot.run())
