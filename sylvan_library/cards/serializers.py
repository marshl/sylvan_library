"""
Card serializers
"""

from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
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
from sylvan_library.cards.models.decks import Deck
from sylvan_library.cards.models.language import Language
from sylvan_library.cards.models.legality import CardLegality


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

    child_sets = SerializerMethodField()

    class Meta:
        model = Set
        fields = "__all__"

    def get_child_sets(self, obj: Set):
        return SetSerializer(obj.child_sets, many=True).data


class CardFacePrintingSerializer(serializers.ModelSerializer):
    localised_faces = CardFaceLocalisationSerializer(many=True)
    image_url = SerializerMethodField()

    class Meta:
        model = CardFacePrinting
        fields = "__all__"

    def get_image_url(self, obj: CardFacePrinting) -> str:
        english_id = Language.english().id
        localised_faces = list(obj.localised_faces.all())
        english = next(
            (lf for lf in localised_faces if lf.localisation.language_id == english_id),
            None,
        )
        path = english.get_image_path() if english else None
        if not path:
            for lf in localised_faces:
                path = lf.get_image_path()
                if path:
                    break
        if not path:
            path = "card_back.jpg"
        return settings.STATIC_URL + path


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


class DeckSerializer(serializers.ModelSerializer):
    """
    Serializer for the Deck object
    """

    class Meta:
        model = Deck
        fields = "__all__"


class CardLegalitySerializer(serializers.ModelSerializer):
    format = serializers.CharField(source="format.name")

    class Meta:
        model = CardLegality
        fields = ("format", "restriction")


class CardPrintingDetailsSerializer(serializers.ModelSerializer):
    """
    Payload for the search-result "Details" tab.  Mirrors
    website/results/search_result_details.html.
    """

    flavour_text = SerializerMethodField()
    artist = SerializerMethodField()
    set = SerializerMethodField()
    legalities = SerializerMethodField()

    class Meta:
        model = CardPrinting
        fields = ("id", "number", "flavour_text", "artist", "set", "legalities")

    def _first_face(self, obj: CardPrinting) -> CardFacePrinting | None:
        return obj.face_printings.first()

    def get_flavour_text(self, obj: CardPrinting) -> str | None:
        face = self._first_face(obj)
        return face.flavour_text if face else None

    def get_artist(self, obj: CardPrinting) -> str | None:
        face = self._first_face(obj)
        return face.artist if face else None

    def get_set(self, obj: CardPrinting) -> dict:
        return {
            "code": obj.set.code,
            "name": obj.set.name,
            "release_date": obj.set.release_date,
            "total_set_size": obj.set.total_set_size,
        }

    def get_legalities(self, obj: CardPrinting) -> list:
        legalities = obj.card.legalities.select_related("format").order_by(
            "format__name"
        )
        return CardLegalitySerializer(legalities, many=True).data
