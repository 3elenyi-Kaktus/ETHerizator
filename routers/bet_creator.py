import json
import logging
from dataclasses import dataclass, field

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from storage.bet import Bet
from helpers import delete_markup
from state_holders.states import state_holder, State
from state_holders.messages import message_holder
from state_holders.callbacks import Callback
from storage.storage import storage


bet_creator_router = Router(name=__name__)


@dataclass
class BetDraft:
    description: str
    options: list[str] = field(default_factory=list)

    def to_str(self):
        result = f"Bet description: {self.description}\n"
        if self.options:
            result += f"Options:\n"
            for i, option in enumerate(self.options, start=1):
                result += f"  [{i}] -> {option}\n"
        return result[:-1]

    def __json__(self):
        return {"description": self.description,
                "options": self.options}


bet_drafts: dict[int, BetDraft] = {}


def at_exit(user_id: int):
    message_holder.delete_message(user_id)
    bet_drafts.pop(user_id, None)
    state_holder.set_state(user_id, State.NONE)


@bet_creator_router.message(Command("view_bet_creator_router"))
async def view_bet_creator_router(message: Message) -> None:
    logging.info(f"view_bet_creator_router")
    _ = await message.answer(
        f"Last messages: {json.dumps(message_holder, indent=4)}\n"
        f"Bet cache: {json.dumps(bet_drafts, indent=4)}\n"
        f"States: {json.dumps(state_holder, indent=4)}")


@bet_creator_router.message(Command("create_bet"))
async def create_bet(message: Message) -> None:
    logging.info(f"create_bet")
    user_id: int = message.from_user.id
    button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_BET_CREATION)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
    state_holder.set_state(user_id, State.AWAITING_BET_DESCRIPTION)
    bet_drafts[user_id] = BetDraft("")
    answer = await message.answer(f"Sure!\n"
                                  f"Please, enter bet description:", reply_markup=markup)
    message_holder.set_message(user_id, answer)


@bet_creator_router.message(
    lambda x: state_holder.get_state(x.from_user.id) in [State.AWAITING_BET_DESCRIPTION, State.AWAITING_BET_OPTION] or
              state_holder.get_state(x.from_user.id).startswith(State.AWAITING_EDITED_BET_OPTION))
@bet_creator_router.callback_query(
    lambda x: x.data == Callback.DISCARD_CURRENT_BET_CHANGES or
              x.data.startswith(Callback.DELETE_BET_OPTION))
async def update_bet_info(update: Update) -> None:
    logging.info(f"update_bet_info")
    addon = ""
    if isinstance(update, Message):
        message: Message = update
        user_id: int = message.from_user.id
        await delete_markup(message_holder.get_message(user_id))
        match state_holder.get_state(user_id):
            case State.AWAITING_BET_DESCRIPTION:
                bet_drafts[user_id].description = message.text
            case State.AWAITING_BET_OPTION:
                bet_drafts[user_id].options.append(message.text)
            case s if s.startswith(State.AWAITING_EDITED_BET_OPTION):
                chosen_option: int = int(
                    state_holder.get_state(user_id).lstrip(State.AWAITING_EDITED_BET_OPTION + "_"))
                bet_drafts[user_id].options[chosen_option - 1] = message.text
                addon += f"Changed option [{chosen_option}] successfully\n"
        state_holder.set_state(user_id, State.NONE)
    elif isinstance(update, CallbackQuery):
        callback_query: CallbackQuery = update
        user_id: int = callback_query.from_user.id
        match callback_query.data:
            case Callback.DISCARD_CURRENT_BET_CHANGES:
                pass
            case s if s.startswith(Callback.DELETE_BET_OPTION):
                chosen_option = int(callback_query.data.lstrip(Callback.DELETE_BET_OPTION + "_"))
                bet_drafts[user_id].options.pop(chosen_option - 1)
                addon += f"Deleted option [{chosen_option}] successfully\n"
    else:
        raise TypeError

    reply_text = addon + bet_drafts[user_id].to_str()
    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_BET_CREATION)
    edit_description_button = InlineKeyboardButton(text="Edit description", callback_data=Callback.EDIT_BET_DESCRIPTION)
    add_option_button = InlineKeyboardButton(text="Add option", callback_data=Callback.ADD_BET_OPTION)
    edit_option_button = InlineKeyboardButton(text="Edit option", callback_data=Callback.ENTER_EDIT_BET_OPTIONS_SELECTION)
    delete_option_button = InlineKeyboardButton(text="Delete option", callback_data=Callback.ENTER_DELETE_BET_OPTIONS_SELECTION)
    button_proceed = InlineKeyboardButton(text="Approve", callback_data=Callback.APPROVE_BET_CREATION)
    buttons = [[cancel_button],
               [edit_description_button],
               [add_option_button, edit_option_button, delete_option_button]]
    if len(bet_drafts[user_id].options) > 1:
        buttons.append([button_proceed])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if len(bet_drafts[user_id].options) < 2:
        reply_text += f"\nPlease, add at least 2 options to proceed"
    if isinstance(update, Message):
        answer = await message.answer(reply_text, reply_markup=markup)
    else:
        answer = await callback_query.message.edit_text(reply_text, reply_markup=markup)
    message_holder.set_message(user_id, answer)


@bet_creator_router.callback_query(F.data == Callback.EDIT_BET_DESCRIPTION)
async def edit_bet_description(callback_query: CallbackQuery) -> None:
    logging.info(f"edit_bet_description")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing bet description...")
    state_holder.set_state(user_id, State.AWAITING_BET_DESCRIPTION)

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_BET_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    edited = await callback_query.message.edit_text(callback_query.message.text + f"\nPlease, enter new description:",
                                                    reply_markup=markup)
    message_holder.set_message(user_id, edited)


@bet_creator_router.callback_query(F.data == Callback.ADD_BET_OPTION)
async def add_bet_option(callback_query: CallbackQuery) -> None:
    logging.info(f"add_bet_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Adding new option...")
    state_holder.set_state(user_id, State.AWAITING_BET_OPTION)

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_BET_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    edited = await callback_query.message.edit_text(callback_query.message.text + f"\nPlease, enter new option:", reply_markup=markup)
    message_holder.set_message(user_id, edited)


@bet_creator_router.callback_query(F.data == Callback.ENTER_EDIT_BET_OPTIONS_SELECTION)
async def enter_edit_bet_option_selection(callback_query: CallbackQuery) -> None:
    logging.info(f"enter_edit_bet_option_selection")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_BET_CHANGES)
    buttons = [[button_cancel]]
    for i, option in enumerate(bet_drafts[user_id].options, start=1):
        buttons.append([InlineKeyboardButton(text=f"[{i}]: {option}", callback_data=f"{Callback.EDIT_BET_OPTION}_{i}")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    edited = await callback_query.message.edit_text(callback_query.message.text + f"\nWhich option you would like to change?", reply_markup=markup)
    message_holder.set_message(user_id, edited)


@bet_creator_router.callback_query(F.data == Callback.ENTER_DELETE_BET_OPTIONS_SELECTION)
async def enter_delete_bet_option_selection(callback_query: CallbackQuery) -> None:
    logging.info(f"enter_delete_bet_option_selection")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_BET_CHANGES)
    buttons = [[button_cancel]]
    for i, option in enumerate(bet_drafts[user_id].options, start=1):
        buttons.append([InlineKeyboardButton(text=f"[{i}]: {option}", callback_data=f"{Callback.DELETE_BET_OPTION}_{i}")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    edited = await callback_query.message.edit_text(callback_query.message.text + f"\nWhich option you would like to delete?", reply_markup=markup)
    message_holder.set_message(user_id, edited)


@bet_creator_router.callback_query(F.data.startswith(Callback.EDIT_BET_OPTION))
async def edit_bet_option(callback_query: CallbackQuery) -> None:
    logging.info(f"edit_bet_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")


    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_BET_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    chosen_option: int = int(callback_query.data.lstrip(Callback.EDIT_BET_OPTION + "_"))
    state_holder.set_state(user_id, f"{State.AWAITING_EDITED_BET_OPTION}_{chosen_option}")
    edited = await callback_query.message.edit_text(bet_drafts[user_id].to_str() + f"\nPlease, enter new option instead of [{chosen_option}]: {bet_drafts[user_id].options[chosen_option - 1]}", reply_markup=markup)
    message_holder.set_message(user_id, edited)


@bet_creator_router.callback_query(F.data == Callback.CANCEL_BET_CREATION)
async def cancel_bet_creation(callback_query: CallbackQuery) -> None:
    logging.info(f"cancel_bet_creation")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Creation cancelled...")
    edited = await callback_query.message.edit_text("Cancelled bet creation.", reply_markup=None)
    at_exit(user_id)


@bet_creator_router.callback_query(F.data == Callback.APPROVE_BET_CREATION)
async def approve_bet_creation(callback_query: CallbackQuery) -> None:
    logging.info(f"approve_bet_creation")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Creation approved...")

    #TODO send bet on blockchain
    bet_id = len(storage.bets)
    storage.bets[len(storage.bets)] = Bet(bet_id, bet_drafts[user_id].description, bet_drafts[user_id].options)

    # _ = storage.conn.createBet()
    # bet_id = len(storage.bets) + 1
    # storage.bets[bet_id] = Bet(bet_id, bet_drafts[callback_query.from_user.id][0],
    #                            [bet_drafts[callback_query.from_user.id][1], bet_drafts[callback_query.from_user.id][2]])

    edited = await callback_query.message.edit_text(f"Bet was created! ID: {bet_id}", reply_markup=None)
    at_exit(user_id)
