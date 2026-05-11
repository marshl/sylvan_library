"""
Views
"""

from rest_framework import viewsets

from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.decks import Deck
from sylvan_library.cards.models.sets import Set
from sylvan_library.cards.serializers import (
    CardSerializer,
    SetSerializer,
    DeckSerializer,
)


# pylint: disable=too-many-ancestors
class CardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = (
        Card.objects.all()
        .prefetch_related(
            "printings__rarity",
            "printings__localisations__ownerships",
            "printings__localisations__language",
            "printings__localisations__localised_faces__image",
            "printings__face_printings__localised_faces__image",
            "printings__face_printings__localised_faces__localisation",
            "printings__set",
            "printings__rarity",
            "faces",
        )
        .order_by("id")
    )

    serializer_class = CardSerializer


class SetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Set model
    """

    queryset = Set.objects.filter().order_by("-release_date")
    serializer_class = SetSerializer


class AllSetsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ALL sets, grouped by parent set
    """

    queryset = (
        Set.objects.filter(parent_set__isnull=True)
        .prefetch_related("child_sets__child_sets__child_sets")
        .order_by("-release_date")
    )
    serializer_class = SetSerializer
    pagination_class = None


class DeckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for decks
    """

    queryset = Deck.objects.all().order_by("-last_modified")
    serializer_class = DeckSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user:
            return queryset.filter(owner=self.request.user)
        return queryset
