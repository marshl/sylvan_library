from rest_framework import serializers

from cards.models import Card


class CardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Card
        # fields = ["id", "name", "power", "toughness"]
        fields = "__all__"
