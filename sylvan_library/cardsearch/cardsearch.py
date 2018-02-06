from django.db import models
from django.db.models.query import Q, QuerySet

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


class BranchParameterNode(SearchParameterNode):
    def __init__(self):
        super().__init__()
        self.child_parameters = list()

    def add_parameter(self, param: SearchParameterNode):
        self.child_parameters.append(param)


class AndParameterNode(BranchParameterNode):
    def __init__(self):
        super().__init__()

    def get_filter(self):
        if len(self.child_parameters) == 0:
            return None

        result = self.child_parameters[0].get_boolean_filter()
        for child in self.child_parameters[1:]:
            result &= child.get_boolean_filter()

        return result


class OrParameterNode(BranchParameterNode):
    def __init__(self):
        super().__init__()

    def get_filter(self):
        if len(self.child_parameters) == 0:
            return None

        result = self.child_parameters[0].get_boolean_filter()
        for child in self.child_parameters[1:]:
            result |= child.get_boolean_filter()
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
        return base_set.filter(name__contains=self.card_name)

    def get_filter(self):
        return Q(name__contains=self.card_name)


class CardSearch:
    def __init__(self):
        self.root_parameter = RootSearchParameter()
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
        return Card.objects.filter(self.root_parameter.get_boolean_filter())
