"""
Card serializers
"""

from rest_framework import serializers

from cards.models.card import Card


class CardSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serialiser for the card object
    """

    class Meta:
        model = Card
        # fields = ["id", "name", "power", "toughness"]
        fields = "__all__"
