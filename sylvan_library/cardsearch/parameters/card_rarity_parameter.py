"""
Card rarity parameters
"""
from django.db.models.query import Q

from cards.models.rarity import Rarity
from cardsearch.parameters.base_parameters import (
    OPERATOR_MAPPING,
    OPERATOR_TO_WORDY_MAPPING,
    CardSearchParam,
)


class CardRarityParam(CardSearchParam):
    """
    The parameter for searching by a card's rarity
    """

    def __init__(self, rarity: Rarity, operator: str):
        super().__init__()
        self.rarity = rarity
        self.operator = operator
        if self.operator == ":":
            self.operator = "="

    def query(self) -> Q:
        if self.operator == "=":
            return Q(rarity=self.rarity)

        return Q(
            **{
                f"rarity__display_order{OPERATOR_MAPPING[self.operator]}": self.rarity.display_order
            }
        )

    def get_pretty_str(self) -> str:
        return (
            "the rarity "
            + ("isn't" if self.negated else "is")
            + (
                " " + OPERATOR_TO_WORDY_MAPPING[self.operator]
                if self.operator not in (":", "=")
                else ""
            )
            + f" {self.rarity.name.lower()}"
        )
