from django.db.models import F

from cards.models.card import (
    Card,
    CardFace,
    CardPrinting,
    CardFacePrinting,
    CardLocalisation,
    CardFaceLocalisation,
)
from data_import.staging import StagedSet


class ExistingSetInfo:
    def __init__(self, staged_set: StagedSet):
        self.staged_set = staged_set

        self.cards: dict[str, Card] = {}
        self.card_faces: dict[tuple[str, str], CardFace] = {}
        self.printings: dict[str, CardPrinting] = {}
        self.face_printings: dict[tuple[str, str], CardFacePrinting] = {}
        self.localisations: dict[tuple[str, str], CardLocalisation] = {}
        self.face_localisations: dict[
            tuple[str, str, str | None], CardFaceLocalisation
        ] = {}

    def get_existing_data(self):
        self.cards = {
            card.scryfall_oracle_id: card
            for card in Card.objects.filter(
                scryfall_oracle_id__in=self.staged_set.get_scryfall_oracle_ids()
            )
            .prefetch_related("rulings", "legalities__format")
            .all()
        }

        self.card_faces = {
            (face.scryfall_oracle_id, face.side): face
            for face in CardFace.objects.filter(
                card__scryfall_oracle_id__in=self.cards.keys()
            )
            .annotate(scryfall_oracle_id=F("card__scryfall_oracle_id"))
            .prefetch_related("subtypes", "supertypes", "types")
        }

        self.printings = {
            printing.scryfall_id: printing
            for printing in CardPrinting.objects.filter(
                card__scryfall_oracle_id__in=self.staged_set.get_scryfall_oracle_ids(),
                set__code=self.staged_set.code,
            ).prefetch_related("rarity")
        }

        self.face_printings = {
            (face_printing.scryfall_id, face_printing.face_side): face_printing
            for face_printing in CardFacePrinting.objects.filter(
                card_printing__scryfall_id__in=self.printings.keys()
            )
            .annotate(
                scryfall_id=F("card_printing__scryfall_id"),
                face_side=F("card_face__side"),
            )
            .prefetch_related("frame_effects")
        }

        self.localisations = {
            (localisation.scryfall_id, localisation.language_name): localisation
            for localisation in CardLocalisation.objects.filter(
                card_printing__scryfall_id__in=self.printings.keys()
            ).annotate(
                language_name=F("language__name"),
                scryfall_id=F("card_printing__scryfall_id"),
            )
        }

        self.face_localisations = {
            (
                face_localisation.scryfall_id,
                face_localisation.language_name,
                face_localisation.face_side,
            ): face_localisation
            for face_localisation in CardFaceLocalisation.objects.filter(
                localisation__card_printing__scryfall_id__in=self.printings.keys()
            ).annotate(
                scryfall_id=F("localisation__card_printing__scryfall_id"),
                language_name=F("localisation__language__name"),
                face_side=F("card_printing_face__card_face__side"),
            )
        }

    def get_card(self, scryfall_oracle_id: str) -> Card | None:
        assert scryfall_oracle_id
        return self.cards.get(scryfall_oracle_id)

    def get_card_face(
        self, scryfall_oracle_id: str, side: str | None
    ) -> CardFace | None:
        """
        Gets the existing CardFace for the given oracle ID and side (if it exists)
        :param scryfall_oracle_id: The scryfall oracle ID of the card face to get
        :param side: The face identifier of the CardFace (usually null, otherwise 'a' or 'b')
        :return: The prefetched CardFace object if it exists, otherwise None
        """
        assert scryfall_oracle_id
        return self.card_faces.get((scryfall_oracle_id, side))

    def get_printing(self, scryfall_id: str) -> CardPrinting | None:
        assert scryfall_id
        return self.printings.get(scryfall_id)

    def get_face_printing(
        self, scryfall_id: str, face_side: str | None
    ) -> CardFacePrinting | None:
        assert scryfall_id
        return self.face_printings.get((scryfall_id, face_side))

    def get_localisation(
        self, scryfall_id: str, language_name: str
    ) -> CardLocalisation | None:
        """
        Gets the existing card localisation that matches the given scryfall ID and language name
        :param scryfall_id: The scryfall ID of the localisation's  printing
        :param language_name: The name of the localisation's language
        :return: The localisation (if it exists)
        """
        assert scryfall_id and language_name
        return self.localisations.get((scryfall_id, language_name))

    def get_face_localisation(
        self, scryfall_id: str, language_name: str, face_side: str
    ) -> CardFaceLocalisation | None:
        return self.face_localisations.get((scryfall_id, language_name, face_side))
