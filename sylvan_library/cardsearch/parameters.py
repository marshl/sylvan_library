from django.db.models.query import Q
from django.db.models import Sum, Case, When, IntegerField
from bitfield.types import Bit

from cards.models import *

comparisons = {'<': '__lt', '<=': '__lte', '>': '__gt', '>=': '__gte', '=': ''}


class CardSearchParam:
    def __init__(self):
        self.child_parameters = list()

    def get_result(self):
        raise NotImplementedError('Please implement this method')


class BranchParam(CardSearchParam):
    def __init__(self):
        super().__init__()
        self.child_parameters = list()

    def add_parameter(self, param: CardSearchParam):
        self.child_parameters.append(param)
        return param


class AndParam(BranchParam):
    def __init__(self):
        super().__init__()

    def get_result(self):
        if not self.child_parameters:
            return Card.objects.none()

        result = self.child_parameters[0].get_result()
        for child in self.child_parameters[1:]:
            result = result.intersection(child.get_result())

        return result


class OrParam(BranchParam):
    def __init__(self):
        super().__init__()

    def get_result(self):
        if not self.child_parameters:
            return Card.objects.none()

        result = self.child_parameters[0].get_result()

        for child in self.child_parameters[1:]:
            result = result.union(child.get_result())

        return result


class NotParam(OrParam):
    def __init__(self):
        super().__init__()

    def get_result(self):
        return Card.objects.difference(super().get_result())


class CardNameParam(CardSearchParam):
    def __init__(self, card_name):
        super().__init__()
        self.card_name = card_name

    def get_result(self):
        return Card.objects.filter(name__icontains=self.card_name)


class CardRulesTextParam(CardSearchParam):
    def __init__(self, card_rules):
        super().__init__()
        self.card_rules = card_rules

    def get_result(self):
        return Card.objects.filter(rules_text__icontains=self.card_rules)


class CardTypeParam(CardSearchParam):
    def __init__(self, card_type):
        super().__init__()
        self.card_type = card_type

    def get_result(self):
        return Card.objects.filter(type__icontains=self.card_type)


class CardSubtypeParam(CardSearchParam):
    def __init__(self, card_subtype):
        super().__init__()
        self.card_subtype = card_subtype

    def get_result(self):
        return Card.objects.filter(subtype__icontains=self.card_subtype)


class CardColourParam(CardSearchParam):
    def __init__(self, card_colour: Bit):
        super().__init__()
        self.card_colour = card_colour

    def get_result(self):
        return Card.objects.filter(colour_flags=self.card_colour)


class CardColourIdentityParam(CardSearchParam):
    def __init__(self, colour_identity: Bit):
        super().__init__()
        self.colour_identity = colour_identity

    def get_result(self):
        return Card.objects.filter(colour_identity_flags=self.colour_identity)


class CardMulticolouredOnlyParam(CardSearchParam):
    def __init__(self):
        super().__init__()

    def get_result(self):
        return Card.objects.filter(colour_count__gt=1)


class CardSetParam(CardSearchParam):
    def __init__(self, set_obj: Set):
        super().__init__()
        self.set_obj = set_obj

    def get_result(self):
        return Card.objects.filter(printings__set=self.set_obj)


class CardBlockParam(CardSearchParam):
    def __init__(self, block_obj: Block):
        super().__init__()
        self.block_obj = block_obj

    def get_result(self):
        return Card.objects.filter(printings__set__block=self.block_obj)


class CardOwnerParam(CardSearchParam):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def get_result(self):
        return Card.objects.filter(printings__printed_languages__physical_cards__ownerships__owner=self.user)


class CardManaCostParam(CardSearchParam):
    def __init__(self, cost: str, exact_match: bool):
        super().__init__()
        self.cost = cost
        self.exact_match = exact_match

    def get_result(self):
        q = Q(cost=self.cost) if self.exact_match else Q(cost__icontains=self.cost)

        return Card.objects.filter(q)


class CardRarityParam(CardSearchParam):
    def __init__(self, rarity: Rarity):
        super().__init__()
        self.rarity = rarity

    def get_result(self):
        q = Q(printings__rarity=self.rarity)
        return Card.objects.filter(q)


class CardNumericalParam(CardSearchParam):

    def __init__(self, number: int, operator: str):
        super().__init__()
        self.number = number
        self.operator = operator

    def get_args(self, field: str):
        return {f'{field}{comparisons[self.operator]}': self.number}


class CardNumPowerParam(CardNumericalParam):
    def __init__(self, num_power: int, comparison: str):
        super().__init__(num_power, comparison)
        self.num_power = num_power
        self.comparison = comparison

    def get_result(self):
        args = self.get_args('num_power')
        return Card.objects.filter(**args)


class CardNumToughnessParam(CardNumericalParam):
    def __init__(self, num_toughness: int, operator: str):
        super().__init__(num_toughness, operator)

    def get_result(self):
        args = self.get_args('num_toughness')
        return Card.objects.filter(**args)


class CardNumLoyaltyParam(CardNumericalParam):
    def __init__(self, number: int, operator: str):
        super().__init__(number, operator)

    def get_result(self):
        args = self.get_args('num_loyalty')
        return Card.objects.filter(**args)


class CardCmcParam(CardNumericalParam):
    def __init__(self, number: int, operator: str):
        super().__init__(number, operator)

    def get_result(self):
        args = self.get_args('cmc')
        return Card.objects.filter(**args)


class CardOwnershipCountParam(CardNumericalParam):
    def __init__(self, user: User, operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def get_result(self):
        annotated_result = Card.objects.annotate(
            ownership_count=Sum(
                Case(When(printings__printed_languages__physical_cards__ownerships__owner=self.user,
                          then='printings__printed_languages__physical_cards__ownerships__count'),
                     output_field=IntegerField(),
                     default=0
                     )))

        kwargs = {f'ownership_count{comparisons[self.operator]}': self.number}
        query = Q(**kwargs)
        return Card.objects.filter(id__in=annotated_result.filter(query))


class CardSortParam:
    def __init__(self, descending: bool = False):
        super().__init__()
        self.sort_descending = descending

    def get_sort_list(self):
        return ['-' + arg if self.sort_descending else arg for arg in self.get_sort_keys()]

    def get_sort_keys(self):
        raise NotImplemented()


class CardNameSortParam(CardSortParam):

    def get_sort_keys(self):
        return ['name']


class CardCollectorNumSortParam(CardSortParam):
    def get_sort_keys(self):
        return ['printings__collector_number']


class CardColourSortParam(CardSortParam):
    def get_sort_keys(self):
        return ['colour_sort_key']


class CardColourWeightSortParam(CardSortParam):
    def get_sort_keys(self):
        return ['cmc', 'colour_sort_key', 'colour_weight']
