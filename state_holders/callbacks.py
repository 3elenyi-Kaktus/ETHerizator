from enum import Enum


class Callback(str, Enum):
    TODO = "TODO"

    EDIT_BET_DESCRIPTION = "edit_bet_description"
    ADD_BET_OPTION = "add_bet_option"
    ENTER_EDIT_BET_OPTIONS_SELECTION = "enter_edit_bet_options_selection"
    ENTER_DELETE_BET_OPTIONS_SELECTION = "enter_delete_bet_options_selection"
    EDIT_BET_OPTION = "edit_bet_option"
    DELETE_BET_OPTION = "delete_bet_option"
    DISCARD_CURRENT_BET_CHANGES = "discard_current_bet_changes"
    CANCEL_BET_CREATION = "cancel_bet_creation"
    APPROVE_BET_CREATION = "approve_bet_creation"




    EXIT_FROM_BET_MAKING = "exit_from_bet_making"
    SELECT_BET_ID = "select_bet_id"
    # PREVIOUS_PAGE_BET_MAKING = "previous_page_bet_making"
    # NEXT_PAGE_BET_MAKING = "next_page_bet_making"
    CHOSEN_BET_OPTION = "chosen_bet_option"
    APPROVE_BET_MAKING = "approve_bet_making"

    EXIT_FROM_REGISTERING = "exit_from_registering"
    APPROVE_REGISTER = "approve_register"
