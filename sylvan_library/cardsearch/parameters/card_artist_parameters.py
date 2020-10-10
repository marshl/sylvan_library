"""
Card artist parameters
"""
from django.db.models.query import Q

from .base_parameters import CardSearchParam


class CardArtistParam(CardSearchParam):
    """
    The parameter for searching by a card printings artist
    """

    def __init__(self, artist: str):
        super().__init__()
        self.artist = artist

    def query(self) -> Q:
        return Q(artist__icontains=self.artist)

    def get_pretty_str(self) -> str:
        return "artist " + ("isn't" if self.negated else "is") + " " + self.artist
