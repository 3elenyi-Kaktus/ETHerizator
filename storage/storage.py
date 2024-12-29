from storage.poll import Poll


class Storage:
    def __init__(self):
        self.polls: dict[int, Poll] = {0: Poll(0, "Test bet", ["lol", "kek", "azaza"])}
        # self.user_wagers: dict[int, tuple[int, int, int]] = {}
        self.balances: dict[int, int] = {}
        # self.registers: dict[int, str] = {}


storage: Storage = Storage()
