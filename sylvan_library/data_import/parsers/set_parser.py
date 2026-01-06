from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.sets import Set, Block
from data_import.models import (
    UpdateSet,
    UpdateBlock,
    UpdateCard,
    UpdateCardFace,
    UpdateCardPrinting,
    UpdateCardFacePrinting,
    UpdateCardLocalisation,
    UpdateCardFaceLocalisation,
    UpdateCardRuling,
    UpdateCardLegality,
    UpdateMode,
)
from data_import.parsers.existing_set_info import ExistingSetInfo
from data_import.parsers.parse_counter import ParseCounter
from data_import.staging import (
    StagedSet,
    StagedCard,
    StagedCardFace,
    StagedCardPrinting,
    StagedCardFacePrinting,
    StagedCardFaceLocalisation,
    StagedCardLocalisation,
)


class SetParser:
    def __init__(
        self,
        staged_set: StagedSet,
        parse_counter: ParseCounter,
        existing_set: ExistingSetInfo,
    ):
        self.staged_set = staged_set
        self.parse_counter = parse_counter
        self.existing_set = existing_set

        self.sets_to_update: list[UpdateSet] = []
        self.blocks_to_update: list[UpdateBlock] = []
        self.cards_to_update: list[UpdateCard] = []
        self.card_faces_to_update: list[UpdateCardFace] = []
        self.printings_to_update: list[UpdateCardPrinting] = []
        self.face_printings_to_update: list[UpdateCardFacePrinting] = []
        self.localisations_to_update: list[UpdateCardLocalisation] = []
        self.face_localisations_to_update: list[UpdateCardFaceLocalisation] = []
        self.rulings_to_update: list[UpdateCardRuling] = []
        self.legalities_to_update: list[UpdateCardLegality] = []

    def bulk_create_updates(self):
        UpdateSet.objects.bulk_create(self.sets_to_update)
        UpdateBlock.objects.bulk_create(self.blocks_to_update)
        UpdateCard.objects.bulk_create(self.cards_to_update)
        UpdateCardFace.objects.bulk_create(self.card_faces_to_update)
        UpdateCardPrinting.objects.bulk_create(self.printings_to_update)
        UpdateCardFacePrinting.objects.bulk_create(self.face_printings_to_update)
        UpdateCardLocalisation.objects.bulk_create(self.localisations_to_update)
        UpdateCardFaceLocalisation.objects.bulk_create(
            self.face_localisations_to_update
        )
        UpdateCardRuling.objects.bulk_create(self.rulings_to_update)
        UpdateCardLegality.objects.bulk_create(self.legalities_to_update)

    def parse_set_data(self):
        """
        Parses a set dict and checks for updates/creates/deletes to be done
        """
        if Set.objects.filter(code=self.staged_set.code).exists():
            existing_set = Set.objects.get(code=self.staged_set.code)
            set_differences = self.staged_set.compare_with_set(existing_set)
            if set_differences:
                self.sets_to_update.append(
                    UpdateSet(
                        update_mode=UpdateMode.UPDATE,
                        set_code=self.staged_set.code,
                        field_data=set_differences,
                    )
                )

        elif not UpdateSet.objects.filter(set_code=self.staged_set.code).exists():
            self.sets_to_update.append(
                UpdateSet(
                    update_mode=UpdateMode.CREATE,
                    set_code=self.staged_set.code,
                    field_data=self.staged_set.get_field_data(),
                )
            )

        if (
            self.staged_set.block_name
            and not Block.objects.filter(name=self.staged_set.block_name).exists()
        ):
            try:
                existing_block_update = UpdateBlock.objects.get(
                    name=self.staged_set.block_name
                )
                if existing_block_update.release_date > self.staged_set.release_date:
                    existing_block_update.release_date = self.staged_set.release_date
                    existing_block_update.save()
            except UpdateBlock.DoesNotExist:
                self.blocks_to_update.append(
                    UpdateBlock(
                        update_mode=UpdateMode.CREATE,
                        name=self.staged_set.block_name,
                        release_date=self.staged_set.release_date,
                    )
                )

        self.process_set_cards()

    def process_set_cards(self) -> None:
        """
        Processes the cards within a set dictionary
        """

        for card_data in self.staged_set.get_cards():
            self.process_all_card_data(card_data)

    def process_all_card_data(self, card_data: dict):
        staged_card = StagedCard(card_data, is_token=self.staged_set.is_token_set)
        staged_card_face = StagedCardFace(card_data)
        staged_card_printing = StagedCardPrinting(card_data, self.staged_set.code)
        staged_face_printing = StagedCardFacePrinting(card_data)

        if (
            not staged_card.scryfall_oracle_id
            # Skip reversible cards like the Transformers version of Doubling Cube
            or staged_card.layout == "reversible_card"
            # Skip punchcards as they aren't properly represented by Scryfall as of writing
            or staged_card_face.name in ("Punchcard", "Ability Punchcard")
        ):
            return

        self.process_card(staged_card)
        self.process_card_faces(staged_card, staged_card_face)

        self.process_card_printing(
            staged_card=staged_card,
            staged_card_face=staged_card_face,
            staged_card_printing=staged_card_printing,
            staged_face_printing=staged_face_printing,
        )

        self.process_card_localisations(
            card_data=card_data,
            staged_card_face=staged_card_face,
            staged_card_printing=staged_card_printing,
            staged_face_printing=staged_face_printing,
        )

    def process_card(self, staged_card: StagedCard) -> None:
        """
        Parses the given card data dict and returns a new or existing StagedCard
        :param staged_card:
        :return: A StagedCard that represents the json card
        """

        if staged_card.scryfall_oracle_id in self.parse_counter.cards_parsed:
            return

        self.parse_counter.cards_parsed.add(staged_card.scryfall_oracle_id)

        existing_card = self.existing_set.get_card(staged_card.scryfall_oracle_id)

        if existing_card:
            differences = staged_card.compare_with_card(existing_card)
            if differences:
                self.cards_to_update.append(
                    UpdateCard(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        name=staged_card.name,
                        field_data=differences,
                    )
                )
        else:
            self.cards_to_update.append(
                UpdateCard(
                    update_mode=UpdateMode.CREATE,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    name=staged_card.name,
                    field_data=staged_card.get_field_data(),
                )
            )
        self.process_card_rulings(staged_card, existing_card=existing_card)
        self.process_card_legalities(staged_card, existing_card=existing_card)

    def process_card_faces(
        self, staged_card: StagedCard, staged_card_face: StagedCardFace
    ) -> None:
        """

        :param staged_card:
        :param staged_card_face:
        :return:
        """
        existing_card_face = self.existing_set.get_card_face(
            staged_card.scryfall_oracle_id, staged_card_face.side
        )
        face_tuple = (staged_card_face.scryfall_oracle_id, staged_card_face.side)

        if face_tuple in self.parse_counter.card_faces_parsed:
            return

        self.parse_counter.card_faces_parsed.add(face_tuple)
        if existing_card_face:
            face_differences = staged_card_face.get_card_face_differences(
                existing_card_face
            )
            if face_differences:
                self.card_faces_to_update.append(
                    UpdateCardFace(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        name=staged_card.name,
                        face_name=staged_card_face.name,
                        side=staged_card_face.side,
                        field_data=face_differences,
                    )
                )
        else:
            self.card_faces_to_update.append(
                UpdateCardFace(
                    update_mode=UpdateMode.CREATE,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    name=staged_card.name,
                    face_name=staged_card_face.name,
                    side=staged_card_face.side,
                    field_data=staged_card_face.get_field_data(),
                )
            )

    def process_card_rulings(
        self, staged_card: StagedCard, existing_card: Card | None = None
    ) -> None:
        """
        Finds CardRulings of the given StagedCard to create or delete
        :param staged_card: The StagedCard to find rulings for
        :param existing_card:
        """
        # Use prefetched rulings to save performance
        existing_rulings = list(existing_card.rulings.all()) if existing_card else []
        for ruling in staged_card.unique_rulings:
            if not any(
                True
                for existing_ruling in existing_rulings
                if existing_ruling.text == ruling["text"]
            ):
                self.rulings_to_update.append(
                    UpdateCardRuling(
                        update_mode=UpdateMode.CREATE,
                        card_name=staged_card.name,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        ruling_date=ruling["date"],
                        ruling_text=ruling["text"],
                    )
                )

        # For every existing ruling, if it isn't contained in the list of rulings,
        # then mark it for deletion
        for existing_ruling in existing_rulings:
            if not any(
                True
                for ruling in staged_card.rulings
                if ruling["text"] == existing_ruling.text
            ):
                self.rulings_to_update.append(
                    UpdateCardRuling(
                        update_mode=UpdateMode.DELETE,
                        card_name=staged_card.name,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        ruling_date=existing_ruling.date,
                        ruling_text=existing_ruling.text,
                    )
                )

    def process_card_legalities(
        self, staged_card: StagedCard, existing_card: Card | None = None
    ) -> None:
        """
        Find CardLegalities for a card to update, create or delete
        :param existing_card:
        :param staged_card: The StagedCard to find legalities for
        """
        # Use prefetched legalities to improve performance
        existing_legalities = (
            list(existing_card.legalities.all()) if existing_card else []
        )
        for format_str, restriction in staged_card.legalities.items():
            if not any(
                True
                for existing_legality in existing_legalities
                if existing_legality.format.code == format_str
            ):
                self.legalities_to_update.append(
                    UpdateCardLegality(
                        update_mode=UpdateMode.CREATE,
                        card_name=staged_card.name,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        format_name=format_str,
                        restriction=restriction,
                    )
                )

        for old_legality in existing_legalities:
            if old_legality.format.code not in staged_card.legalities:
                self.legalities_to_update.append(
                    UpdateCardLegality(
                        update_mode=UpdateMode.DELETE,
                        card_name=staged_card.name,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        format_name=old_legality.format.code,
                        restriction=old_legality.restriction,
                    )
                )

            # Legalities to update
            elif (
                staged_card.legalities[old_legality.format.code]
                != old_legality.restriction
            ):
                self.legalities_to_update.append(
                    UpdateCardLegality(
                        update_mode=UpdateMode.UPDATE,
                        card_name=staged_card.name,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        format_name=old_legality.format.code,
                        restriction=staged_card.legalities[old_legality.format.code],
                    )
                )

    def process_card_printing(
        self,
        staged_card: StagedCard,
        staged_card_face: StagedCardFace,
        staged_card_printing: StagedCardPrinting,
        staged_face_printing: StagedCardFacePrinting,
    ) -> None:
        """
        Process a Card printed in a given set,
         returning the printings and printed languages that were found
        :param staged_card: The already known StagedCard
        :param staged_card_face:
        :param staged_card_printing:
        :param staged_face_printing:
        :return: A tuple containing the StagedCardPrinting and a list of StagedCardLocalisations
        """
        existing_printing = self.existing_set.get_printing(
            staged_card_printing.scryfall_id
        )
        if (
            staged_card_printing.scryfall_id
            not in self.parse_counter.card_printings_parsed
        ):
            self.parse_counter.card_printings_parsed.add(
                staged_card_printing.scryfall_id
            )
            if not existing_printing:
                self.printings_to_update.append(
                    UpdateCardPrinting(
                        update_mode=UpdateMode.CREATE,
                        card_scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        card_name=staged_card.name,
                        scryfall_id=staged_card_printing.scryfall_id,
                        set_code=self.staged_set.code,
                        field_data=staged_card_printing.get_field_data(),
                    )
                )
            else:
                differences = staged_card_printing.compare_with_existing_card_printing(
                    existing_printing
                )
                if differences:
                    self.printings_to_update.append(
                        UpdateCardPrinting(
                            update_mode=UpdateMode.UPDATE,
                            card_scryfall_oracle_id=staged_card.scryfall_oracle_id,
                            card_name=staged_card.name,
                            scryfall_id=staged_card_printing.scryfall_id,
                            set_code=self.staged_set.code,
                            field_data=differences,
                        )
                    )
        if staged_face_printing.uuid in self.parse_counter.card_face_printings_parsed:
            return

        self.parse_counter.card_face_printings_parsed.add(staged_face_printing.uuid)
        existing_face_printing = self.existing_set.get_face_printing(
            staged_card_printing.scryfall_id, face_side=staged_card_face.side
        )

        if existing_face_printing:
            differences = staged_face_printing.compare_with_existing_face_printing(
                existing_face_printing
            )
            if differences:
                self.face_printings_to_update.append(
                    UpdateCardFacePrinting(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_id=staged_card_printing.scryfall_id,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        card_name=staged_card.name,
                        card_face_name=staged_card_face.name,
                        printing_uuid=staged_face_printing.uuid,
                        side=staged_card_face.side,
                        field_data=differences,
                    )
                )
        else:
            self.face_printings_to_update.append(
                UpdateCardFacePrinting(
                    update_mode=UpdateMode.CREATE,
                    scryfall_id=staged_card_printing.scryfall_id,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    card_name=staged_card.name,
                    card_face_name=staged_card_face.name,
                    printing_uuid=staged_face_printing.uuid,
                    side=staged_card_face.side,
                    field_data=staged_face_printing.get_field_data(),
                )
            )

    def process_card_localisations(
        self,
        card_data: dict,
        staged_card_face: StagedCardFace,
        staged_card_printing: StagedCardPrinting,
        staged_face_printing: StagedCardFacePrinting,
    ) -> None:
        """

        :param card_data:
        :param staged_card_face:
        :param staged_card_printing:
        :param staged_face_printing:
        :return:
        """
        language_data_list = []
        if not card_data.get("isForeignOnly", False):
            # Fake the english language version from normal data
            english_data = {
                "language": "English",
                "name": card_data.get("name"),
                "text": card_data.get("text"),
                "type": card_data.get("type"),
            }
            if "faceName" in card_data:
                english_data["faceName"] = card_data["faceName"]
            if "multiverseId" in card_data["identifiers"]:
                english_data["multiverseId"] = card_data["identifiers"]["multiverseId"]
            language_data_list.append(english_data)
        language_data_list += card_data.get("foreignData", [])
        for language_data in language_data_list:
            self.parse_foreign_data(
                language_data,
                staged_card_face,
                staged_card_printing,
                staged_face_printing,
            )

    def parse_foreign_data(
        self,
        foreign_data: dict,
        staged_card_face: StagedCardFace,
        staged_card_printing: StagedCardPrinting,
        staged_face_printing: StagedCardFacePrinting,
    ):
        """

        :param foreign_data:
        :param staged_card_face:
        :param staged_card_printing:
        :param staged_face_printing:
        :return:
        """
        staged_localisation = StagedCardLocalisation(staged_card_printing, foreign_data)

        localisation_key = (
            staged_card_printing.scryfall_id,
            staged_localisation.language_name,
        )
        existing_localisation = self.existing_set.get_localisation(
            staged_card_printing.scryfall_id,
            language_name=staged_localisation.language_name,
        )

        if localisation_key not in self.parse_counter.card_localisations_parsed:
            self.parse_counter.card_localisations_parsed.add(localisation_key)

            if not existing_localisation:
                self.localisations_to_update.append(
                    UpdateCardLocalisation(
                        update_mode=UpdateMode.CREATE,
                        language_code=staged_localisation.language_name,
                        printing_scryfall_id=staged_card_printing.scryfall_id,
                        card_name=staged_localisation.card_name,
                        field_data=staged_localisation.get_field_data(),
                    )
                )
            else:
                differences = staged_localisation.compare_with_existing_localisation(
                    existing_localisation
                )
                if differences:
                    self.localisations_to_update.append(
                        UpdateCardLocalisation(
                            update_mode=UpdateMode.UPDATE,
                            language_code=staged_localisation.language_name,
                            printing_scryfall_id=staged_card_printing.scryfall_id,
                            card_name=staged_localisation.card_name,
                            field_data=differences,
                        )
                    )

        existing_face_localisation = self.existing_set.get_face_localisation(
            staged_card_printing.scryfall_id,
            language_name=staged_localisation.language_name,
            face_side=staged_card_face.side,
        )

        staged_localised_face = StagedCardFaceLocalisation(
            staged_card_printing, staged_face_printing, foreign_data
        )

        if not existing_face_localisation:
            self.face_localisations_to_update.append(
                UpdateCardFaceLocalisation(
                    update_mode=UpdateMode.CREATE,
                    language_code=staged_localised_face.language_name,
                    printing_scryfall_id=staged_card_printing.scryfall_id,
                    face_name=staged_localised_face.face_name,
                    face_printing_uuid=staged_localised_face.face_printing_uuid,
                    field_data=staged_localised_face.get_field_data(),
                )
            )
        else:
            differences = staged_localised_face.compare_with_existing_face_localisation(
                existing_face_localisation
            )
            if differences:
                self.face_localisations_to_update.append(
                    UpdateCardFaceLocalisation(
                        update_mode=UpdateMode.UPDATE,
                        language_code=staged_localised_face.language_name,
                        printing_scryfall_id=staged_card_printing.scryfall_id,
                        face_name=staged_localised_face.face_name,
                        face_printing_uuid=staged_localised_face.face_printing_uuid,
                        field_data=differences,
                    )
                )
