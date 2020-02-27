"""
Module for the ParseSearch
"""
from typing import Optional

from django.contrib.auth.models import User

from cards.models import Set
from cardsearch.base_search import BaseSearch
from cardsearch.parameters import CardSetParam, BranchParam
from cardsearch.parser import CardQueryParser, ParseError


class ParseSearch(BaseSearch):
    """
    Search that consumes a query string
    """

    def __init__(self, user: User = None):
        super().__init__()
        self.query_string: Optional[str] = None
        self.error_message: Optional[str] = None
        self.user: User = user

    def get_preferred_set(self) -> Optional[Set]:
        """
        Gets the preferred set of this search
        :return:
        """
        if not self.root_parameter:
            return None

        if isinstance(self.root_parameter, CardSetParam):
            return self.root_parameter.set_obj

        if isinstance(self.root_parameter, BranchParam):
            for child in self.root_parameter.child_parameters:
                if isinstance(child, CardSetParam):
                    return child.set_obj
        return None

    def build_parameters(self) -> None:
        """
        Builds the root parameter object using the query string
        """
        if not self.query_string:
            return

        query_parser = CardQueryParser(self.user)
        try:
            self.root_parameter = query_parser.parse(self.query_string)
            print(self.root_parameter.query())
        except (ParseError, ValueError) as error:
            self.error_message = str(error)
