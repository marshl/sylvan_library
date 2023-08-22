"""
Card set parameters
"""
from typing import List

from django.db.models.query import Q

from cards.models.legality import CardLegality
from cards.models.sets import Set, Block, Format
from cardsearch.parameters.base_parameters import (
    CardSearchContext,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
    CardTextParameter,
)


class CardSetParam(CardTextParameter):
    """
    The parameter for searching by a card's set
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "set"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["set", "s"]

    def __init__(self, negated: bool, param_args: ParameterArgs):
        super().__init__(negated, param_args)
        self.set_obj = None

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        self.set_obj = self.get_set()

    def get_set(self) -> Set:
        try:
            return Set.objects.get(code__iexact=self.value)
        except Set.DoesNotExist:
            pass

        try:
            return Set.objects.get(name__iexact=self.value)
        except Set.DoesNotExist:
            pass

        try:
            return Set.objects.get(name__icontains=self.value)
        except Set.DoesNotExist as ex:
            raise QueryValidationError(f'Unknown set "{self.value}"') from ex
        except Set.MultipleObjectsReturned:
            try:
                return Set.objects.get(name__icontains=self.value).exclude(type="promo")
            except (Set.DoesNotExist, Set.MultipleObjectsReturned) as ex:
                raise QueryValidationError(
                    f'Multiple sets match "{self.value}"'
                ) from ex

    def query(self, query_context: QueryContext) -> Q:
        if self.negated:
            return ~Q(set=self.set_obj)
        return Q(set=self.set_obj)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the card "
            + ("isn't" if self.negated else "is")
            + f" in {self.set_obj.name}"
        )


class CardBlockParam(CardTextParameter):
    """
    The parameter for searching by a card's block
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "block"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["block", "b"]

    def __init__(self, negated: bool, parameter_args: ParameterArgs):
        super().__init__(negated, parameter_args)
        self.block_obj = None

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        self.block_obj = self.get_block()

    def get_block(self):
        try:
            return Block.objects.get(name__iexact=self.value)
        except (Block.DoesNotExist, Block.MultipleObjectsReturned):
            pass

        card_set = None
        try:
            card_set = Set.objects.get(code__iexact=self.value)
        except Set.DoesNotExist:
            try:
                card_set = Set.objects.get(name__icontains=self.value)
            except (Set.DoesNotExist, Set.MultipleObjectsReturned):
                pass

        if card_set and card_set.block:
            return card_set.block

        try:
            return Block.objects.get(name__icontains=self.value)
        except Block.DoesNotExist as ex:
            raise QueryValidationError(f'Unknown block "{self.value}"') from ex
        except Block.MultipleObjectsReturned as ex:
            raise QueryValidationError(f'Multiple blocks match "{self.value}"') from ex

    def query(self, query_context: QueryContext) -> Q:
        assert self.block_obj
        if self.negated:
            return ~Q(set__block=self.block_obj)
        return Q(set__block=self.block_obj)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} in {self.block_obj}"


class CardLegalityParam(CardTextParameter):
    """
    The parameter for searching by a card's "legality" (banned in a format, legal in a format etc.)
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "format"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["format", "f", "legal", "legality", "banned", "restricted"]

    def __init__(self, negated: bool, param_args: ParameterArgs):
        super().__init__(negated, param_args)
        if param_args.keyword == "banned":
            self.restriction = "banned"
        elif param_args.keyword == "restricted":
            self.restriction = "restricted"
        else:
            self.restriction = "legal"
        self.card_format = None

    def validate(self, query_context) -> None:
        super().validate(query_context)

        try:
            self.card_format = Format.objects.get(name__iexact=self.value)
        except Format.DoesNotExist:
            raise QueryValidationError(f'Format "{self.value}" does not exist.')

    def query(self, query_context: QueryContext) -> Q:
        assert self.card_format
        legality_query = CardLegality.objects.filter(
            format=self.card_format,
            restriction__iexact=self.restriction,
        )
        query = Q(card__legalities__in=legality_query)
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            f"it's not {self.restriction} in {self.card_format.name}"
            if self.negated
            else f"it's {self.restriction} in {self.card_format.name}"
        )
