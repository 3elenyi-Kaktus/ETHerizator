import logging
from enum import IntEnum
from typing import Optional

from aiogram.types import Message, InlineKeyboardMarkup, Update

from state_holders.messages import message_holder

COLS_BUTTONS_MAX_NUM = 8
BUTTONS_MAX_NUM = 100


async def delete_markup(message: Message):
    logging.info("Deleting markup")
    if not message or message.reply_markup is None:
        return
    logging.critical(message.reply_markup)
    deleted = await message.delete_reply_markup()
    if isinstance(deleted, bool):
        logging.critical(f"Deleted markup from inline message! (ID: {message.message_id})")


# if message reply caused by new Message from user - send new one, otherwise (by CallbackQuery) edit existing one
async def handle_ambiguous_reply(user_id: int, update: Update, text: str, markup: Optional[InlineKeyboardMarkup]):
    if isinstance(update, Message):
        answer = await update.answer(text, reply_markup=markup)
        message_holder.set(user_id, answer)
    else:
        edited = await update.message.edit_text(text, reply_markup=markup)
        message_holder.set(user_id, edited)


class EtherUnit(IntEnum):
    WEI = 0
    GWEI = 9
    ETH = 18


class EtherUnitsConverter:
    mapping: dict[str, EtherUnit] = {
        "wei": EtherUnit.WEI,
        "gwei": EtherUnit.GWEI,
        "eth": EtherUnit.ETH,
    }

    @staticmethod
    def unitTypeByName(unit: str) -> EtherUnit:
        return EtherUnitsConverter.mapping[unit]

    @staticmethod
    def fromFloat(number: str, unit: EtherUnit) -> int:
        # asserting that decimal part will ve completely converted to integer
        integer, decimal = number.split(".")
        return int(integer) * (10**unit.value) + int(decimal) * (10 ** (unit.value - len(decimal)))

    @staticmethod
    def fromInteger(number: str, unit: EtherUnit) -> int:
        return int(number) * (10**unit.value)
