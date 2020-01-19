from base_search import BaseSearch
from cardsearch.parser import CardQueryParser, ParseError

from django.contrib.auth.models import User


class ParseSearch(BaseSearch):
    def __init__(self, user: User = None):
        super().__init__()
        self.query_string = None
        self.error_message = None
        self.user = user

    def get_preferred_set(self):
        return None

    def build_parameters(self):
        if not self.query_string:
            return

        query_parser = CardQueryParser(self.user)
        try:
            self.root_parameter = query_parser.parse(self.query_string)
            print(self.root_parameter.query())
        except (ParseError, ValueError) as error:
            self.error_message = str(error)
