from dataclasses import dataclass

from storage.poll import Poll


@dataclass
class Account:
    id: int
    username: str
    password: str
    balance: int


class Storage:
    def __init__(self):
        self.polls: dict[int, Poll] = {0: Poll(0, "Test bet", ["lol", "kek", "azaza"])}
        self.accounts: dict[int, Account] = {}  # dict of all accounts, should go to db
        self.active_mapping: dict[int, int] = {}  # mapping of tg ID -> user account ID


storage: Storage = Storage()
