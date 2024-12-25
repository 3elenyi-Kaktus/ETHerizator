from enum import Enum


class State(str, Enum):
    NONE = "none"

    # bet_creator_router states
    AWAITING_BET_DESCRIPTION = "awaiting_bet_description"
    AWAITING_BET_OPTION = "awaiting_bet_option"
    AWAITING_EDITED_BET_OPTION = "awaiting_edited_bet_option"

    # wager_maker_router states
    AWAITING_WAGER_ETHER_AMOUNT = "awaiting_wager_ether_amount"

    # REGISTERING = "registering"


class ConversationStatesHolder:
    def __init__(self):
        self.states: dict[int, State] = {}

    def set_state(self, user_id: int, state: State | str) -> None:
        self.states[user_id] = state

    def get_state(self, user_id: int) -> State | str:
        return self.states.get(user_id, None)

    def __json__(self):
        return self.states


state_holder: ConversationStatesHolder = ConversationStatesHolder()
