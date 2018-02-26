from cardsearch import cardsearch
from cards.models import Colour


class SimpleSearch:

    def __init__(self):
        self.text = None
        self.colours = list()
        self.include_name = False
        self.include_types = False
        self.include_rules = False
        self.set = None
        self.format = None
        self.match_colours = False
        self.multicoloured_only = False
        self.exclude_colours = False
        self.card_type = False
        self.sort_order = None

    def get_query(self):

        searcher = cardsearch.CardSearch()
        root_param = searcher.root_parameter

        if self.text:
            text_root = root_param.add_parameter(cardsearch.OrParameterNode())
            if self.include_name:
                text_root.add_parameter(cardsearch.CardNameSearchParam(self.text))

            if self.include_rules:
                text_root.add_parameter(cardsearch.CardRulesSearchParam(self.text))

            if self.include_types:
                text_root.add_parameter(cardsearch.CardTypeSearchParameter(self.text))
                text_root.add_parameter(cardsearch.CardSubtypeParam(self.text))

        if self.colours:
            param = cardsearch.AndParameterNode() if self.match_colours else cardsearch.OrParameterNode()
            root_param.add_parameter(param)

            for colour in self.colours:
                param.add_parameter(cardsearch.CardColourParam(colour))

            if self.exclude_colours:
                for colour in [c for c in Colour.objects.all() if c not in self.colours]:
                    p = cardsearch.CardColourParam(colour)
                    p.boolean_flag = False
                    root_param.add_parameter(p)

        if self.set:
            root_param.add_parameter(cardsearch.CardSetParam(self.set))

        if self.multicoloured_only:
            root_param.add_parameter(cardsearch.CardMulticolouredOnlyParam())

        if self.card_type:
            root_param.add_parameter(cardsearch.CardTypeSearchParameter(self.card_type))

        return searcher.result_search()
