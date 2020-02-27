"""
Base parameters objects and helpers
"""
import logging
from abc import ABC
from functools import reduce
from typing import List, Union, Dict

from django.db.models import F
from django.db.models.query import Q

from cards.models import Card

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


def or_group_queries(q_objects: List[Q]) -> Q:
    """
    Groups a list of Q query objects into an or group
    :param q_objects: The Q objects to group
    :return: The grouped queries
    """
    if not q_objects:
        return Q()
    return reduce(lambda a, b: a | b, q_objects)


def and_group_queries(q_objects: List[Q]) -> Q:
    """
    Groups a list of Q query objects into an and group
    :param q_objects: The Q objects to group
    :return: The grouped queries
    """
    if not q_objects:
        return Q()
    return reduce(lambda a, b: a & b, q_objects)


def validate_colour_flags(colours: int) -> None:
    """
    Validates that the given colour flags do exist
    :param colours: The colours to validate
    """
    assert colours >= 0
    assert colours <= (
        Card.colour_flags.white
        | Card.colour_flags.blue
        | Card.colour_flags.black
        | Card.colour_flags.red
        | Card.colour_flags.green
    )


class CardSearchParam:
    """
    The base search parameter class
    """

    def __init__(self) -> None:
        self.negated: bool = False

    def query(self) -> Q:
        """
        Returns the query of this parameter and all child parameters
        :return:
        """
        raise NotImplementedError("Please implement this method")

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        raise NotImplementedError(
            "Please implement get_pretty_str on " + type(self).__name__
        )


class BranchParam(CardSearchParam):
    # pylint: disable=abstract-method
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

    def query(self) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found, returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            query.add(child.query(), Q.AND)

        if self.negated:
            return ~query
        return query

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str()
        result = " and ".join(
            "(" + param.get_pretty_str() + ")"
            if isinstance(param, OrParam) and len(param.child_parameters) > 1
            else param.get_pretty_str()
            for param in self.child_parameters
        )

        return result


class OrParam(BranchParam):
    """
    The class for combining two or more sub-parameters with an "OR" clause
    """

    def query(self) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found,returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            query |= child.query()

        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str()

        return " or ".join(param.get_pretty_str() for param in self.child_parameters)


class CardNumericalParam(CardSearchParam, ABC):
    # pylint: disable=abstract-method
    """
    The base parameter for searching by some numerical value
    """

    def __init__(self, number: Union[float, F], operator: str):
        super().__init__()
        self.number = number
        self.operator = operator

    def get_args(self, field: str) -> Dict[str, Union[float, F]]:
        """
        Shortcut to generate the Q object parameters for the given field
        :param field: The card field to compare with
        :return:
        """
        django_op = OPERATOR_MAPPING[self.operator]
        return {field + django_op: self.number}
