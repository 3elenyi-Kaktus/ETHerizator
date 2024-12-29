from enum import Enum


class State(str, Enum):
    NONE = "none"

    # authenticator router
    AWAITING_REGISTER_USERNAME = "awaiting_register_username"
    AWAITING_REGISTER_PASSWORD = "awaiting_register_password"
    AWAITING_REGISTER_PASSWORD_DOUBLE_CHECK = "awaiting_register_password_double_check"

    # bet_creator_router states
    AWAITING_POLL_DESCRIPTION = "awaiting_bet_description"
    AWAITING_POLL_OPTION = "awaiting_bet_option"
    AWAITING_EDITED_POLL_OPTION = "awaiting_edited_bet_option"

    # wager_maker_router states
    AWAITING_BET_WAGER_AMOUNT = "awaiting_wager_ether_amount"

    # REGISTERING = "registering"


class ConversationStatesHolder:
    def __init__(self):
        self.states: dict[int, State] = {}

    def set(self, user_id: int, state: State | str) -> None:
        self.states[user_id] = state

    def get(self, user_id: int) -> State | str:
        return self.states.get(user_id, None)

    def __json__(self):
        return self.states


state_holder: ConversationStatesHolder = ConversationStatesHolder()
