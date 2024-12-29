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

root_router = Router(name=__name__)


# step_back_t0_bets_selection
@root_router.message(Command("menu"))
@root_router.callback_query(F.data == Callback.RETURN_TO_MAIN_MENU)
async def main_menu(update: Update) -> None:
    user_id = update.from_user.id
    if user_id not in storage.balances.keys():
        if isinstance(update, Message):
            _ = await update.answer(f"You don't have an account yet, please register first (/start)", reply_markup=None)
            return
        raise RuntimeError("User expected to be registered here")
    account_button = InlineKeyboardButton(text="Your account [x]", callback_data=Callback.OPEN_ACCOUNT_MENU)
    polls_button = InlineKeyboardButton(text="Polls", callback_data=Callback.OPEN_POLLS_MENU)
    roulette_button = InlineKeyboardButton(text="Roulette [x]", callback_data=Callback.RUN_ROULETTE)
    games_button = InlineKeyboardButton(text="Games [x]", callback_data=Callback.RUN_GAMES)
    slots_button = InlineKeyboardButton(text="Slots [x]", callback_data=Callback.RUN_SLOTS)
    buttons = [
        [account_button],
        [polls_button],
        [roulette_button, games_button, slots_button],
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(update, Message):
        answer = await update.answer(f"Choose any activity you want:", reply_markup=markup)
        message_holder.set_message(user_id, answer)
    else:
        edited = await update.message.edit_text(f"Choose any activity you want:", reply_markup=markup)
        message_holder.set_message(user_id, edited)


@root_router.callback_query(F.data == Callback.OPEN_POLLS_MENU)
async def open_polls_menu(callback_query: CallbackQuery) -> None:
    logging.info(f"open_polls_menu")
    user_id: int = callback_query.from_user.id

    main_menu_button = InlineKeyboardButton(text="To main menu", callback_data=Callback.RETURN_TO_MAIN_MENU)
    create_poll_button = InlineKeyboardButton(text="Create new poll", callback_data=Callback.CREATE_NEW_POLL)
    vote_poll_button = InlineKeyboardButton(text="Bet on existing poll", callback_data=Callback.CREATE_NEW_BET)
    my_polls_button = InlineKeyboardButton(text="Manage my polls [x]", callback_data=Callback.MANAGE_POLLS)
    my_votes_button = InlineKeyboardButton(text="Manage my bets [x]", callback_data=Callback.MANAGE_BETS)
    buttons = [[main_menu_button], [create_poll_button, vote_poll_button], [my_polls_button, my_votes_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    answer = await callback_query.message.edit_text(f"Here you can create and manage polls, bets", reply_markup=markup)
    message_holder.set_message(user_id, answer)
