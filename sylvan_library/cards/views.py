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

    queryset = Card.objects.all()
    serializer_class = CardSerializer
    # permission_classes = [permissions.IsAuthenticated]
