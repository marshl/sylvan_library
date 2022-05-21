"""
Card set parameters
"""
from django.db.models.query import Q

from cards.models.legality import CardLegality
from cards.models.sets import Set, Block
from cardsearch.parameters.base_parameters import CardSearchParam


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
        return "the card " + ("isn't" if self.negated else "is") + f" in {self.set_obj.name}"


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
    """
    The parameter for searching by a card's "legality" (banned in a format, legal in a format etc.)
    """
    def __init__(self, format_string: str, restriction: str):
        super().__init__()
        self.format_string = format_string
        self.restriction = restriction

    def query(self) -> Q:
        legality_query = CardLegality.objects.filter(
            format__name__iexact=self.format_string,
            restriction__iexact=self.restriction,
        )
        query = Q(card__legalities__in=legality_query)
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return (
            f"it's {self.restriction} in {self.format_string}"
            if self.negated
            else f"it's {self.restriction} in {self.format_string}"
        )
