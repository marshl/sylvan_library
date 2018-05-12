from cardsearch.card_search import CardSearch
from cardsearch.parameters import *

import logging

logger = logging.getLogger('django')


class FieldSearch:

    def __init__(self):
        self.card_name = None
        self.rules_text = None
        self.cmc = None
        self.cmc_operator = None
        self.white = False
        self.blue = False
        self.black = False
        self.red = False
        self.green = False

    def get_query(self):

        searcher = CardSearch()
        root_param = searcher.root_parameter

        if self.card_name:
            logger.info(f'Searching for card name {self.card_name}')
            root_param.add_parameter(CardNameParam(self.card_name))

        if self.rules_text:
            logger.info(f'Searching for rules text {self.rules_text}')
            root_param.add_parameter(CardRulesTextParam(self.rules_text))

        if self.cmc is not None:
            logger.info(f'Searching for CMC {self.cmc}/{self.cmc_operator}')
            root_param.add_parameter(CardCmcParam(self.cmc, self.cmc_operator))

        if self.white:
            root_param.add_parameter(CardColourParam(Card.colour_flags.white))

        if self.blue:
            root_param.add_parameter(CardColourParam(Card.colour_flags.blue))

        if self.black:
            root_param.add_parameter(CardColourParam(Card.colour_flags.black))

        if self.red:
            root_param.add_parameter(CardColourParam(Card.colour_flags.red))

        if self.green:
            root_param.add_parameter(CardColourParam(Card.colour_flags.green))

        return searcher.result_search()
