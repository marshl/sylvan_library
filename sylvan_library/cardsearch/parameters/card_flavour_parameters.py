from django.db.models import Q

from parameters import CardSearchParam


class CardFlavourTextParam(CardSearchParam):
    """
    Parameter for the printing flavour text
    """

    def __init__(self, flavour_text: str) -> None:
        super().__init__()
        self.flavour_text = flavour_text

    def query(self) -> Q:
        query = Q(flavour_text__icontains=self.flavour_text)
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return (
            "flavour "
            + ("doesn't contain" if self.negated else "contains")
            + f' "{self.flavour_text}"'
        )
