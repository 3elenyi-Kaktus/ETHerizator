from storage.bet import Bet


class Storage:
    def __init__(self):
        self.bets: dict[int, Bet] = {0: Bet(0, "Test bet", ["lol", "kek", "azaza"])}
        # self.user_wagers: dict[int, tuple[int, int, int]] = {}
        self.balances: dict[int, int] = {}
        # self.registers: dict[int, str] = {}


storage: Storage = Storage()
