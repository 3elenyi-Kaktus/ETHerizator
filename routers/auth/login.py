import logging
import uuid
from dataclasses import dataclass

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

from helpers import delete_markup
from routers.auth.signup import signup_rt
from state_holders.messages import message_holder
from storage.storage import storage
from state_holders.states import State, state_holder
from state_holders.callbacks import Callback


login_rt = Router(name=__name__)
