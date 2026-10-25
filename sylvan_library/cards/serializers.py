"""
Card serializers
"""

from datetime import date

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.staticfiles import finders
from django.db.models import Prefetch, Q, Sum
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
)
from sylvan_library.cards.models.language import Language
from sylvan_library.cards.models.legality import CardLegality


class RaritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Rarity
        fields = ("id", "name", "symbol")


class PrintingSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fields = ("id", "name", "code")


class SetSerializer(serializers.ModelSerializer):

    child_sets = SerializerMethodField()

    class Meta:
        model = Set
        fields = "__all__"

    def get_child_sets(self, obj: Set):
        return SetSerializer(obj.child_sets, many=True).data


def face_printing_image_url(face_printing: CardFacePrinting) -> str:
    """
    Gets the image URL of a face printing, preferring the English image and falling back
    to the card back if no image file is on disk
    """
    english_id = Language.english().id
    localised_faces = sorted(
        face_printing.localised_faces.all(),
        key=lambda lf: lf.localisation.language_id != english_id,
    )
    for lf in localised_faces:
        path = lf.get_image_path()
        if path and finders.find(path):
            return settings.STATIC_URL + path
    return settings.STATIC_URL + "card_back.jpg"


def printing_image_url(printing: CardPrinting | None) -> str:
    """
    Gets the image URL of the front face of a printing
    """
    face_printing = (
        printing.face_printings.order_by("card_face__side").first()
        if printing
        else None
    )
    if not face_printing:
        return settings.STATIC_URL + "card_back.jpg"
    return face_printing_image_url(face_printing)


def printing_back_image_url(printing: CardPrinting | None) -> str | None:
    """
    Gets the image URL of the back face of a two-faced printing (transform, modal double
    faced etc.), or None if all its faces are on one image (split, adventure etc.) or
    there's no image file for the back
    """
    if not printing:
        return None
    face_printings = list(printing.face_printings.order_by("card_face__side"))
    if len(face_printings) < 2:
        return None
    front = face_printing_image_url(face_printings[0])
    for face_printing in face_printings[1:]:
        url = face_printing_image_url(face_printing)
        if url != front and url != settings.STATIC_URL + "card_back.jpg":
            return url
    return None


class CardFacePrintingSerializer(serializers.ModelSerializer):
    image_url = SerializerMethodField()

    class Meta:
        model = CardFacePrinting
        fields = ("id", "image_url")

    def get_image_url(self, obj: CardFacePrinting) -> str:
        return face_printing_image_url(obj)


def get_context_user(serializer: serializers.Serializer):
    """
    Gets the logged in user from the serializer's request context, if there is one
    """
    request = serializer.context.get("request")
    if request and request.user.is_authenticated:
        return request.user
    return None


class CardPrintingSerializer(serializers.ModelSerializer):
    """
    A printing as shown in a search result. Cards like basic lands have hundreds of
    printings, so this only has what the result needs.
    """

    set = PrintingSetSerializer()
    rarity = RaritySerializer()
    face_printings = CardFacePrintingSerializer(many=True)
    keyrune_code = SerializerMethodField()
    owned_count = SerializerMethodField()

    class Meta:
        model = CardPrinting
        fields = (
            "id",
            "number",
            "set",
            "rarity",
            "keyrune_code",
            "owned_count",
            "face_printings",
        )

    def get_keyrune_code(self, obj: CardPrinting) -> str:
        return obj.get_set_keyrune_code()

    def get_owned_count(self, obj: CardPrinting) -> int | None:
        """
        How many of this printing the user owns, or None for anonymous users
        """
        if not get_context_user(self):
            return None
        return obj.user_owned_count or 0


class CardFaceSerializer(serializers.ModelSerializer):

    types = StringRelatedField(many=True)
    subtypes = StringRelatedField(many=True)
    supertypes = StringRelatedField(many=True)

    class Meta:
        model = CardFace
        fields = "__all__"


def card_prefetches(user: AbstractBaseUser | None) -> list:
    """
    The related objects CardSerializer uses, to prefetch on a list or queryset of cards.
    Cards like basic lands have thousands of localisations, so rather than fetch those,
    each printing gets the user's owned count added up by the database as
    user_owned_count, and only localised faces with a downloaded image are fetched.
    """
    printings = CardPrinting.objects.select_related("set", "rarity")
    if user:
        printings = printings.annotate(
            user_owned_count=Sum(
                "localisations__ownerships__count",
                filter=Q(localisations__ownerships__owner=user),
            )
        )
    faces_with_images = CardFaceLocalisation.objects.filter(
        image__file_path__isnull=False
    ).select_related("image", "localisation")
    return [
        "faces__types",
        "faces__subtypes",
        "faces__supertypes",
        Prefetch("printings", queryset=printings),
        "printings__face_printings",
        Prefetch(
            "printings__face_printings__localised_faces", queryset=faces_with_images
        ),
    ]


class CardSerializer(serializers.ModelSerializer):
    """
    Serialiser for the card object. Prefetch card_prefetches() first.
    """

    faces = CardFaceSerializer(many=True, read_only=True)
    printings = CardPrintingSerializer(many=True, read_only=True)
    owned_count = SerializerMethodField()

    class Meta:
        model = Card
        fields = "__all__"

    def get_owned_count(self, obj: Card) -> int | None:
        """
        How many of this card the user owns across all printings, or None for anonymous users
        """
        if not get_context_user(self):
            return None
        return sum(p.user_owned_count or 0 for p in obj.printings.all())


class CardLegalitySerializer(serializers.ModelSerializer):
    format = serializers.CharField(source="format.name")

    class Meta:
        model = CardLegality
        fields = ("format", "restriction")


class CardPrintingDetailsSerializer(serializers.ModelSerializer):
    """
    Payload for the search-result "Details" tab
    """

    flavour_text = SerializerMethodField()
    artist = SerializerMethodField()
    set = SerializerMethodField()
    release_date = SerializerMethodField()
    legalities = SerializerMethodField()

    class Meta:
        model = CardPrinting
        fields = (
            "id",
            "number",
            "flavour_text",
            "artist",
            "set",
            "release_date",
            "legalities",
        )

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

    def get_release_date(self, obj: CardPrinting) -> date | None:
        return obj.original_release_date or obj.set.release_date

    def get_legalities(self, obj: CardPrinting) -> list:
        legalities = obj.card.legalities.select_related("format").order_by(
            "format__name"
        )
        return CardLegalitySerializer(legalities, many=True).data
