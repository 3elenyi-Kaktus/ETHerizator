from dataclasses import dataclass, field


@dataclass
class Wager:
    better_id: int
    amount: int


# TODO delicate dance with initial supplies of 1 wei at every option
@dataclass
class PollOption:
    id: int
    description: str
    wagers: dict[int, Wager] = field(default_factory=dict)
    supply: int = 1


class Poll:
    def __init__(self, id_: int, description: str, options: list[str]):
        self.id: int = id_
        self.description: str = description
        self.options: list[PollOption] = [PollOption(i, x) for i, x in enumerate(options, start=0)]
        self.total_supply: int = len(self.options)

    def get_total_supply(self) -> int:
        return self.total_supply

    def get_option_coeff(self, option_id: int) -> float:
        return float(self.total_supply) / self.options[option_id].supply

    def get_option_coeffs(self) -> list[float]:
        return [float(self.total_supply) / x.supply for x in self.options]

    def get_description(self) -> str:
        return self.description

    def get_option_description(self, option_id: int) -> str:
        return self.options[option_id].description

    def get_option_descriptions(self) -> list[str]:
        return [x.description for x in self.options]

    def make_bet(self, better_id: int, amount: int, option_id: int) -> bool:
        if better_id in self.options[option_id].wagers.keys():
            return False
        self.options[option_id].wagers[better_id] = Wager(better_id, amount)
        return True

    def cancel_bet(self, better_id: int, option_id: int) -> bool:
        if better_id not in self.options[option_id].wagers.keys():
            return False
        self.options[option_id].wagers.pop(better_id)
        return True
