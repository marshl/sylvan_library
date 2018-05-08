from cardsearch.card_search import CardSearch
from cardsearch.parameters import *


class FieldSearch:

    def __init__(self):
        self.card_name = None
        self.rules_text = None

    def get_query(self):

        searcher = CardSearch()
        root_param = searcher.root_parameter

        if self.card_name is not None:
            root_param.add_parameter(CardNameParam(self.card_name))

        if self.rules_text is not None:
            root_param.add_parameter(CardRulesTextParam(self.rules_text))

        return searcher.result_search()
