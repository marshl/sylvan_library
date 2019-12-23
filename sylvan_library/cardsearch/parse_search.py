from base_search import BaseSearch
from query_parser import CardQueryParser, ParseError


class ParseSearch(BaseSearch):
    def __init__(self):
        self.query_string = None
        self.error_message = None
        super().__init__()

    def get_preferred_set(self):
        return None

    def build_parameters(self):
        if not self.query_string:
            return

        query_parser = CardQueryParser()
        try:
            self.root_parameter = query_parser.parse(self.query_string)
        except ParseError as error:
            self.error_message = error.msg
