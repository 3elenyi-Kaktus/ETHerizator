import json
import logging
import re
from dataclasses import dataclass

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from helpers import delete_markup, EtherUnitsConverter
from storage.bet import Bet
from storage.storage import storage
from state_holders.states import state_holder, State
from state_holders.messages import message_holder
from state_holders.callbacks import Callback

wager_maker_router = Router(name=__name__)


@dataclass
class WagerDraft:
    bet_id: int = -1
    option_id: int = -1
    amount: int = -1

    def __json__(self):
        return {
            "bet_id": self.bet_id,
            "option_id": self.option_id,
            "amount": self.amount,
        }


wager_drafts: dict[int, WagerDraft] = {}


def at_exit(user_id: int):
    message_holder.delete_message(user_id)
    wager_drafts.pop(user_id, None)
    state_holder.set_state(user_id, State.NONE)


@wager_maker_router.message(Command("view_wager_maker_router"))
async def view_wager_maker_router(message: Message):
    logging.info(f"view_wager_maker_router")
    _ = await message.answer(
        f"Last messages: {json.dumps(message_holder, indent=4)}\n"
        f"Wager drafts: {json.dumps(wager_drafts, indent=4)}\n"
        f"States: {json.dumps(state_holder, indent=4)}")


@wager_maker_router.message(Command("make_wager"))
@wager_maker_router.callback_query(F.data == Callback.DISCARD_WAGER_BET_CHANGES)
async def make_wager(update: Update) -> None:
    logging.info(f"make_wager")
    user_id: int = update.from_user.id
    wager_drafts[user_id] = WagerDraft()

    # TODO create paging system
    # TODO get available bets from blockchain

    bet_ids: list[int] = list(storage.bets.keys())

    # bet_ids = storage.conn.getAvailableBets()

    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_WAGER_MAKING)
    buttons = [[cancel_button]]
    for bet_id in bet_ids[:9]:
        buttons.append([InlineKeyboardButton(text=storage.bets[bet_id].description,
                                             callback_data=f"{Callback.SELECT_BET_ID}_{bet_id}")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(update, Message):
        answer = await update.answer(f"Please, select one of available bets:", reply_markup=markup)
        message_holder.set_message(user_id, answer)
    else:
        edited = await update.message.edit_text(f"Please, select one of available bets:", reply_markup=markup)
        message_holder.set_message(user_id, edited)


@wager_maker_router.callback_query(lambda x: x.data.startswith(Callback.SELECT_BET_ID) or x.data == Callback.DISCARD_WAGER_OPTION_CHANGES)
async def update_wager_info(callback_query: CallbackQuery) -> None:
    logging.info(f"update_wager_info")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Selected bet...")
    match callback_query.data:
        case s if s.startswith(Callback.SELECT_BET_ID):
            bet_id: int = int(callback_query.data.split("_")[-1])
        case Callback.DISCARD_WAGER_OPTION_CHANGES:
            bet_id: int = wager_drafts[user_id].bet_id
        case _:
            raise RuntimeError
    wager_drafts[user_id].bet_id = bet_id
    bet: Bet = storage.bets[bet_id]

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_WAGER_BET_CHANGES)
    buttons = [[cancel_button]]
    for i, option in enumerate(bet.options, start=1):
        buttons.append([InlineKeyboardButton(text=f"[{i}]: {option.description}",
                                             callback_data=f"{Callback.CHOOSE_BET_OPTION}_{i}")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    option_coeffs: list[float] = bet.get_option_coeffs()
    reply_text = (f"Your wager:\n"
                  f"Bet ID: {bet_id}\n"
                  f"{bet.description}\n"
                  f"Options:\n")
    for i, (option, coeff) in enumerate(zip(bet.options, option_coeffs), start=1):
        reply_text += f"  [{i}] (coeff: x{coeff:.2f}) -> {option.description}\n"
    reply_text.rstrip("\n")
    edited = await callback_query.message.edit_text(reply_text, reply_markup=markup)
    message_holder.set_message(user_id, edited)


@wager_maker_router.callback_query(lambda x: x.data.startswith(Callback.CHOOSE_BET_OPTION) or x.data == Callback.DISCARD_WAGER_ETHER_CHANGES)
async def choose_bet_option(callback_query: CallbackQuery) -> None:
    logging.info(f"choose_bet_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Selected option...")
    match callback_query.data:
        case s if s.startswith(Callback.CHOOSE_BET_OPTION):
            bet_option = int(callback_query.data.split("_")[-1]) - 1
        case Callback.DISCARD_WAGER_ETHER_CHANGES:
            bet_option = wager_drafts[user_id].option_id
        case _:
            raise RuntimeError

    wager_drafts[user_id].option_id = bet_option
    bet_id = wager_drafts[user_id].bet_id
    bet = storage.bets[bet_id]

    # TODO get user balance from blockchain

    user_balance: int = storage.balances[user_id]

    # user_balance = storage.conn.getBalance(callback_query.from_user.id)

    state_holder.set_state(user_id, State.AWAITING_WAGER_ETHER_AMOUNT)
    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_WAGER_OPTION_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
    edited = await callback_query.message.edit_text(f"Your wager:\n"
                                                    f"Bet ID: {bet_id}\n"
                                                    f"{bet.description}\n"
                                                    f"Chosen option: [{bet_option + 1}]: {bet.get_option_description(bet_option)}\n"
                                                    f"\n"
                                                    f"Your balance: {f'{user_balance:.18f}'.rstrip('0')}\n"
                                                    f"Please, enter how much ETH you want to bet:", reply_markup=markup)
    message_holder.set_message(user_id, edited)


@wager_maker_router.message(lambda x: state_holder.get_state(x.from_user.id) == State.AWAITING_WAGER_ETHER_AMOUNT)
async def awaiting_wager_ether_amount(message: Message) -> None:
    logging.info(f"awaiting_wager_ether_amount")
    user_id: int = message.from_user.id

    await delete_markup(message_holder.get_message(user_id))
    match = re.fullmatch(r"(\d+(\.\d+)?) ?([gG]?wei|[gG]?Wei|G?WEI|[eE]th|ETH)", message.text)
    if not match:
        cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_WAGER_OPTION_CHANGES)
        markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
        answer = await message.answer(f"Please, enter amount in the following format: number [wei|gwei|eth]", reply_markup=markup)
        message_holder.set_message(user_id, answer)
        return

    number, decimal, unit = match.groups()
    unit = unit.lower()
    if unit == "wei" and decimal is not None:
        cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_WAGER_OPTION_CHANGES)
        markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
        answer = await message.answer(f"Wei is a non-dividable unit, you can't use floating point numbers with it.\n"
                                      f"Please, enter amount in the following format: number [wei|gwei|eth]",
                                      reply_markup=markup)
        message_holder.set_message(user_id, answer)
        return

    if decimal is not None:
        ether_amount: int = EtherUnitsConverter.fromFloat(number, EtherUnitsConverter.unitTypeByName(unit))
    else:
        ether_amount: int = EtherUnitsConverter.fromInteger(number, EtherUnitsConverter.unitTypeByName(unit))
    wager_drafts[user_id].amount = ether_amount
    bet_id = wager_drafts[user_id].bet_id
    bet = storage.bets[bet_id]
    bet_option = wager_drafts[user_id].option_id

    state_holder.set_state(user_id, State.NONE)

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_WAGER_ETHER_CHANGES)
    approve_button = InlineKeyboardButton(text="Approve", callback_data=Callback.APPROVE_WAGER_MAKING)
    markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button, approve_button]])
    # TODO make automatic convertion from wei to nearest most pretty unit
    answer = await message.answer(f"Your wager:\n"
                                  f"Bet ID: {bet_id}\n"
                                  f"{bet.description}\n"
                                  f"Chosen option: [{bet_option + 1}]: {bet.get_option_description(bet_option)}\n"
                                  f"Wager size: {ether_amount} ETH", reply_markup=markup)
    message_holder.set_message(user_id, answer)


@wager_maker_router.callback_query(F.data == Callback.CANCEL_WAGER_MAKING)
async def cancel_wager_making(callback_query: CallbackQuery) -> None:
    logging.info(f"cancel_wager_making")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Making wager cancelled...")
    _ = await callback_query.message.edit_text("Cancelled making wager.", reply_markup=None)
    at_exit(user_id)


@wager_maker_router.callback_query(F.data == Callback.APPROVE_WAGER_MAKING)
async def approve_wager_making(callback_query: CallbackQuery) -> None:
    logging.info(f"approve_wager_making")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Approved wager...")

    ether_amount: int = wager_drafts[user_id].amount
    bet_id = wager_drafts[user_id].bet_id
    bet = storage.bets[bet_id]
    bet_option = wager_drafts[user_id].option_id

    # TODO push wager onto blockchain

    storage.bets[bet_id].make_bet(user_id, ether_amount, bet_option)

    # storage.conn.makeBet(callback_query.from_user.id, bet_id, bet_option, int(ether_amount * (10 ** 18)))
    # TODO make automatic convertion from wei to nearest most pretty unit
    _ = await callback_query.message.edit_text(f"Succesfully betted {f'{ether_amount:.18f}'.rstrip('0')} ETH with bet ID: {bet_id}\n"
                                                    f"{bet.description}\n"
                                                    f"On option: [{bet_option + 1}]: {bet.get_option_description(bet_option)}\n",
                                                    reply_markup=None)
    at_exit(callback_query.from_user.id)
