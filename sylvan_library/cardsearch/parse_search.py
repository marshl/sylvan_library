"""
Module for the ParseSearch
"""

from typing import Optional

from django.contrib.auth import get_user_model

from cards.models.sets import Set
from cardsearch.base_search import BaseSearch
from cardsearch.parameters.base_parameters import CardSearchBranchNode
from cardsearch.parameters.card_set_parameters import CardSetParam
from cardsearch.parser.base_parser import ParseError
from cardsearch.parser.query_parser import CardQueryParser


class ParseSearch(BaseSearch):
    """
    Search that consumes a query string
    """

    def __init__(self, user: get_user_model(), query_string: str):
        super().__init__(user)
        self.query_string: str = query_string
        self.error_message: Optional[str] = None

    def get_preferred_set(self) -> Optional[Set]:
        """
        Gets the preferred set of this search
        :return:
        """
        if not self.root_parameter:
            return None

        if isinstance(self.root_parameter, CardSetParam):
            return self.root_parameter.set_obj

        if isinstance(self.root_parameter, CardSearchBranchNode):
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

        query_parser = CardQueryParser()
        try:
            self.root_parameter = query_parser.parse(self.query_string)
            self.sort_params = self.root_parameter.get_sort_parameters()
        except (ParseError, ValueError) as error:
            self.error_message = str(error)
