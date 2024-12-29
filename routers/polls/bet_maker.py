import json
import logging
import re
from dataclasses import dataclass

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from helpers import delete_markup, EtherUnitsConverter
from storage.poll import Poll
from storage.storage import storage
from state_holders.states import state_holder, State
from state_holders.messages import message_holder
from state_holders.callbacks import Callback

bet_maker_router = Router(name=__name__)


@dataclass
class BetDraft:
    poll_id: int = -1
    option_id: int = -1
    amount: int = -1

    def __json__(self):
        return {
            "poll_id": self.poll_id,
            "option_id": self.option_id,
            "amount": self.amount,
        }


bet_drafts: dict[int, BetDraft] = {}


def at_exit(user_id: int):
    message_holder.delete(user_id)
    bet_drafts.pop(user_id, None)
    state_holder.set(user_id, State.NONE)


@bet_maker_router.message(Command("view_bet_maker_router"))
async def view_bet_maker_router(message: Message):
    logging.info(f"view_bet_maker_router")
    _ = await message.answer(
        f"Last messages: {json.dumps(message_holder, indent=4)}\n"
        f"Bet drafts: {json.dumps(bet_drafts, indent=4)}\n"
        f"States: {json.dumps(state_holder, indent=4)}"
    )


@bet_maker_router.message(Command("make_bet"))
@bet_maker_router.callback_query(lambda x: x.data in [Callback.DISCARD_BET_POLL_ID_CHANGES, Callback.CREATE_NEW_BET])
async def make_bet(update: Update) -> None:
    logging.info(f"make_bet")
    user_id: int = update.from_user.id
    bet_drafts[user_id] = BetDraft()

    # TODO create paging system
    # TODO get available polls from blockchain

    poll_ids: list[int] = list(storage.polls.keys())

    # bet_ids = storage.conn.getAvailableBets()

    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_BET_MAKING)
    buttons = [[cancel_button]]
    for poll_id in poll_ids[:9]:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=storage.polls[poll_id].description, callback_data=f"{Callback.SELECT_POLL_ID}_{poll_id}"
                )
            ]
        )
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(update, Message):
        answer = await update.answer(f"Please, select one of available polls:", reply_markup=markup)
        message_holder.set(user_id, answer)
    else:
        edited = await update.message.edit_text(f"Please, select one of available polls:", reply_markup=markup)
        message_holder.set(user_id, edited)


@bet_maker_router.callback_query(
    lambda x: x.data.startswith(Callback.SELECT_POLL_ID) or x.data == Callback.DISCARD_BET_POLL_OPTION_CHANGES
)
async def update_bet_info(callback_query: CallbackQuery) -> None:
    logging.info(f"update_bet_info")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Selected poll...")
    match callback_query.data:
        case s if s.startswith(Callback.SELECT_POLL_ID):
            poll_id: int = int(callback_query.data.split("_")[-1])
        case Callback.DISCARD_BET_POLL_OPTION_CHANGES:
            poll_id: int = bet_drafts[user_id].poll_id
        case _:
            raise RuntimeError
    bet_drafts[user_id].poll_id = poll_id
    poll: Poll = storage.polls[poll_id]

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_BET_POLL_ID_CHANGES)
    buttons = [[cancel_button]]
    for i, option in enumerate(poll.options, start=1):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"[{i}]: {option.description}", callback_data=f"{Callback.SELECT_POLL_OPTION}_{i}"
                )
            ]
        )
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    option_coeffs: list[float] = poll.get_option_coeffs()
    reply_text = f"Your bet:\n" f"Poll ID: {poll_id}\n" f"{poll.description}\n" f"Options:\n"
    for i, (option, coeff) in enumerate(zip(poll.options, option_coeffs), start=1):
        reply_text += f"  [{i}] (coeff: x{coeff:.2f}) -> {option.description}\n"
    reply_text.rstrip("\n")
    edited = await callback_query.message.edit_text(reply_text, reply_markup=markup)
    message_holder.set(user_id, edited)


@bet_maker_router.callback_query(
    lambda x: x.data.startswith(Callback.SELECT_POLL_OPTION) or x.data == Callback.DISCARD_BET_WAGER_CHANGES
)
async def choose_bet_option(callback_query: CallbackQuery) -> None:
    logging.info(f"choose_bet_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Selected option...")
    match callback_query.data:
        case s if s.startswith(Callback.SELECT_POLL_OPTION):
            poll_option = int(callback_query.data.split("_")[-1]) - 1
        case Callback.DISCARD_BET_WAGER_CHANGES:
            poll_option = bet_drafts[user_id].option_id
        case _:
            raise RuntimeError

    bet_drafts[user_id].option_id = poll_option
    poll_id = bet_drafts[user_id].poll_id
    poll = storage.polls[poll_id]

    # TODO get user balance from blockchain

    user_balance: int = storage.balances[user_id]

    # user_balance = storage.conn.getBalance(callback_query.from_user.id)

    state_holder.set(user_id, State.AWAITING_BET_WAGER_AMOUNT)
    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_BET_POLL_OPTION_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
    edited = await callback_query.message.edit_text(
        f"Your bet:\n"
        f"Poll ID: {poll_id}\n"
        f"{poll.description}\n"
        f"Chosen option: [{poll_option + 1}]: {poll.get_option_description(poll_option)}\n"
        f"\n"
        f"Your balance: {f'{user_balance:.18f}'.rstrip('0')}\n"
        f"Please, enter how much ETH you want to bet:",
        reply_markup=markup,
    )
    message_holder.set(user_id, edited)


@bet_maker_router.message(lambda x: state_holder.get(x.from_user.id) == State.AWAITING_BET_WAGER_AMOUNT)
async def awaiting_bet_wager_amount(message: Message) -> None:
    logging.info(f"awaiting_bet_wager_amount")
    user_id: int = message.from_user.id

    await delete_markup(message_holder.get(user_id))
    match = re.fullmatch(r"(\d+(\.\d+)?) ?([gG]?wei|[gG]?Wei|G?WEI|[eE]th|ETH)", message.text)
    if not match:
        cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_BET_POLL_OPTION_CHANGES)
        markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
        answer = await message.answer(
            f"Please, enter amount in the following format: number [wei|gwei|eth]", reply_markup=markup
        )
        message_holder.set(user_id, answer)
        return

    number, decimal, unit = match.groups()
    unit = unit.lower()
    if unit == "wei" and decimal is not None:
        cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_BET_POLL_OPTION_CHANGES)
        markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
        answer = await message.answer(
            f"Wei is a non-dividable unit, you can't use floating point numbers with it.\n"
            f"Please, enter amount in the following format: number [wei|gwei|eth]",
            reply_markup=markup,
        )
        message_holder.set(user_id, answer)
        return

    if decimal is not None:
        ether_amount: int = EtherUnitsConverter.fromFloat(number, EtherUnitsConverter.unitTypeByName(unit))
    else:
        ether_amount: int = EtherUnitsConverter.fromInteger(number, EtherUnitsConverter.unitTypeByName(unit))
    bet_drafts[user_id].amount = ether_amount
    poll_id = bet_drafts[user_id].poll_id
    poll = storage.polls[poll_id]
    poll_option = bet_drafts[user_id].option_id

    state_holder.set(user_id, State.NONE)

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_BET_WAGER_CHANGES)
    approve_button = InlineKeyboardButton(text="Approve", callback_data=Callback.APPROVE_BET_MAKING)
    markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button, approve_button]])
    # TODO make automatic convertion from wei to nearest most pretty unit
    answer = await message.answer(
        f"Your bet:\n"
        f"Poll ID: {poll_id}\n"
        f"{poll.description}\n"
        f"Chosen option: [{poll_option + 1}]: {poll.get_option_description(poll_option)}\n"
        f"Wager size: {ether_amount} ETH",
        reply_markup=markup,
    )
    message_holder.set(user_id, answer)


@bet_maker_router.callback_query(F.data == Callback.CANCEL_BET_MAKING)
async def cancel_bet_making(callback_query: CallbackQuery) -> None:
    logging.info(f"cancel_bet_making")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Making bet cancelled...")
    _ = await callback_query.message.edit_text("Cancelled making bet.", reply_markup=None)
    at_exit(user_id)


@bet_maker_router.callback_query(F.data == Callback.APPROVE_BET_MAKING)
async def approve_bet_making(callback_query: CallbackQuery) -> None:
    logging.info(f"approve_bet_making")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Approved bet...")

    ether_amount: int = bet_drafts[user_id].amount
    poll_id = bet_drafts[user_id].poll_id
    poll = storage.polls[poll_id]
    poll_option = bet_drafts[user_id].option_id

    # TODO push bet onto blockchain

    storage.polls[poll_id].make_bet(user_id, ether_amount, poll_option)

    # storage.conn.makeBet(callback_query.from_user.id, bet_id, bet_option, int(ether_amount * (10 ** 18)))
    # TODO make automatic convertion from wei to nearest most pretty unit
    _ = await callback_query.message.edit_text(
        f"Succesfully betted {f'{ether_amount:.18f}'.rstrip('0')} ETH with poll ID: {poll_id}\n"
        f"{poll.description}\n"
        f"On option: [{poll_option + 1}]: {poll.get_option_description(poll_option)}\n",
        reply_markup=None,
    )
    at_exit(callback_query.from_user.id)
