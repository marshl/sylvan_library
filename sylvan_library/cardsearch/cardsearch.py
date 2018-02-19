from django.db import models
from django.db.models.query import Q, QuerySet
from django.contrib.auth.models import User

import operator
from functools import reduce

from cards.models import *

comparisons = {'<': '__lt', '<=': '__lte', '>': '__gt', '>=': '__gte', '=': ''}


class SearchParameterNode:
    def __init__(self):
        self.child_parameters = list()
        self.boolean_flag = True

    def get_result(self):
        raise NotImplementedError('Please implement this method')


class BranchParameterNode(SearchParameterNode):
    def __init__(self):
        super().__init__()
        self.child_parameters = list()

    def add_parameter(self, param: SearchParameterNode):
        self.child_parameters.append(param)
        return param


class AndParameterNode(BranchParameterNode):
    def __init__(self):
        super().__init__()

    def get_result(self):
        result = Card.objects.all()
        for child in self.child_parameters:
            result = result.intersection(child.get_result())

        if not self.boolean_flag:
            result = Card.objects.all().difference(result)

        return result


class OrParameterNode(BranchParameterNode):
    def __init__(self):
        super().__init__()

    def get_result(self):
        result = Card.objects.none()
        for child in self.child_parameters:
            result = result.union(child.get_result())

        if not self.boolean_flag:
            result = Card.objects.all().difference(result)

        return result


class CardNameSearchParameter(SearchParameterNode):
    def __init__(self, card_name):
        super().__init__()
        self.card_name = card_name

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(name__icontains=self.card_name)
        else:
            return Card.objects.exclude(name__icontains=self.card_name)


class CardRulesSearchParameter(SearchParameterNode):
    def __init__(self, card_rules):
        super().__init__()
        self.card_rules = card_rules

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(rules__icontains=self.card_rules)
        else:
            return Card.objects.exclude(rules__icontains=self.card_rules)


class CardTypeParameter(SearchParameterNode):
    def __init__(self, card_type):
        super().__init__()
        self.card_type = card_type

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(type__icontains=self.card_type)
        else:
            return Card.objects.exclude(type__icontains=self.card_type)


class CardSubtypeParameter(SearchParameterNode):
    def __init__(self, card_subtype):
        super().__init__()
        self.card_subtype = card_subtype

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(subtype__icontains=self.card_subtype)
        else:
            return Card.objects.exclude(subtype__icontains=self.card_subtype)


class CardColourParameter(SearchParameterNode):
    def __init__(self, card_colour: Colour):
        super().__init__()
        self.card_colour = card_colour

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(colour_flags=self.card_colour)
        else:
            return Card.objects.exclude(colour_flags=self.card_colour)


class CardMulticolouredOnlyParameter(SearchParameterNode):
    def __init__(self):
        super().__init__()

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(colour_count__gt=1)
        else:
            return Card.objects.filter(colour_count__lte=1)


class CardSetParameter(SearchParameterNode):
    def __init__(self, set_obj: Set):
        super().__init__()
        self.set_obj = set_obj

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(printings__set=self.set_obj)
        else:
            return Card.objects.exclude(printings__set=self.set_obj)


class CardOwnerParameter(SearchParameterNode):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(printings__printed_languages__physical_cards__ownerships__owner=self.user)
        else:
            return Card.objects.exclude(printings__printed_languages__physical_cards__ownerships__owner=self.user)


class CardNumericalParameter(SearchParameterNode):

    def __init__(self, number: int, operator: str):
        super().__init__()
        self.number = number
        self.operator = operator

    def get_args(self, field: str):
        return {f'{field}{comparisons[self.operator]}': self.number}


class CardNumPowerParameter(CardNumericalParameter):
    def __init__(self, num_power: int, comparison: str):
        super().__init__(num_power, comparison)
        self.num_power = num_power
        self.comparison = comparison

    def get_result(self):

        args = self.get_args('num_power')

        if self.boolean_flag:
            return Card.objects.filter(**args)
        else:
            return Card.objects.exlcude(**args)


class CardNumToughnessParameter(CardNumericalParameter):
    def __init__(self, num_toughness: int, operator: str):
        super().__init__(num_toughness, operator)

    def get_result(self):
        args = self.get_args('num_toughness')
        if self.boolean_flag:
            return Card.objects.filter(**args)
        else:
            return Card.objects.exclude(**args)


class CardNumLoyaltyParameter(CardNumericalParameter):
    def __init__(self, number: int, operator: str):
        super().__init__(number, operator)

    def get_result(self):
        args = self.get_args('num_loyalty')
        if self.boolean_flag:
            return Card.objects.filter(**args)
        else:
            return Card.objects.exclude(**args)


class CardCmcParameter(CardNumericalParameter):
    def __init__(self, number: int, operator: str):
        super().__init__(number, operator)

    def get_result(self):
        args = self.get_args('cmc')
        if self.boolean_flag:
            return Card.objects.filter(**args)
        else:
            return Card.objects.exclude(**args)


class CardSearch:
    def __init__(self):
        self.root_parameter = AndParameterNode()

    def result_search(self):
        return self.root_parameter.get_result()
