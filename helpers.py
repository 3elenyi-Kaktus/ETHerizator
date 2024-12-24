import logging
from aiogram.types import Message

COLS_BUTTONS_MAX_NUM = 8
BUTTONS_MAX_NUM = 100

async def delete_markup(message: Message):
    logging.info('Deleting markup')
    if not message or message.reply_markup is None:
        return
    logging.critical(message.reply_markup)
    deleted = await message.delete_reply_markup()
    if isinstance(deleted, bool):
        logging.critical(f"Deleted markup from inline message! (ID: {message.message_id})")