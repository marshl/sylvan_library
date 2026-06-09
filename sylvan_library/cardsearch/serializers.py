"""
Serializers for cardsearch
"""
from rest_framework import serializers

from sylvan_library.cards.serializers import CardSerializer, CardPrintingSerializer


class SearchResultSerializer(serializers.Serializer):
    """
    Serializer for a single search result
    """

    card = CardSerializer()
    selected_printing = CardPrintingSerializer()
