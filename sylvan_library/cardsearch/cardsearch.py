from django.db import models
from django.db.models.query import Q, QuerySet
from django.contrib.auth.models import User

import operator
from functools import reduce

from cards.models import *


class SearchParameterNode:
    def __init__(self):
        self.child_parameters = list()
        self.boolean_flag = True

    def get_filters_r(self):
        return self.get_filter()

    def get_filter(self):
        raise NotImplementedError('Please implement this method')

    def get_boolean_filter(self):
        return self.get_filter() if self.boolean_flag else ~self.get_filter()

    def get_result(self):
        raise NotImplementedError('Please implement this method')

    def __str__(self):
        return '!'


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

    def get_filter(self):
        filters = [x.get_boolean_filter() for x in self.child_parameters]
        if not filters:
            return None

        result = filters[0]
        for f in filters:
            result &= f
        return result
        # return reduce(operator.and_, filters, Q())

    def __str__(self):
        return 'AND (' + ', '.join(self.child_parameters) + ')'

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

    def get_filter(self):
        filters = [x.get_boolean_filter() for x in self.child_parameters]
        if not filters:
            return None

        result = filters[0]
        for f in filters:
            result |= f
        return result

        # return reduce(operator.or_, filters, Q())

    def __str__(self):
        return 'OR (' + ', '.join(self.child_parameters) + ')'

    def get_result(self):
        result = Card.objects.none()
        for child in self.child_parameters:
            result = result.union(child.get_result())

        if not self.boolean_flag:
            result = Card.objects.all().difference(result)

        return result


class RootSearchParameter(SearchParameterNode):
    def __init__(self):
        super().__init__()

    def apply_filter(self, base_set: QuerySet):
        pass


class CardNameSearchParameter(SearchParameterNode):
    def __init__(self, card_name):
        super().__init__()
        self.card_name = card_name

    def apply_filter(self, base_set: QuerySet):
        return base_set.filter(name__icontains=self.card_name)

    def get_filter(self):
        return Q(name__icontains=self.card_name)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(name__icontains=self.card_name)
        else:
            return Card.objects.exclude(name__icontains=self.card_name)


class CardRulesSearchParameter(SearchParameterNode):
    def __init__(self, card_rules):
        super().__init__()
        self.card_rules = card_rules

    def get_filter(self):
        return Q(rules__icontains=self.card_rules)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(rules__icontains=self.card_rules)
        else:
            return Card.objects.exclude(rules__icontains=self.card_rules)


class CardTypeSearchParameter(SearchParameterNode):
    def __init__(self, card_type):
        super().__init__()
        self.card_type = card_type

    def get_filter(self):
        return Q(type__icontains=self.card_type)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(type__icontains=self.card_type)
        else:
            return Card.objects.exclude(type__icontains=self.card_type)


class CardSubtypeParameter(SearchParameterNode):
    def __init__(self, card_subtype):
        super().__init__()
        self.card_subtype = card_subtype

    def get_filter(self):
        return Q(subtype__icontains=self.card_subtype)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(subtype__icontains=self.card_subtype)
        else:
            return Card.objects.exclude(subtype__icontains=self.card_subtype)


class CardColourParameter(SearchParameterNode):
    def __init__(self, card_colour: Colour):
        super().__init__()
        self.card_colour = card_colour

    def get_filter(self):
        return Q(colours=self.card_colour)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(colours=self.card_colour)
        else:
            return Card.objects.exclude(colours=self.card_colour)


class CardMulticolouredOnlyParameter(SearchParameterNode):
    def __init__(self):
        super().__init__()

    def get_filter(self):
        return Q(caolour_count__gt=1)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(colour_count__gt=1)
        else:
            return Card.objects.filter(colour_count__lte=1)


class CardSetParameter(SearchParameterNode):
    def __init__(self, set_obj: Set):
        super().__init__()
        self.set_obj = set_obj

    def get_filter(self):
        return Q(printings__set=self.set_obj)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(printings__set=self.set_obj)
        else:
            return Card.objects.exclude(printings__set=self.set_obj)


class CardOwnerParameter(SearchParameterNode):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def get_filter(self):
        return Q(printings__printed_languages__physical_cards__ownerships__owner=self.user)

    def get_result(self):
        if self.boolean_flag:
            return Card.objects.filter(printings__printed_languages__physical_cards__ownerships__owner=self.user)
        else:
            return Card.objects.exclude(printings__printed_languages__physical_cards__ownerships__owner=self.user)


class CardSearch:
    def __init__(self):
        self.root_parameter = AndParameterNode()
        self.parameter_list = list()

    def add_parameter(self, param):
        self.parameter_list.append(param)

    def get_base_result_set(self):
        return Card.objects.all()

    def search(self):
        base_set = self.get_base_result_set()
        for param in self.parameter_list:
            base_set = param.apply_filter(base_set)

        return base_set

    def q_search(self):
        query = self.parameter_list[0].create_q()
        for param in self.parameter_list[1:]:
            query &= param.create_q()

        return Card.objects.filter(query)

    def tree_search(self):
        filters = self.root_parameter.get_boolean_filter()
        print(filters)
        return Card.objects.filter(filters)

    def result_search(self):
        return self.root_parameter.get_result()
