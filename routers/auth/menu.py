import json
import logging
import uuid
from dataclasses import dataclass

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from drafts.account import account_drafts
from helpers import delete_markup, handle_ambiguous_reply
from routers.auth.login import login_rt
from routers.auth.signup import signup_rt
from state_holders.messages import message_holder
from storage.storage import storage
from state_holders.states import State, state_holder
from state_holders.callbacks import Callback


authenticator_rt = Router(name=__name__)
authenticator_rt.include_routers(signup_rt, login_rt)


@authenticator_rt.message(Command("auth"))
@authenticator_rt.callback_query(F.data == Callback.RETURN_TO_AUTH_MENU)
async def auth(update: Update) -> None:
    logging.info("auth")
    user_id = update.from_user.id

    if not user_id in state_holder.states.keys():
        state_holder.set(user_id, State.NONE)

    if user_id in storage.active_mapping.keys():
        await handle_ambiguous_reply(user_id, update, f"You have already signed in as {storage.accounts[storage.active_mapping[user_id]].username}", None)
        return

    account_drafts.pop(user_id, None)
    cancel_button = InlineKeyboardButton(text="Cancel", callback_data=Callback.EXIT_AUTH_MENU)
    register_button = InlineKeyboardButton(text="Register", callback_data=Callback.REGISTER_NEW_ACCOUNT)
    log_in_button = InlineKeyboardButton(text="Log in [x]", callback_data=Callback.LOG_IN_TO_ACCOUNT)
    buttons = [
        [cancel_button],
        [register_button, log_in_button],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await handle_ambiguous_reply(user_id, update, f"Create an account or sign in with existing one", markup)


@authenticator_rt.callback_query(F.data == Callback.EXIT_AUTH_MENU)
async def exit_auth_menu(callback_query: CallbackQuery) -> None:
    logging.info(f"exit_auth_menu")
    user_id = callback_query.from_user.id

    await callback_query.answer(f"Auth cancelled...")
    deleted = await callback_query.message.delete()
