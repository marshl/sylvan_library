"""
The module for all search parameters
"""
import logging
from django.db.models.query import Q, F
from django.db.models.functions import Concat
from django.db.models import Sum, Case, When, IntegerField, Value
from django.contrib.auth.models import User
from bitfield.types import Bit

from cards.models import (
    Block,
    Card,
    Rarity,
    Set,
)

logger = logging.getLogger('django')

OPERATOR_MAPPING = {'LT': '__lt', 'LTE': '__lte', 'GT': '__gt', 'GTE': '__gte', 'EQ': ''}

NUMERICAL_OPERATOR_CHOICES = (
    ('GT', '>'),
    ('GTE', '>='),
    ('LT', '<'),
    ('LTE', '<='),
    ('EQ', '='),
)


class CardSearchParam:
    """
    The base search parameter class
    """

    def __init__(self):
        self.child_parameters = list()

    def query(self) -> Q:
        raise NotImplementedError('Please implement this method')


# pylint: disable=abstract-method
class BranchParam(CardSearchParam):
    """
    The base branching parameter class (subclassed to "and" and "or" parameters)
    """

    def __init__(self):
        super().__init__()
        self.child_parameters = list()

    def add_parameter(self, param: CardSearchParam):
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
            logger.info('No child parameters found, returning empty set')
            return Card.objects.none()

        q = Q()
        for child in self.child_parameters:
            q.add(child.query(), Q.AND)

        if self.inverse:
            return ~q
        return q


class OrParam(BranchParam):
    """
    The class for combining two or more sub-parameters with an "OR" clause
    """

    def __init__(self, inverse: bool = False):
        self.inverse = inverse
        super().__init__()

    def query(self) -> Q:
        if not self.child_parameters:
            logger.info('No child parameters found,returning empty set')
            return Card.objects.none()

        q = Q()
        for child in self.child_parameters:
            q.add(child.query(), Q.OR)

        return ~q if self.inverse else q


class CardNameParam(CardSearchParam):
    """
    The parameter for searching by a card's name
    """

    def __init__(self, card_name):
        super().__init__()
        self.card_name = card_name

    def query(self) -> Q:
        return Q(name__icontains=self.card_name)


class CardRulesTextParam(CardSearchParam):
    """
    The parameter for searching by a card's rules text
    """

    def __init__(self, card_rules):
        super().__init__()
        self.card_rules = card_rules

    def query(self) -> Q:
        if '~' not in self.card_rules:
            return Q(rules_text__icontains=self.card_rules)
        chunks = [Value(c) for c in self.card_rules.split('~')]
        params = [F('name')] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        return Q(rules_text__icontains=Concat(*params))


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


class CardColourParam(CardSearchParam):
    """
    The parameter for searching by a card's colour
    """

    def __init__(self, card_colour: Bit):
        super().__init__()
        self.card_colour = card_colour

    def query(self) -> Q:
        return Q(colour_flags=self.card_colour)


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
        return Q(printings__printed_languages__physical_cards__ownerships__owner=self.user)


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


class CardRarityParam(CardSearchParam):
    """
    The parameter for searching by a card's rarity
    """

    def __init__(self, rarity: Rarity):
        super().__init__()
        self.rarity = rarity

    def query(self) -> Q:
        return Q(printings__rarity=self.rarity)


# pylint: disable=abstract-method
class CardNumericalParam(CardSearchParam):
    """
    The base parameter for searching by some numerical value
    """

    def __init__(self, number: int, operator: str):
        super().__init__()
        self.number = number
        self.operator = operator

    def get_args(self, field: str) -> dict:
        return {f'{field}{OPERATOR_MAPPING[self.operator]}': self.number}


class CardNumPowerParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical power
    """

    def __init__(self, num_power: int, comparison: str):
        super().__init__(num_power, comparison)
        self.num_power = num_power
        self.comparison = comparison

    def query(self) -> Q:
        args = self.get_args('num_power')
        return Q(**args)


class CardNumToughnessParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical toughness
    """

    def query(self) -> Q:
        args = self.get_args('num_toughness')
        return Q(**args)


class CardNumLoyaltyParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical loyalty
    """

    def query(self) -> Q:
        args = self.get_args('num_loyalty')
        return Q(**args)


class CardCmcParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical converted mana cost
    """

    def query(self) -> Q:
        args = self.get_args('cmc')
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
                Case(When(printings__printed_languages__physical_cards__ownerships__owner=self.user,
                          then='printings__printed_languages__physical_cards__ownerships__count'),
                     output_field=IntegerField(),
                     default=0
                     )))

        kwargs = {f'ownership_count{OPERATOR_MAPPING[self.operator]}': self.number}
        query = Q(**kwargs)
        return Q(id__in=annotated_result.filter(query))


class CardSortParam:
    """
    The base sorting parameter
    """

    def __init__(self, descending: bool = False):
        super().__init__()
        self.sort_descending = descending

    def get_sort_list(self) -> list:
        return ['-' + arg if self.sort_descending else arg for arg in self.get_sort_keys()]

    def get_sort_keys(self) -> list:
        raise NotImplementedError()


class CardNameSortParam(CardSortParam):
    """
    THe sort parameter for a card's name
    """

    def get_sort_keys(self) -> list:
        return ['name']


class CardCollectorNumSortParam(CardSortParam):
    """
    The sort parameter for a card's collector number
    """

    def get_sort_keys(self) -> list:
        return ['printings__number']


class CardColourSortParam(CardSortParam):
    """
    The sort parameter for a card's colour key
    """

    def get_sort_keys(self) -> list:
        return ['colour_sort_key']


class CardColourWeightSortParam(CardSortParam):
    """
    The sort parameter for a card's colour weight
    """

    def get_sort_keys(self) -> list:
        return ['cmc', 'colour_sort_key', 'colour_weight']
