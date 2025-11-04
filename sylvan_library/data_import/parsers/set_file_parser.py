from data_import.parsers.parse_counter import ParseCounter
from data_import.parsers.existing_set_info import ExistingSetInfo
from data_import.parsers.set_parser import SetParser
from data_import.staging import StagedSet


class SetFileParser:
    def __init__(self, set_data: dict, parse_counter: ParseCounter | None = None):
        self.set_data = set_data
        self.parse_counter = parse_counter

    def get_staged_sets(self) -> list[StagedSet]:
        result = [StagedSet(self.set_data, for_token=False)]

        # If the set has tokens, and isn't a dedicated token set, then create a separate set just
        # for the tokens of that set
        if (
            self.set_data.get("tokens")
            and self.set_data.get("cards")
            and self.set_data.get("type") != "token"
        ):
            result.append(StagedSet(self.set_data, for_token=True))

        return result

    def parse_set_file(self):
        """
        Parses a set dict and checks for updates/creates/deletes to be done
        """
        for staged_set in self.get_staged_sets():
            existing_set = ExistingSetInfo(staged_set=staged_set)
            existing_set.get_existing_data()
            set_parser = SetParser(
                staged_set=staged_set,
                parse_counter=self.parse_counter,
                existing_set=existing_set,
            )
            set_parser.parse_set_data()
            set_parser.bulk_create_updates()
