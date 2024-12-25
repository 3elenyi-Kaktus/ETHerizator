import logging
from enum import IntEnum

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
        return int(integer) * (10 ** unit.value) + int(decimal) * (10 ** (unit.value - len(decimal)))

    @staticmethod
    def fromInteger(number: str, unit: EtherUnit) -> int:
        return int(number) * (10 ** unit.value)