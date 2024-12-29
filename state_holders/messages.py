from aiogram.types import Message


class LastMessageHolder:
    def __init__(self):
        self.messages: dict[int, Message] = {}

    def get(self, user_id: int) -> Message:
        return self.messages.get(user_id, None)

    def set(self, user_id: int, message: Message) -> None:
        self.messages[user_id] = message

    def delete(self, user_id: int) -> None:
        self.messages.pop(user_id, None)

    def __json__(self):
        return {k: v.message_id for k, v in self.messages.items()}


message_holder: LastMessageHolder = LastMessageHolder()
