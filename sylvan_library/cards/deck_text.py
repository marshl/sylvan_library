"""
Converting a deck's cards to and from the plain text board format, e.g.
4x Lightning Bolt
1 Kenrith, the Returned King *CMDR*
"""

import re
from typing import Dict, Optional, List, Tuple, Any

from django.core.exceptions import ValidationError
from django.db.models import Func, Value, F

from sylvan_library.cards.models.card import Card
from sylvan_library.cards.models.decks import Deck, DeckCard

BOARDS = ("main", "side", "maybe", "acquire")


def parse_card_text(text: str) -> Optional[Tuple[int, str, dict]]:
    """
    Parses the text of a card row and returns the count, name and other options of the card
    :param text: The line of deck text for the card
    :return: If the text is valid, then a tuple containing the count, name and options
             for hte card, otherwise None
    """
    if text is None or text.strip() == "":
        return None

    text = text.strip().replace("’", "'").replace("Æ", "Ae")
    if re.match(r"^\d+$", text):
        return None

    # Note that this regex won't work for cards that start with numbers
    # Fortunately the only card like that is "1998 World Champion"
    matches = re.match(
        r"((?P<count>\d+)\s*x?)? *(?P<name>.+?)(?P<cmdr> ?\*cmdr\*)?$",
        text,
        re.IGNORECASE,
    )

    if not matches:
        raise ValidationError(f"Invalid card {text}")

    card_name = matches["name"].strip()

    if matches["count"] is None:
        count = 1
    else:
        try:
            count = int(matches["count"])
        except (TypeError, ValueError) as ex:
            raise ValidationError(
                f"Invalid count \"{matches['count']}\" for {card_name}"
            ) from ex

    if count == 0:
        return None

    return count, card_name, {"is_commander": bool(matches["cmdr"])}


def card_from_text(
    count: int, card_name: str, board: str, options: Dict[str, Any], deck: Deck
) -> Optional[DeckCard]:
    """
    Parses a single line of text and returns the DeckCard for it
    :param count: The card count
    :param card_name: The name of the card
    :param board: The board that the card belongs to
    :param options: A dict of additional configuration for the card, (e.g. is_commander: bool)
    :param deck: The deck the card is being added to
    :return: A DeckCard object if it is valid
    :raises: ValidationError if the card could not be parsed for some reason
    """

    if card_name.lower() in (
        "creatures",
        "creature",
        "artifacts",
        "artifact",
        "land",
        "lands",
        "basic land",
        "non-basic land",
        "nonbasic land",
        "planeswalker",
        "planeswalkers",
        "instant",
        "instants",
        "sorcery",
        "sorceries",
        "general",
        "commander",
        "commanders",
        "x",
        "enchantment",
        "enchantments",
        "other spells",
        "instants and sorc.",
        "other",
        "battle",
        "battles",
    ):
        return None

    try:
        # We have to ignore tokens, as otherwise Earthshaker Khenra would return two results
        # But you shouldn't be putting tokens in a deck anyway
        # We also have to ignore "Battle the Horde" and "Unknown Event" sets which both include cards
        # with the same name as normal cards
        card: Card = Card.objects.exclude(printings__set__code__in=("TBTH", "UNK")).get(
            name__iexact=card_name, is_token=False
        )
    except Card.DoesNotExist as ex:
        stripped_name = re.sub(r"\W", "", card_name)
        card_matches = (
            Card.objects.annotate(
                short_name=Func(
                    F("name"),
                    Value(r"\W"),
                    Value(""),
                    Value("g"),
                    function="regexp_replace",
                )
            )
            .exclude(name__startswith="A-")  # Ignore Alchemy cards
            .filter(is_token=False, short_name__icontains=stripped_name)
        )
        if card_matches.count() == 1:
            card = card_matches.first()
        else:
            raise ValidationError(f'Unknown card "{card_name}"') from ex
    except Card.MultipleObjectsReturned as ex:
        raise ValidationError(f'Card "{card_name}" matches too many cards: {ex}')

    if card.layout in ("scheme", "planar", "vanguard", "emblem"):
        raise ValidationError(
            f'You can\'t put the {card.layout} card "{card.name}" in a deck'
        )

    # It doesn't make sense to have the back half of a meld card in a deck (which is stored as a separate card)
    if (
        card.layout == "meld"
        and card.faces.count() == 1
        and card.faces.first().side == "b"
    ):
        raise ValidationError(
            f"Reverse side meld cards like {card.name} are not allowed"
        )

    deck_card = DeckCard(card=card, count=count, board=board, deck=deck)
    if options["is_commander"]:
        deck_card.is_commander = True

    return deck_card


def get_deck_cards(boards: Dict[str, str], deck: Deck) -> List[DeckCard]:
    """
    Gets the cards from the text of all the boards in the deck.
    :param boards: The board keys to their text values
    :param deck: The deck the cards belong to
    :return: The list of DeckCards as long as they are all valid
    :raises: ValidationError if ANY of the cards are invalid (wrong number, wrong name etc.)
    """
    deck_cards: List[DeckCard] = []
    validation_errors = []
    for board_key, board in boards.items():
        for line in (board or "").split("\n"):
            try:
                parts = parse_card_text(line)
                if parts is None:
                    continue
                count, card_name, options = parts
                deck_card = card_from_text(count, card_name, board_key, options, deck)
                if not deck_card:
                    continue
                # If the card already exists in this board...
                existing_card = next(
                    (
                        dc
                        for dc in deck_cards
                        if dc.card == deck_card.card and dc.board == board_key
                    ),
                    None,
                )
                # ... then just add to the existing count
                if existing_card:
                    existing_card.count += deck_card.count
                else:
                    deck_cards.append(deck_card)
            except ValidationError as error:
                validation_errors.append(error)

    if validation_errors:
        raise ValidationError(validation_errors)

    return deck_cards


def get_board_text(deck: Deck) -> Dict[str, str]:
    """
    Gets the text of each board of a deck, with the main board split into type groups
    :param deck: The deck
    :return: The board keys to their text values
    """
    main_board = ""
    for card_group in deck.get_card_groups():
        if not card_group["cards"]:
            continue
        main_board += card_group["name"] + "\n"
        main_board += (
            "\n".join(card.as_deck_text() for card in card_group["cards"]) + "\n\n"
        )

    boards = {"main": main_board}
    for board_key in ("side", "maybe", "acquire"):
        board_cards = deck.cards.filter(board=board_key).order_by("card__name")
        boards[board_key] = "\n".join(card.as_deck_text() for card in board_cards)
    return boards
