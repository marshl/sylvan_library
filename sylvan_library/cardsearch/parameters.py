"""
The module for all search parameters
"""
from abc import ABC
from collections import Counter
import logging
from django.db.models.query import Q, F
from django.db.models.functions import Concat
from django.db.models import Sum, Case, When, IntegerField, Value
from django.contrib.auth.models import User
from bitfield.types import Bit

from cards.models import Block, Card, Rarity, Set, Colour
from django.db.models import F
from typing import Union
from typing import List

logger = logging.getLogger("django")

OPERATOR_MAPPING = {
    "<": "__lt",
    "<=": "__lte",
    ">": "__gt",
    ">=": "__gte",
    "=": "",
    ":": "",
    "LT": "__lt",
    "LTE": "__lte",
    "GT": "__gt",
    "GTE": "__gte",
    "EQ": "",
}

NUMERICAL_OPERATOR_CHOICES = (
    ("GT", ">"),
    ("GTE", ">="),
    ("LT", "<"),
    ("LTE", "<="),
    ("EQ", "="),
)


class CardSearchParam:
    """
    The base search parameter class
    """

    def query(self) -> Q:
        """
        Returns the query of this parameter and all child parameters
        :return:
        """
        raise NotImplementedError("Please implement this method")

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        raise NotImplementedError(
            "Please implement get_pretty_str on " + type(self).__name__
        )


# pylint: disable=abstract-method
class BranchParam(CardSearchParam):
    """
    The base branching parameter class (subclassed to "and" and "or" parameters)
    """

    def __init__(self):
        super().__init__()
        self.child_parameters: List[CardSearchParam] = list()

    def add_parameter(self, param: CardSearchParam):
        """
        Adds a child parameter to this node
        :param param: The child to add
        :return:
        """
        self.child_parameters.append(param)
        return param


class AndParam(BranchParam):
    """
    The class for combining two or more sub-parameters with an "AND" clause
    """

    def __init__(self, inverse: bool = False):
        self.inverse = inverse
        super().__init__()

    def query(self) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found, returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            query.add(child.query(), Q.AND)

        if self.inverse:
            return ~query
        return query

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str()
        result = " and ".join(param.get_pretty_str() for param in self.child_parameters)
        if within_or_block:
            return "(" + result + ")"

        return result


class OrParam(BranchParam):
    """
    The class for combining two or more sub-parameters with an "OR" clause
    """

    def __init__(self, inverse: bool = False):
        self.inverse = inverse
        super().__init__()

    def query(self) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found,returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            query.add(child.query(), Q.OR)

        return ~query if self.inverse else query

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str()
        return " or ".join(
            param.get_pretty_str(within_or_block=True)
            for param in self.child_parameters
        )


class CardNameParam(CardSearchParam):
    """
    The parameter for searching by a card's name
    """

    def __init__(self, card_name, match_exact: bool = False, inverse: bool = False):
        super().__init__()
        self.card_name = card_name
        self.inverse = inverse
        self.match_exact = match_exact

    def query(self) -> Q:
        if self.match_exact:
            q = Q(name__iexact=self.card_name)
        else:
            q = Q(name__icontains=self.card_name)

        return ~q if self.inverse else q

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        if self.inverse:
            return f'the name does not contain "{self.card_name}"'
        return f'the name contains "{self.card_name}"'


class CardRulesTextParam(CardSearchParam):
    """
    The parameter for searching by a card's rules text
    """

    def __init__(self, card_rules, exact: bool = False, inverse: bool = False):
        super().__init__()
        self.card_rules = card_rules
        self.exact_match = exact
        self.inverse = inverse

    def query(self) -> Q:
        if "~" not in self.card_rules:
            if self.exact_match:
                return Q(rules_text__iexact=self.card_rules)
            return Q(rules_text__icontains=self.card_rules)

        chunks = [Value(c) for c in self.card_rules.split("~")]
        params = [F("name")] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.exact_match:
            query = Q(rules_text__iexact=Concat(*params))
        else:
            query = Q(rules_text__icontains=Concat(*params))

        params = [Value("this spell")] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.exact_match:
            query |= Q(rules_text__iexact=Concat(*params))
        else:
            query |= Q(rules_text__icontains=Concat(*params))

        return ~query if self.inverse else query

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        if self.inverse:
            return f"rules text {'is not' if self.exact_match else 'does nto contain'} \"{self.card_rules}\""
        return f"rules text {'is' if self.exact_match else 'contains'} \"{self.card_rules}\""


class CardFlavourTextParam(CardSearchParam):
    """
    The parameter for searching by a card's flavour text
    """

    def __init__(self, flavour_text):
        super().__init__()
        self.flavour_text = flavour_text

    def query(self) -> Q:
        return Q(printings__flavour_text__icontains=self.flavour_text)


class CardTypeParam(CardSearchParam):
    """
    The parameter for searching by a card's type or supertypes
    """

    def __init__(self, card_type):
        super().__init__()
        self.card_type = card_type

    def query(self) -> Q:
        return Q(type__icontains=self.card_type)


class CardSubtypeParam(CardSearchParam):
    """
    The parameter for searching by a card's subtypes
    """

    def __init__(self, card_subtype):
        super().__init__()
        self.card_subtype = card_subtype

    def query(self) -> Q:
        return Q(subtype__icontains=self.card_subtype)


class CardGenericTypeParam(CardSearchParam):
    def __init__(self, card_type: str, operator: str, inverse: bool = False):
        super().__init__()
        self.card_type = card_type
        self.operator = operator
        self.inverse = inverse

    def query(self) -> Q:
        if self.operator == "=":
            result = Q(type__iexact=self.card_type) | Q(subtype__iexact=self.card_type)
        else:
            result = Q(type__icontains=self.card_type) | Q(
                subtype__icontains=self.card_type
            )
        return ~result if self.inverse else result

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        return f'the card types include "{self.card_type}"'


class CardColourParam(CardSearchParam):
    """
    The parameter for searching by a card's colour
    """

    def __init__(self, card_colour: Bit):
        super().__init__()
        self.card_colour = card_colour

    def query(self) -> Q:
        return Q(colour_flags=self.card_colour)


class CardComplexColourParam(CardSearchParam):
    def __init__(
        self,
        colours: int,
        operator: str = "=",
        inverse: bool = False,
        identity: bool = False,
    ):
        assert colours >= 0
        assert colours <= (
            Card.colour_flags.white
            | Card.colour_flags.blue
            | Card.colour_flags.black
            | Card.colour_flags.red
            | Card.colour_flags.green
        )
        self.colours = colours
        if operator == ":":
            self.operator = "<=" if identity else ">="
        else:
            self.operator = operator
        self.inverse = inverse
        self.identity = identity

    def query(self) -> Q:
        field = "colour_identity_flags" if self.identity else "colour_flags"
        if self.operator == ">=":
            return (
                ~Q(**{field: self.colours})
                if self.inverse
                else Q(**{field: self.colours})
            )

        if self.operator == ">" or self.operator == "=":
            result = Q(**{field: self.colours})
            exclude = Q()

            for c in Colour.objects.exclude(symbol="C"):
                if not c.bit_value & self.colours:
                    exclude |= Q(**{field: c.bit_value})
            if exclude:
                result &= exclude if self.operator == ">" else ~exclude
            return ~result if self.inverse else result

        if self.operator == "<" or self.operator == "<=":
            include = Q()
            exclude = Q()
            for c in Colour.objects.exclude(symbol="C"):
                if c.bit_value & self.colours:
                    include |= Q(**{field: c.bit_value})
                else:
                    exclude &= ~Q(**{field: c.bit_value})

            if self.identity:
                include |= Q(colour_identity_flags=0)

            if self.operator == "<":
                result = include & exclude & ~Q(**{field: self.colours})
                return ~result if self.inverse else result
            result = include & exclude
            return ~result if self.inverse else result

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        if self.colours == 0:
            return (
                "is cards have colourless identity"
                if self.identity
                else "the cards are colourless"
            )

        colour_names = ""
        for c in Colour.objects.all():
            if c.bit_value & self.colours:
                colour_names += c.symbol

        param_type = "colour identity" if self.identity else "colours"
        return f"the {param_type} {self.operator} {colour_names}"


class CardColourIdentityParam(CardSearchParam):
    """
    The parameter for searching by a card's colour identity
    """

    def __init__(self, colour_identity: Bit):
        super().__init__()
        self.colour_identity = colour_identity

    def query(self) -> Q:
        return Q(colour_identity_flags=self.colour_identity)


class CardMulticolouredOnlyParam(CardSearchParam):
    """
    The parameter for searching by whether a card is multicoloured or not
    """

    def query(self) -> Q:
        return Q(colour_count__gt=1)


class CardSetParam(CardSearchParam):
    """
    The parameer for searching by a card's set
    """

    def __init__(self, set_obj: Set):
        super().__init__()
        self.set_obj = set_obj

    def query(self) -> Q:
        return Q(printings__set=self.set_obj)


class CardBlockParam(CardSearchParam):
    """
    The parameter for searching by a card's block
    """

    def __init__(self, block_obj: Block):
        super().__init__()
        self.block_obj = block_obj

    def query(self) -> Q:
        return Q(printings__set__block=self.block_obj)


class CardOwnerParam(CardSearchParam):
    """
    The parameter for searching by whether it is owned by a given user
    """

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def query(self) -> Q:
        return Q(
            printings__printed_languages__physical_cards__ownerships__owner=self.user
        )


class CardManaCostParam(CardSearchParam):
    """
    The parameter for searching by a card's mana cost
    """

    def __init__(self, cost: str, exact_match: bool):
        super().__init__()
        self.cost = cost
        self.exact_match = exact_match

    def query(self) -> Q:
        return Q(cost=self.cost) if self.exact_match else Q(cost__icontains=self.cost)


SYMBOL_REMAPPING = {
    "w/r": "r/w",
    "u/g": "g/u",
    "b/w": "w/b",
    "r/u": "u/r",
    "g/b": "b/g",
}


class CardManaCostComplexParam(CardSearchParam):
    def __init__(self, cost: str, operator: str):
        super().__init__()
        self.cost_text = cost.lower()
        self.operator = operator

        self.symbol_counts = Counter()
        pos = 0
        current_symbol = ""
        in_symbol = False
        while True:
            if pos >= len(self.cost_text):
                break
            char = self.cost_text[pos]
            if char == "{":
                if in_symbol:
                    raise Exception()
                in_symbol = True
                current_symbol = ""
            elif char == "}":
                if in_symbol:
                    self.symbol_counts[
                        SYMBOL_REMAPPING.get(current_symbol, current_symbol)
                    ] += 1

                    in_symbol = False
                else:
                    raise Exception()
            elif in_symbol:
                current_symbol += char
            elif not in_symbol:
                self.symbol_counts[char] += 1

            pos += 1

        if in_symbol:
            raise Exception()

    def query(self) -> Q:
        query = Q()

        for symbol, count in dict(self.symbol_counts).items():
            num = None
            try:
                num = int(symbol)
            except TypeError:
                pass

            if num is not None:
                pass
            else:
                query &= Q(cost__icontains=("{" + symbol + "}") * count)
                if self.operator == "=":
                    query &= ~Q(cost__icontains=("{" + symbol + "}") * (count + 1))

        return query


class CardRarityParam(CardSearchParam):
    """
    The parameter for searching by a card's rarity
    """

    def __init__(self, rarity: Rarity):
        super().__init__()
        self.rarity = rarity

    def query(self) -> Q:
        return Q(id__in=Card.objects.filter(printings__rarity=self.rarity))


class CardNumericalParam(CardSearchParam, ABC):
    """
    The base parameter for searching by some numerical value
    """

    def __init__(self, number: Union[int, F], operator: str):
        super().__init__()
        self.number = number
        self.operator = operator

    def get_args(self, field: str) -> dict:
        """
        Shortcut to generate the Q object parameters for the given field
        :param field: The card field to compare with
        :return:
        """
        django_op = OPERATOR_MAPPING[self.operator]
        return {field + django_op: self.number}


class CardNumPowerParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical power
    """

    def query(self) -> Q:
        args = self.get_args("num_power")
        return Q(**args) & Q(power__isnull=False)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        return f"the power {self.operator} {self.number}"


class CardNumToughnessParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical toughness
    """

    def query(self) -> Q:
        args = self.get_args("num_toughness")
        return Q(**args) & Q(toughness__isnull=False)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        return f"the toughness {self.operator} {self.number}"


class CardNumLoyaltyParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical loyalty
    """

    def query(self) -> Q:
        args = self.get_args("num_loyalty")
        return Q(**args)


class CardCmcParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical converted mana cost
    """

    def query(self) -> Q:
        args = self.get_args("cmc")
        q = Q()
        if isinstance(self.number, F):
            q &= Q(**{"toughness__isnull": False})
        return q & Q(**args)


class CardColourCountParam(CardNumericalParam):
    def __init__(self, number: int, operator: str, identity: bool = False):
        super().__init__(number, operator)
        self.identity = identity

    def query(self) -> Q:
        args = (
            self.get_args("colour_identity_count")
            if self.identity
            else self.get_args("colour_count")
        )
        return Q(**args)


class CardOwnershipCountParam(CardNumericalParam):
    """
    The parameter for searching by how many a user owns of it
    """

    def __init__(self, user: User, operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def query(self) -> Q:
        annotated_result = Card.objects.annotate(
            ownership_count=Sum(
                Case(
                    When(
                        printings__printed_languages__physical_cards__ownerships__owner=self.user,
                        then="printings__printed_languages__physical_cards__ownerships__count",
                    ),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )

        kwargs = {f"ownership_count{OPERATOR_MAPPING[self.operator]}": self.number}
        query = Q(**kwargs)
        return Q(id__in=annotated_result.filter(query))

    def get_pretty_str(selFixedf, within_or_block: bool = False) -> str:
        return f"you own {self.operator} {self.number}"


class CardSortParam:
    """
    The base sorting parameter
    """

    def __init__(self, descending: bool = False):
        super().__init__()
        self.sort_descending = descending

    def get_sort_list(self) -> list:
        """
        Gets the sort list taking order into account
        :return:
        """
        return [
            "-" + arg if self.sort_descending else arg for arg in self.get_sort_keys()
        ]

    def get_sort_keys(self) -> list:
        """
        Gets the list of attributes to be sorted by
        :return:
        """
        raise NotImplementedError()


class CardNameSortParam(CardSortParam):
    """
    THe sort parameter for a card's name
    """

    def get_sort_keys(self) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        return ["name"]


class CardPowerSortParam(CardSortParam):
    """
    THe sort parameter for a card's numerical power
    """

    def get_sort_keys(self) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        return ["num_power"]


class CardCollectorNumSortParam(CardSortParam):
    """
    The sort parameter for a card's collector number
    """

    def get_sort_keys(self) -> list:
        return ["printings__number"]


class CardColourSortParam(CardSortParam):
    """
    The sort parameter for a card's colour key
    """

    def get_sort_keys(self) -> list:
        return ["colour_sort_key"]


class CardColourWeightSortParam(CardSortParam):
    """
    The sort parameter for a card's colour weight
    """

    def get_sort_keys(self) -> list:
        return ["cmc", "colour_sort_key", "colour_weight"]
