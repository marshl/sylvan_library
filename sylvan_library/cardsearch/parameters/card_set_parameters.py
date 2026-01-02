"""
Card set parameters
"""

import datetime
from typing import List

from django.db.models.query import Q

from sylvan_library.cards.models.legality import CardLegality
from sylvan_library.cards.models.sets import Set, Block, Format
from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchContext,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
    CardSearchParameter,
    OPERATOR_MAPPING,
    CardSearchBinaryParameter,
)


def user_query_to_set(value: str) -> Set:
    # Search by code EXACT
    matching_sets = Set.objects.filter(Q(code__iexact=value) | Q(name__iexact=value))
    if matching_sets.exists():
        return matching_sets.first()

    matching_sets = Set.objects.filter(name__icontains=value)

    if not matching_sets.exists():
        raise QueryValidationError(f'Unknown set "{value}"') from ex

    if matching_sets.count() > 1:
        matching_sets = matching_sets.exclude(type="promo")

    if matching_sets.count() > 1:
        raise QueryValidationError(f'Multiple sets match "{value}"')

    return matching_sets.first()


class CardSetParam(CardSearchParameter):
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

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.set_obj = None

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        self.set_obj = user_query_to_set(self.value)

    def query(self, query_context: QueryContext) -> Q:
        return Q(
            **{
                (
                    "set"
                    if query_context.search_mode == CardSearchContext.PRINTING
                    else "printings__set"
                ): self.set_obj,
                "_negated": self.negated,
            }
        )

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the card "
            + ("isn't" if self.negated else "is")
            + f" in {self.set_obj.name}"
        )


class CardBlockParam(CardSearchParameter):
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

    def __init__(self, parameter_args: ParameterArgs, negated: bool = False):
        super().__init__(parameter_args, negated)
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


class CardLegalityParam(CardSearchParameter):
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

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
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
        except Format.DoesNotExist as ex:
            raise QueryValidationError(f'Format "{self.value}" does not exist.') from ex

    def query(self, query_context: QueryContext) -> Q:
        assert self.card_format
        legality_query = CardLegality.objects.filter(
            format=self.card_format,
            restriction__iexact=self.restriction,
        )
        query = Q(
            **{
                (
                    "card__legalities__in"
                    if query_context.search_mode == CardSearchContext.PRINTING
                    else "legalities__in"
                ): legality_query
            }
        )
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            f"it's not {self.restriction} in {self.card_format.name}"
            if self.negated
            else f"it's {self.restriction} in {self.card_format.name}"
        )


class CardDateParam(CardSearchParameter):
    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "date"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return ["<", "<=", ">=", ">"]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["date", "d"]

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.date = None

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        try:
            year = int(self.value)
        except ValueError:
            pass
        else:
            self.date = datetime.date(year, 1, 1)
            return

        try:
            self.date = datetime.date.fromisoformat(self.value)
            return
        except ValueError:
            pass

        set_obj = user_query_to_set(self.value)
        self.date = set_obj.release_date

    def query(self, query_context: QueryContext) -> Q:
        django_op = OPERATOR_MAPPING[self.operator]
        query = {"set__release_date" + django_op: self.date}

        return Q(**query, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the card "
            + ("wasn't" if self.negated else "was")
            + f" released "
            + ("before" if self.operator in ("<", "<=") else "after")
            + " "
            + self.date.isoformat()
        )


class CardUniversesBeyondParam(CardSearchBinaryParameter):
    """
    A parameter for searching for cards that have been in a Universes Beyond set
    For example, Doctor Who, Lord of the Rings (and commander)
    """

    @classmethod
    def get_is_keywords(cls) -> List[str]:
        return ["ub", "universes-beyond"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "is universes beyond"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        return Q(
            **{
                (
                    "set__code__in"
                    if query_context.search_mode == CardSearchContext.PRINTING
                    else "printings__set__code__in"
                ): list(
                    {
                        "40K",
                        "ACR",
                        "BOT",
                        "FCA",
                        "FIC",
                        "FIN",
                        "LTC",
                        "LTR",
                        "PIP",
                        "REX",
                        "SPC",
                        "SPE",
                        "SPM",
                        "SPM",
                        "T40K",
                        "TFIC",
                        "TFIN",
                        "TLA",
                        "TWHO",
                        "WHO",
                    }
                ),
                "_negated": self.negated,
            }
        )

    def get_pretty_str(self, query_context: QueryContext) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} multicoloured"
