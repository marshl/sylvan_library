"""
Card rarity parameters
"""
from django.db.models.query import Q

from cardsearch.parameters.base_parameters import CardNumericalParam


class CardPriceParam(CardNumericalParam):
    """
    The parameter for searching by how many a user owns of it
    """

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q query object
        """
        args = self.get_args("latest_price__paper_value")
        return Q(**args)

    def get_pretty_str(self) -> str:
        return f"is worth {self.operator} ${self.number}"
