"""
Card set parameters
"""
from django.db.models.query import Q

from cards.models import Block, Set
from .base_parameters import CardSearchParam


class CardSetParam(CardSearchParam):
    """
    The parameter for searching by a card's set
    """

    def __init__(self, set_obj: Set):
        super().__init__()
        self.set_obj: Set = set_obj

    def query(self) -> Q:
        if self.negated:
            return ~Q(set=self.set_obj)
        return Q(set=self.set_obj)

    def get_pretty_str(self) -> str:
        return "set " + ("isn't" if self.negated else "is") + f" {self.set_obj.name}"


class CardBlockParam(CardSearchParam):
    """
    The parameter for searching by a card's block
    """

    def __init__(self, block_obj: Block):
        super().__init__()
        self.block_obj = block_obj

    def query(self) -> Q:
        if self.negated:
            return ~Q(set__block=self.block_obj)
        return Q(set__block=self.block_obj)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} in {self.block_obj}"


class CardLegalityParam(CardSearchParam):
    def __init__(self, format_string: str):
        super().__init__()
        self.format_string = format_string

    def query(self) -> Q:
        query = Q(card__legalities__format__name__iexact=self.format_string)
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return (
            f"isn't legal in {self.format_string}"
            if self.negated
            else f"is legal in {self.format_string}"
        )
