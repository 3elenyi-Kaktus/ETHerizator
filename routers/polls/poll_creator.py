import json
import logging
from dataclasses import dataclass, field

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from storage.poll import Poll
from helpers import delete_markup
from state_holders.states import state_holder, State
from state_holders.messages import message_holder
from state_holders.callbacks import Callback
from storage.storage import storage


poll_creator_router = Router(name=__name__)


@dataclass
class PollDraft:
    description: str
    options: list[str] = field(default_factory=list)

    def to_str(self):
        result = f"Poll description: {self.description}\n"
        if self.options:
            result += f"Options:\n"
            for i, option in enumerate(self.options, start=1):
                result += f"  [{i}] -> {option}\n"
        return result[:-1]

    def __json__(self):
        return {"description": self.description, "options": self.options}


poll_drafts: dict[int, PollDraft] = {}


def at_exit(user_id: int):
    message_holder.delete(user_id)
    poll_drafts.pop(user_id, None)
    state_holder.set(user_id, State.NONE)


@poll_creator_router.message(Command("view_poll_creator_router"))
async def view_poll_creator_router(message: Message) -> None:
    logging.info(f"view_poll_creator_router")
    _ = await message.answer(
        f"Last messages: {json.dumps(message_holder, indent=4)}\n"
        f"Poll cache: {json.dumps(poll_drafts, indent=4)}\n"
        f"States: {json.dumps(state_holder, indent=4)}"
    )


@poll_creator_router.message(Command("create_poll"))
@poll_creator_router.callback_query(F.data == Callback.CREATE_NEW_POLL)
async def create_poll(update: Update) -> None:
    logging.info(f"create_poll")
    user_id: int = update.from_user.id
    button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_POLL_CREATION)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
    state_holder.set(user_id, State.AWAITING_POLL_DESCRIPTION)
    poll_drafts[user_id] = PollDraft("")
    if isinstance(update, Message):
        answer = await update.answer(f"Sure!\n" f"Please, enter poll description:", reply_markup=markup)
        message_holder.set(user_id, answer)
    else:
        edited = await update.message.edit_text(f"Sure!\n" f"Please, enter poll description:", reply_markup=markup)
        message_holder.set(user_id, edited)


@poll_creator_router.message(
    lambda x: state_holder.get(x.from_user.id) in [State.AWAITING_POLL_DESCRIPTION, State.AWAITING_POLL_OPTION]
    or state_holder.get(x.from_user.id).startswith(State.AWAITING_EDITED_POLL_OPTION)
)
@poll_creator_router.callback_query(
    lambda x: x.data == Callback.DISCARD_CURRENT_POLL_CHANGES or x.data.startswith(Callback.DELETE_POLL_OPTION)
)
async def update_poll_info(update: Update) -> None:
    logging.info(f"update_poll_info")
    addon = ""
    if isinstance(update, Message):
        message: Message = update
        user_id: int = message.from_user.id
        await delete_markup(message_holder.get(user_id))
        match state_holder.get(user_id):
            case State.AWAITING_POLL_DESCRIPTION:
                poll_drafts[user_id].description = message.text
            case State.AWAITING_POLL_OPTION:
                poll_drafts[user_id].options.append(message.text)
            case s if s.startswith(State.AWAITING_EDITED_POLL_OPTION):
                chosen_option: int = int(state_holder.get(user_id).lstrip(State.AWAITING_EDITED_POLL_OPTION + "_"))
                poll_drafts[user_id].options[chosen_option - 1] = message.text
                addon += f"Changed option [{chosen_option}] successfully\n"
        state_holder.set(user_id, State.NONE)
    elif isinstance(update, CallbackQuery):
        callback_query: CallbackQuery = update
        user_id: int = callback_query.from_user.id
        match callback_query.data:
            case Callback.DISCARD_CURRENT_POLL_CHANGES:
                pass
            case s if s.startswith(Callback.DELETE_POLL_OPTION):
                chosen_option = int(callback_query.data.lstrip(Callback.DELETE_POLL_OPTION + "_"))
                poll_drafts[user_id].options.pop(chosen_option - 1)
                addon += f"Deleted option [{chosen_option}] successfully\n"
    else:
        raise TypeError

    reply_text = addon + poll_drafts[user_id].to_str()
    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.CANCEL_POLL_CREATION)
    edit_description_button = InlineKeyboardButton(
        text="Edit description", callback_data=Callback.EDIT_POLL_DESCRIPTION
    )
    add_option_button = InlineKeyboardButton(text="Add option", callback_data=Callback.ADD_POLL_OPTION)
    edit_option_button = InlineKeyboardButton(
        text="Edit option", callback_data=Callback.ENTER_EDIT_POLL_OPTIONS_SELECTION
    )
    delete_option_button = InlineKeyboardButton(
        text="Delete option", callback_data=Callback.ENTER_DELETE_POLL_OPTIONS_SELECTION
    )
    button_proceed = InlineKeyboardButton(text="Approve", callback_data=Callback.APPROVE_POLL_CREATION)
    buttons = [
        [cancel_button],
        [edit_description_button],
        [add_option_button, edit_option_button, delete_option_button],
    ]
    if len(poll_drafts[user_id].options) > 1:
        buttons.append([button_proceed])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if len(poll_drafts[user_id].options) < 2:
        reply_text += f"\nPlease, add at least 2 options to proceed"
    if isinstance(update, Message):
        answer = await update.answer(reply_text, reply_markup=markup)
    else:
        answer = await update.message.edit_text(reply_text, reply_markup=markup)
    message_holder.set(user_id, answer)


@poll_creator_router.callback_query(F.data == Callback.EDIT_POLL_DESCRIPTION)
async def edit_poll_description(callback_query: CallbackQuery) -> None:
    logging.info(f"edit_poll_description")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing poll description...")
    state_holder.set(user_id, State.AWAITING_POLL_DESCRIPTION)

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_POLL_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    edited = await callback_query.message.edit_text(
        callback_query.message.text + f"\nPlease, enter new description:", reply_markup=markup
    )
    message_holder.set(user_id, edited)


@poll_creator_router.callback_query(F.data == Callback.ADD_POLL_OPTION)
async def add_poll_option(callback_query: CallbackQuery) -> None:
    logging.info(f"add_poll_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Adding new option...")
    state_holder.set(user_id, State.AWAITING_POLL_OPTION)

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_POLL_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    edited = await callback_query.message.edit_text(
        callback_query.message.text + f"\nPlease, enter new option:", reply_markup=markup
    )
    message_holder.set(user_id, edited)


@poll_creator_router.callback_query(F.data == Callback.ENTER_EDIT_POLL_OPTIONS_SELECTION)
async def enter_edit_poll_option_selection(callback_query: CallbackQuery) -> None:
    logging.info(f"enter_edit_poll_option_selection")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_POLL_CHANGES)
    buttons = [[button_cancel]]
    for i, option in enumerate(poll_drafts[user_id].options, start=1):
        buttons.append(
            [InlineKeyboardButton(text=f"[{i}]: {option}", callback_data=f"{Callback.EDIT_POLL_OPTION}_{i}")]
        )
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    edited = await callback_query.message.edit_text(
        callback_query.message.text + f"\nWhich option you would like to change?", reply_markup=markup
    )
    message_holder.set(user_id, edited)


@poll_creator_router.callback_query(F.data == Callback.ENTER_DELETE_POLL_OPTIONS_SELECTION)
async def enter_delete_poll_option_selection(callback_query: CallbackQuery) -> None:
    logging.info(f"enter_delete_poll_option_selection")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_POLL_CHANGES)
    buttons = [[button_cancel]]
    for i, option in enumerate(poll_drafts[user_id].options, start=1):
        buttons.append(
            [InlineKeyboardButton(text=f"[{i}]: {option}", callback_data=f"{Callback.DELETE_POLL_OPTION}_{i}")]
        )
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    edited = await callback_query.message.edit_text(
        callback_query.message.text + f"\nWhich option you would like to delete?", reply_markup=markup
    )
    message_holder.set(user_id, edited)


@poll_creator_router.callback_query(F.data.startswith(Callback.EDIT_POLL_OPTION))
async def edit_poll_option(callback_query: CallbackQuery) -> None:
    logging.info(f"edit_poll_option")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Editing options...")

    button_cancel = InlineKeyboardButton(text="Cancel", callback_data=Callback.DISCARD_CURRENT_POLL_CHANGES)
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_cancel]])
    chosen_option: int = int(callback_query.data.lstrip(Callback.EDIT_POLL_OPTION + "_"))
    state_holder.set(user_id, f"{State.AWAITING_EDITED_POLL_OPTION}_{chosen_option}")
    edited = await callback_query.message.edit_text(
        poll_drafts[user_id].to_str()
        + f"\nPlease, enter new option instead of [{chosen_option}]: {poll_drafts[user_id].options[chosen_option - 1]}",
        reply_markup=markup,
    )
    message_holder.set(user_id, edited)


@poll_creator_router.callback_query(F.data == Callback.CANCEL_POLL_CREATION)
async def cancel_poll_creation(callback_query: CallbackQuery) -> None:
    logging.info(f"cancel_poll_creation")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Creation cancelled...")
    edited = await callback_query.message.edit_text("Cancelled poll creation.", reply_markup=None)
    at_exit(user_id)


@poll_creator_router.callback_query(F.data == Callback.APPROVE_POLL_CREATION)
async def approve_poll_creation(callback_query: CallbackQuery) -> None:
    logging.info(f"approve_poll_creation")
    user_id: int = callback_query.from_user.id
    await callback_query.answer(f"Creation approved...")

    # TODO send poll on blockchain
    poll_id = len(storage.polls)
    storage.polls[len(storage.polls)] = Poll(poll_id, poll_drafts[user_id].description, poll_drafts[user_id].options)

    # _ = storage.conn.createBet()
    # bet_id = len(storage.bets) + 1
    # storage.bets[bet_id] = Bet(bet_id, bet_drafts[callback_query.from_user.id][0],
    #                            [bet_drafts[callback_query.from_user.id][1], bet_drafts[callback_query.from_user.id][2]])

    edited = await callback_query.message.edit_text(f"Poll was created! ID: {poll_id}", reply_markup=None)
    at_exit(user_id)
