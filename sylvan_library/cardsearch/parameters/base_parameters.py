"""
Base parameters objects and helpers
"""

import dataclasses
import math
from abc import abstractmethod, ABCMeta
import enum
import logging
from abc import ABC
from functools import reduce
from typing import List, Union, Dict, Optional

from django.contrib.auth import get_user_model
from django.db.models import F, OrderBy
from django.db.models.query import Q

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

OPERATOR_TO_WORDY_MAPPING = {
    "<": "less than",
    "<=": "less than or equal to",
    ">": "greater than",
    ">=": "greater than or equal to",
    "=": "equal to",
    ":": "equal to",
    "LT": "less than",
    "LTE": "less than or equal to",
    "GT": "greater than",
    "GTE": "greater than or equal to",
    "EQ": "equal to",
}


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


class CardSearchContext(enum.Enum):
    """
    Different search modes (the model "origin" of the search, for example card, card printing)
    """

    CARD = "CARD"
    PRINTING = "PRINTING"


@dataclasses.dataclass
class ParameterArgs:
    """
    Argument container for all parameter parser functions
    """

    keyword: str
    operator: str
    value: str
    is_regex: bool = False


class QueryValidationError(Exception):
    """
    An error that occurs when calling validate() on a
    parameter
    """


@dataclasses.dataclass
class QueryContext:
    user: Optional[get_user_model()]
    search_mode: Optional[CardSearchContext]


class CardSearchTreeNode(ABC):
    """
    The base search parameter class
    """

    def __init__(self, negated: bool = False):
        self.negated = negated

    @abstractmethod
    def query(self, query_context: QueryContext) -> Q:
        """
        Returns the query of this parameter and all child parameters
        :return:
        """
        raise NotImplementedError

    def validate(self, query_context: QueryContext) -> None:
        pass

    @abstractmethod
    def get_default_search_context(self) -> CardSearchContext:
        raise NotImplementedError

    @abstractmethod
    def get_pretty_str(self, query_context: QueryContext) -> Optional[str]:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        raise NotImplementedError(
            f"Please implement get_pretty_str on {type(self).__name__}"
        )

    def get_sort_parameters(self):
        return []


class CardSearchParameter(CardSearchTreeNode, ABC):
    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(negated)
        self.operator = param_args.operator
        self.value = param_args.value.lower()
        self.is_regex = param_args.is_regex

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        return param_args.keyword.lower() in cls.get_search_keywords()

    @classmethod
    @abstractmethod
    def get_parameter_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_search_operators(cls) -> List[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_search_keywords(cls) -> List[str]:
        raise NotImplementedError

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        if self.operator not in self.get_search_operators():
            raise QueryValidationError(
                f'Can\'t use operator "{self.operator}" for {self.get_parameter_name()} parameter'
            )


class CardSortParam(CardSearchParameter, metaclass=ABCMeta):
    """
    The base sorting parameter
    """

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", ">", "<"]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["order", "sort"]

    @classmethod
    @abstractmethod
    def get_sort_keywords(cls) -> List[str]:
        raise NotImplementedError

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        if not super().matches_param_args(param_args):
            return False

        return param_args.value in cls.get_sort_keywords()

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        if param_args.operator == "<":
            self.negated = True

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def get_pretty_str(self, query_context: QueryContext) -> Optional[str]:
        return None

    def query(self, query_context: QueryContext) -> Q:
        return Q()

    def get_sort_list(self, search_context: CardSearchContext) -> List[OrderBy]:
        """
        Gets the sort list taking order into account
        :return:
        """
        sort_keys = self.get_sort_keys(search_context)

        return [
            OrderBy(
                F(key.strip("-")),
                descending=bool(self.negated) != bool(key.startswith("-")),
                nulls_last=True,
            )
            for key in sort_keys
        ]

    @abstractmethod
    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        """
        Gets the list of attributes to be sorted by
        :return:
        """
        raise NotImplementedError()


class CardSearchBranchNode(CardSearchTreeNode, ABC):
    """
    The base branching parameter class (subclassed to "and" and "or" parameters)
    """

    def __init__(self, negated: bool = False):
        super().__init__(negated)
        self.child_parameters: List[CardSearchTreeNode] = []

    def add_parameter(self, param: CardSearchTreeNode) -> CardSearchTreeNode:
        """
        Adds a child parameter to this node
        :param param: The child to add
        :return:
        """
        self.child_parameters.append(param)
        return param

    def get_default_search_context(self) -> CardSearchContext:
        for child in self.child_parameters:
            if child.get_default_search_context() == CardSearchContext.PRINTING:
                return CardSearchContext.PRINTING

        return CardSearchContext.CARD

    def validate(self, query_context: QueryContext) -> None:
        for child in self.child_parameters:
            child.validate(query_context)

    def get_sort_parameters(self) -> List[CardSortParam]:
        sort_params = []
        for child in self.child_parameters:
            if isinstance(child, CardSearchBranchNode):
                sort_params += child.get_sort_parameters()
            elif isinstance(child, CardSortParam):
                sort_params.append(child)
        return sort_params


class CardSearchAnd(CardSearchBranchNode):
    """
    The class for combining two or more sub-parameters with an "AND" clause
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "and"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return []

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return []

    def query(self, query_context: QueryContext) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found, returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            if isinstance(child, CardSearchTreeNode):
                query.add(child.query(query_context), Q.AND)

        if self.negated:
            return ~query
        return query

    def get_pretty_str(self, query_context: QueryContext) -> Optional[str]:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str(query_context)

        parts = []
        for param in self.child_parameters:
            string = param.get_pretty_str(query_context)
            if string is not None:
                if isinstance(param, CardSearchOr) and len(param.child_parameters) > 1:
                    parts.append(f"({string})")
                else:
                    parts.append(string)

        return " and ".join(parts) if parts else None


class CardSearchOr(CardSearchBranchNode):
    """
    The class for combining two or more sub-parameters with an "OR" clause
    """

    def query(self, query_context: QueryContext) -> Q:
        if not self.child_parameters:
            logger.info("No child parameters found,returning empty set")
            return Q()

        query = Q()
        for child in self.child_parameters:
            query |= child.query(query_context)

        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> Optional[str]:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if len(self.child_parameters) == 1:
            return self.child_parameters[0].get_pretty_str(query_context)

        parts = []
        for param in self.child_parameters:
            string = param.get_pretty_str(query_context)
            if string is not None:
                parts.append(string)

        return " or ".join(parts) if parts else None


class CardSearchNumericalParameter(CardSearchParameter, ABC):
    """
    The base parameter for searching by some numerical value
    """

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.number = None

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return ["<", "<=", ":", "=", ">", ">="]

    def get_args(
        self, field: str, query_context: QueryContext
    ) -> Dict[str, Union[float, F]]:
        """
        Shortcut to generate the Q object parameters for the given field
        :param field: The card field to compare with
        :return:
        """
        django_op = OPERATOR_MAPPING[self.operator]
        return {field + django_op: self.get_search_value(query_context)}

    def validate(self, query_context: QueryContext) -> None:
        super().validate(query_context)
        if self.number is None:
            self.number = self.get_search_value(query_context)

    def get_search_value(self, query_context: QueryContext) -> Union[float, F]:
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        if self.value in ("toughness", "tough", "tou"):
            return F(f"{prefix}faces__num_toughness")

        if self.value in ("power", "pow"):
            return F(f"{prefix}faces__num_power")

        if self.value in ("loyalty", "loy"):
            return F(f"{prefix}faces__num_loyalty")

        if self.value in ("cmc", "cost", "mv", "manavalue"):
            return F(f"{prefix}mana_value")

        if self.value in ("inf", "infinity", "∞"):
            return math.inf

        try:
            return float(self.value)
        except ValueError as ex:
            raise QueryValidationError(
                f"Could not convert {self.value} to number"
            ) from ex


class CardSearchBinaryParameter(CardSearchParameter, ABC):
    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":"]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["is", "has", "not"]

    @classmethod
    @abstractmethod
    def get_is_keywords(cls) -> List[str]:
        raise NotImplementedError

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        if not super().matches_param_args(param_args):
            return False

        return param_args.value.lower() in cls.get_is_keywords()

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        if param_args.keyword == "not":
            self.negated = not self.negated
