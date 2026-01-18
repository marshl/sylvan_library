import logging
import re

from sylvan_library.cardsearch.colours import (
    get_card_face_produces,
    RE_GENERIC_MANA,
    MANA_SYMBOLS,
)
from sylvan_library.cards.models.card import CardFace, Card
from sylvan_library.cardsearch.models import CardFaceSearchMetadata, CardSearchMetadata
from sylvan_library.cardsearch.sort_key import get_sort_key

logger = logging.getLogger("django")

RE_REMINDER_TEXT = re.compile(r"\(.+?\)")


def build_card_symbol_counts(metadata: CardFaceSearchMetadata) -> bool:
    """
    Builds the counts of symbols in the costs of the given card
    :param metadata: The metadata record to build symbol counts for
    """
    changed = False
    for symbol in MANA_SYMBOLS:
        if metadata.card_face.mana_cost:
            count = metadata.card_face.mana_cost.count("{" + symbol + "}")
        else:
            count = 0

        attr_name = "symbol_count_" + symbol.lower().replace("/", "_")
        if getattr(metadata, attr_name) != count:
            setattr(metadata, attr_name, count)
            changed = True

    generic_count = get_card_generic_mana(metadata.card_face)
    if metadata.symbol_count_generic != generic_count:
        metadata.symbol_count_generic = generic_count
        changed = True

    return changed


def get_card_generic_mana(card_face: CardFace) -> int:
    """
    Gets the number for the generic mana symbol in a cards cost
    (if there is one, otherwise 0)
    :return: The amount of generic mana required to cast this card
    """
    if not card_face.mana_cost:
        return 0

    generic_mana = RE_GENERIC_MANA.search(card_face.mana_cost)
    if generic_mana:
        return int(generic_mana.group(1))
    return 0


def build_produces_counts(metadata: CardFaceSearchMetadata) -> bool:
    """
    Computes what colours a card can produce
    :param metadata: The card to build "produces" data for
    """
    produces = get_card_face_produces(metadata.card_face)
    changed = False
    for symbol, does_produce in produces.items():
        attr_name = "produces_" + symbol
        if getattr(metadata, attr_name) != does_produce:
            setattr(metadata, attr_name, does_produce)
            changed = True

    return changed


def build_metadata_for_card_face(card_face: CardFace) -> bool:
    """
    Constructs (or repopulates) the search metadata for the given card
    :param card_face: The card to build the metadata for
    """
    if hasattr(card_face, "search_metadata"):
        metadata = card_face.search_metadata
    else:
        metadata = CardFaceSearchMetadata(card_face=card_face)
    changed = False
    if card_face.rules_text and "(" in card_face.rules_text:
        new_text = RE_REMINDER_TEXT.sub("", card_face.rules_text)
        if metadata.rules_without_reminders != new_text:
            metadata.rules_without_reminders = new_text
            changed = True

    changed = build_card_symbol_counts(metadata) or changed
    changed = build_produces_counts(metadata) or changed

    if changed or not metadata.id:
        metadata.save()
    return changed


def is_card_commander(card: Card):
    face = card.faces.first()

    # if face.supertypes.filter(name="Token").exists():
    if any(_type.name == "Token" for _type in face.types.all()):
        return False

    if face.rules_text:
        if " can be your commander" in face.rules_text:
            return True

    # if face.types.filter(name="Background").exists():
    if any(_type.name == "Background" for _type in face.types.all()):
        return True

    if any(
        supertype.name == "Legendary" for supertype in face.supertypes.all()
    ) and any(_type.name == "Creature" for _type in face.types.all()):
        return True

    if card.name == "Grist, the Hunger Tide":
        return True

    return False


def build_metadata_for_card(card: Card) -> bool:
    if hasattr(card, "search_metadata"):
        metadata = card.search_metadata
        changed = False
    else:
        metadata = CardSearchMetadata(card=card)
        changed = True

    is_commander = is_card_commander(card)
    if metadata.is_commander != is_commander:
        changed = True
        metadata.is_commander = is_commander

    super_sort_key = get_sort_key(card)
    if metadata.super_sort_key != super_sort_key:
        changed = True
        metadata.super_sort_key = super_sort_key

    if changed:
        metadata.save()
    return changed
