from enum import Enum


class Callback(str, Enum):
    TODO = "TODO"

    # bet_creator_router callbacks
    EDIT_BET_DESCRIPTION = "edit_bet_description"
    ADD_BET_OPTION = "add_bet_option"
    ENTER_EDIT_BET_OPTIONS_SELECTION = "enter_edit_bet_options_selection"
    ENTER_DELETE_BET_OPTIONS_SELECTION = "enter_delete_bet_options_selection"
    EDIT_BET_OPTION = "edit_bet_option"
    DELETE_BET_OPTION = "delete_bet_option"
    DISCARD_CURRENT_BET_CHANGES = "discard_current_bet_changes"
    CANCEL_BET_CREATION = "cancel_bet_creation"
    APPROVE_BET_CREATION = "approve_bet_creation"

    # wager_maker_router states
    SELECT_BET_ID = "select_bet_id"
    CHOOSE_BET_OPTION = "choose_bet_option"
    DISCARD_WAGER_BET_CHANGES = "discard_wager_bet_changes"
    DISCARD_WAGER_OPTION_CHANGES = "discard_wager_option_changes"
    DISCARD_WAGER_ETHER_CHANGES = "discard_wager_ether_changes"
    CANCEL_WAGER_MAKING = "cancel_wager_making"
    APPROVE_WAGER_MAKING = "approve_wager_making"

    # EXIT_FROM_REGISTERING = "exit_from_registering"
    # APPROVE_REGISTER = "approve_register"
