"""
Views
"""

from rest_framework import viewsets

from sylvan_library.cards.models.card import Card
from sylvan_library.cards.serializers import CardSerializer


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
