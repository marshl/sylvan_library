"""
Card serializers
"""

from rest_framework import serializers
from rest_framework.relations import StringRelatedField

from sylvan_library.cards.models.card import (
    Card,
    CardFace,
    CardPrinting,
    Set,
    Rarity,
    CardFacePrinting,
    CardFaceLocalisation,
    CardLocalisation,
)
from sylvan_library.cards.models.card_price import CardPrice
from sylvan_library.cards.models.language import Language


class CardLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = "__all__"


class CardLocalisationSerializer(serializers.ModelSerializer):

    language = CardLanguageSerializer()

    class Meta:
        model = CardLocalisation
        fields = "__all__"


class CardFaceLocalisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardFaceLocalisation
        fields = "__all__"


class CardPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardPrice
        fields = "__all__"


class RaritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Rarity
        fields = "__all__"


class SetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fields = "__all__"


class CardFacePrintingSerializer(serializers.ModelSerializer):
    localised_faces = CardFaceLocalisationSerializer(many=True)

    class Meta:
        model = CardFacePrinting
        fields = "__all__"


class CardPrintingSerializer(serializers.ModelSerializer):
    set = SetSerializer()
    rarity = RaritySerializer()
    latest_price = CardPriceSerializer()
    face_printings = CardFacePrintingSerializer(many=True)
    localisations = CardLocalisationSerializer(many=True)

    class Meta:
        model = CardPrinting
        fields = "__all__"


class CardFaceSerializer(serializers.ModelSerializer):

    types = StringRelatedField(many=True)
    subtypes = StringRelatedField(many=True)
    supertypes = StringRelatedField(many=True)

    class Meta:
        model = CardFace
        fields = "__all__"


class CardSerializer(serializers.ModelSerializer):
    """
    Serialiser for the card object
    """

    faces = CardFaceSerializer(many=True, read_only=True)
    printings = CardPrintingSerializer(many=True, read_only=True)

    class Meta:
        model = Card
        fields = "__all__"
