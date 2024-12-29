import json
import logging
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from drafts.account import account_drafts, AccountDraft
from helpers import delete_markup, handle_ambiguous_reply
from state_holders.messages import message_holder
from storage.storage import storage, Account
from state_holders.states import State, state_holder
from state_holders.callbacks import Callback


def at_exit(user_id: int):
    message_holder.delete(user_id)
    account_drafts.pop(user_id, None)
    state_holder.set(user_id, State.NONE)


def gen_account_id() -> int:
    return uuid.uuid4().int


signup_rt = Router(name=__name__)


@signup_rt.message(Command("view_signup_router"))
async def view_signup_router(message: Message):
    logging.info(f"view_signup_router")
    _ = await message.answer(
        f"Last messages: {json.dumps(message_holder, indent=4)}\n"
        f"Account drafts: {json.dumps(account_drafts, indent=4)}\n"
        f"States: {json.dumps(state_holder, indent=4)}"
    )


@signup_rt.callback_query(lambda x: x.data in [Callback.REGISTER_NEW_ACCOUNT, Callback.DISCARD_REGISTER_USERNAME])
async def register_new_account(callback_query: CallbackQuery) -> None:
    logging.info(f"register_new_account")
    user_id = callback_query.from_user.id

    account_drafts[user_id] = AccountDraft(gen_account_id())
    state_holder.set(user_id, State.AWAITING_REGISTER_USERNAME)

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.RETURN_TO_AUTH_MENU)
    buttons = [[cancel_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    edited = await callback_query.message.edit_text(f"Please, create a username:", reply_markup=markup)
    message_holder.set(user_id, edited)


@signup_rt.message(lambda x: state_holder.get(x.from_user.id) == State.AWAITING_REGISTER_USERNAME)
@signup_rt.callback_query(F.data == Callback.DISCARD_REGISTER_PASSWORD)
async def awaiting_register_username(update: Update) -> None:
    logging.info(f"awaiting_register_username")
    user_id = update.from_user.id
    if isinstance(update, Message):
        await delete_markup(message_holder.get(user_id))

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_REGISTER_USERNAME)
    buttons = [[cancel_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(update, Message):
        username = update.text
        for account in storage.accounts.values():
            if account.username == username:
                answer = await update.answer(f"Username {username} already exists!\n"
                                             f"Please, try another one:", reply_markup=markup
                )
                message_holder.set(user_id, answer)
                return

        account_drafts[user_id].username = username
    state_holder.set(user_id, State.AWAITING_REGISTER_PASSWORD)

    await handle_ambiguous_reply(user_id, update,
                                 f"Please, create new password (at least 8 characters):", markup)


@signup_rt.message(lambda x: state_holder.get(x.from_user.id) == State.AWAITING_REGISTER_PASSWORD)
async def awaiting_register_password(message: Message) -> None:
    logging.info(f"awaiting_register_password")
    user_id = message.from_user.id
    await delete_markup(message_holder.get(user_id))

    cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_REGISTER_PASSWORD)
    buttons = [[cancel_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    # TODO make passwords secure by more restrictions on them
    password = message.text
    if len(password) < 8:
        answer = await message.answer(f"Your password is too short!\n"
                                      f"Please, try another one:", reply_markup=markup)
        message_holder.set(user_id, answer)
        return

    account_drafts[user_id].password = password
    state_holder.set(user_id, State.AWAITING_REGISTER_PASSWORD_DOUBLE_CHECK)
    answer = await message.answer(f"Please, confirm your password:", reply_markup=markup)
    message_holder.set(user_id, answer)


@signup_rt.message(lambda x: state_holder.get(x.from_user.id) == State.AWAITING_REGISTER_PASSWORD_DOUBLE_CHECK)
async def awaiting_register_password_double_check(message: Message) -> None:
    logging.info(f"awaiting_register_password_double_check")
    user_id = message.from_user.id
    await delete_markup(message_holder.get(user_id))

    password = message.text
    if password != account_drafts[user_id].password:
        cancel_button = InlineKeyboardButton(text="Return", callback_data=Callback.DISCARD_REGISTER_PASSWORD)
        buttons = [[cancel_button]]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        answer = await message.answer(f"Your passwords mismatch.\n"
                                      f"Please, try again:", reply_markup=markup)
        message_holder.set(user_id, answer)
        return

    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.RETURN_TO_AUTH_MENU)
    approve_button = InlineKeyboardButton(text="Approve", callback_data=Callback.APPROVE_REGISTER)
    buttons = [[cancel_button, approve_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    state_holder.set(user_id, State.NONE)
    answer = await message.answer(
        f"Your username: {account_drafts[user_id].username}\n"
        f"Password is set.\n"
        f"Do you want to proceed?", reply_markup=markup
    )
    message_holder.set(user_id, answer)


@signup_rt.callback_query(F.data == Callback.APPROVE_REGISTER)
async def approve_register(callback_query: CallbackQuery) -> None:
    logging.info(f"approve_register")
    user_id = callback_query.from_user.id

    await callback_query.answer(f"Register approved...")
    draft_account = account_drafts[user_id]
    # TODO adding 1 eth here in testing purposes
    storage.accounts[draft_account.id] = Account(
        draft_account.id, draft_account.username, draft_account.password, 1**18
    )
    storage.active_mapping[user_id] = draft_account.id

    _ = await callback_query.message.edit_text(
        f"Successfully created new account with username: {account_drafts[user_id].username}\n"
        f"Account ID: {account_drafts[user_id].id}\n"
        f"You can now continue with your business.",
        reply_markup=None,
    )
    at_exit(user_id)
