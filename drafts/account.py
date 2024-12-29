from dataclasses import dataclass


@dataclass
class AccountDraft:
    id: int
    username: str = ""
    password: str = ""

    def __json__(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
        }


account_drafts: dict[int, AccountDraft] = {}