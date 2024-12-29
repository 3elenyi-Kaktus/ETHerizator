from enum import Enum


class Callback(str, Enum):
    TODO = "todo"

    # root router
    RETURN_TO_MAIN_MENU = "return_to_main_menu"
    OPEN_POLLS_MENU = "open_polls_menu"
    OPEN_ACCOUNT_MENU = "open_account_menu"
    RUN_ROULETTE = "run_roulette"
    RUN_GAMES = "run_games"
    RUN_SLOTS = "run_slots"
    MANAGE_POLLS = "manage_polls"
    MANAGE_BETS = "manage_bets"

    # poll_creator router callbacks
    CREATE_NEW_POLL = "create_new_poll"
    EDIT_POLL_DESCRIPTION = "edit_poll_description"
    ADD_POLL_OPTION = "add_poll_option"
    ENTER_EDIT_POLL_OPTIONS_SELECTION = "enter_edit_poll_options_selection"
    ENTER_DELETE_POLL_OPTIONS_SELECTION = "enter_delete_poll_options_selection"
    EDIT_POLL_OPTION = "edit_poll_option"
    DELETE_POLL_OPTION = "delete_poll_option"
    DISCARD_CURRENT_POLL_CHANGES = "discard_current_poll_changes"
    CANCEL_POLL_CREATION = "cancel_poll_creation"
    APPROVE_POLL_CREATION = "approve_poll_creation"

    # bet_maker router states
    CREATE_NEW_BET = "create_new_bet"
    SELECT_POLL_ID = "select_poll_id"
    SELECT_POLL_OPTION = "select_poll_option"
    DISCARD_BET_POLL_ID_CHANGES = "discard_bet_poll_id_changes"
    DISCARD_BET_POLL_OPTION_CHANGES = "discard_bet_poll_option_changes"
    DISCARD_BET_WAGER_CHANGES = "discard_bet_wager_changes"
    CANCEL_BET_MAKING = "cancel_bet_making"
    APPROVE_BET_MAKING = "approve_bet_making"

    # EXIT_FROM_REGISTERING = "exit_from_registering"
    # APPROVE_REGISTER = "approve_register"
