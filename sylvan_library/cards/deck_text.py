"""
Converting a deck's cards to and from the plain text board format, e.g.
4x Lightning Bolt
1 Kenrith, the Returned King *CMDR*
"""

import datetime
import re
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Func, QuerySet, Value
from django.db.models.functions import Lower

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
        r"((?P<count>\d+)\s*(?:x\b)?)? *(?P<name>.+?)(?P<cmdr> ?\*cmdr\*)?$",
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


def deck_card_queryset() -> QuerySet:
    """
    The cards that can be put in a deck by name.
    Tokens are ignored, as otherwise Earthshaker Khenra would return two results, and
    you shouldn't be putting tokens in a deck anyway. The "Battle the Horde" and
    "Unknown Event" sets are also ignored, as they both include cards with the same
    name as normal cards.
    """
    return Card.objects.exclude(printings__set__code__in=("TBTH", "UNK")).filter(
        is_token=False
    )


def cards_by_name(names: List[str]) -> Dict[str, Card]:
    """
    The cards with exactly the given names, ignoring case, in one query. Names that
    match more than one card are left out.
    :param names: The card names to look up
    :return: The lower case card names to their cards
    """
    matches: Dict[str, List[Card]] = {}
    for card in (
        deck_card_queryset()
        .annotate(lower_name=Lower("name"))
        .filter(lower_name__in={name.lower() for name in names})
        .distinct()
    ):
        matches.setdefault(card.lower_name, []).append(card)
    return {name: cards[0] for name, cards in matches.items() if len(cards) == 1}


def validate_card_for_deck(card: Card) -> None:
    """
    Checks that a card can be put in a deck at all
    :raises: ValidationError if it can't
    """
    if card.is_token:
        raise ValidationError(f'You can\'t put the token "{card.name}" in a deck')

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


def card_from_text(
    count: int,
    card_name: str,
    board: str,
    options: Dict[str, Any],
    deck: Deck,
    known_cards: Optional[Dict[str, Card]] = None,
) -> Optional[DeckCard]:
    """
    Parses a single line of text and returns the DeckCard for it
    :param count: The card count
    :param card_name: The name of the card
    :param board: The board that the card belongs to
    :param options: A dict of additional configuration for the card, (e.g. is_commander: bool)
    :param deck: The deck the card is being added to
    :param known_cards: Cards already looked up by their lower case name
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

    card = (known_cards or {}).get(card_name.lower())
    if card is None:
        try:
            card = deck_card_queryset().get(name__iexact=card_name)
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

    validate_card_for_deck(card)

    deck_card = DeckCard(card=card, count=count, board=board, deck=deck)
    if options["is_commander"]:
        deck_card.is_commander = True

    return deck_card


@dataclass
class BoardLine:
    """
    The result of reading one line of a board's text: either the card it names or why
    it couldn't be read. Blank lines and headings like "Creatures" aren't included.
    """

    line_number: int
    typed_name: str
    deck_card: Optional[DeckCard] = None
    error: Optional[str] = None


def parse_board_lines(board_key: str, text: str, deck: Deck) -> List[BoardLine]:
    """
    Reads each line of a board's text
    :param board_key: The board the text is for (main, side etc.)
    :param text: The text of the board
    :param deck: The deck the cards belong to
    :return: A BoardLine for each line that names a card, or tries to
    """
    results: List[BoardLine] = []
    parsed_lines = []
    for line_number, line in enumerate((text or "").split("\n"), start=1):
        try:
            parts = parse_card_text(line)
        except ValidationError as error:
            results.append(
                BoardLine(line_number, line.strip(), error=" ".join(error.messages))
            )
            continue
        if parts is not None:
            parsed_lines.append((line_number, parts))

    known_cards = cards_by_name([name for _, (_, name, _) in parsed_lines])
    for line_number, (count, card_name, options) in parsed_lines:
        try:
            deck_card = card_from_text(
                count, card_name, board_key, options, deck, known_cards
            )
        except ValidationError as error:
            results.append(
                BoardLine(line_number, card_name, error=" ".join(error.messages))
            )
            continue
        if deck_card:
            results.append(BoardLine(line_number, card_name, deck_card=deck_card))
    return sorted(results, key=lambda line: line.line_number)


def merge_deck_cards(lines: List[BoardLine]) -> List[DeckCard]:
    """
    The deck cards from the lines that could be read, with the counts of any card
    listed more than once in the same board added together
    """
    deck_cards: List[DeckCard] = []
    for line in lines:
        deck_card = line.deck_card
        if deck_card is None:
            continue
        existing_card = next(
            (
                dc
                for dc in deck_cards
                if dc.card == deck_card.card and dc.board == deck_card.board
            ),
            None,
        )
        if existing_card:
            existing_card.count += deck_card.count
            existing_card.is_commander |= deck_card.is_commander
        else:
            deck_cards.append(deck_card)
    return deck_cards


def get_deck_cards(boards: Dict[str, str], deck: Deck) -> List[DeckCard]:
    """
    Gets the cards from the text of all the boards in the deck.
    :param boards: The board keys to their text values
    :param deck: The deck the cards belong to
    :return: The list of DeckCards as long as they are all valid
    :raises: ValidationError if ANY of the cards are invalid (wrong number, wrong name etc.)
    """
    lines: List[BoardLine] = []
    validation_errors = []
    for board_key, board in boards.items():
        board_lines = parse_board_lines(board_key, board, deck)
        lines += board_lines
        validation_errors += [
            f"{board_key.capitalize()} line {line.line_number}: {line.error}"
            for line in board_lines
            if line.error
        ]

    if validation_errors:
        raise ValidationError(validation_errors)

    return merge_deck_cards(lines)


def check_deck_text(boards: Dict[str, str], deck_format: str, owner) -> dict:
    """
    Reads the text of a deck's boards without saving anything, for showing problems
    while the deck is being edited.
    :param boards: The board keys to their text values
    :param deck_format: The deck's format, or blank to skip the format rules
    :param owner: The user editing the deck
    :return: Each board's card count and its problem lines, and any format rules the
             readable cards break
    """
    result: Dict[str, Any] = {"boards": {}, "format_errors": []}
    # The format rules are queries on the deck's saved cards, so the deck is saved
    # and then rolled back
    with transaction.atomic():
        deck = Deck.objects.create(
            owner=owner,
            name="Deck check",
            format=deck_format or "unknown",
            date_created=datetime.date.today(),
        )
        lines: List[BoardLine] = []
        for board_key in BOARDS:
            board_lines = parse_board_lines(board_key, boards.get(board_key, ""), deck)
            lines += board_lines
            issues = []
            for line in board_lines:
                if line.error:
                    issues.append({"line": line.line_number, "error": line.error})
                elif line.deck_card.card.name.lower() != line.typed_name.lower():
                    issues.append(
                        {
                            "line": line.line_number,
                            "matched": line.deck_card.card.name,
                        }
                    )
            result["boards"][board_key] = {
                "count": sum(
                    line.deck_card.count for line in board_lines if line.deck_card
                ),
                "issues": issues,
            }

        if deck_format:
            for deck_card in merge_deck_cards(lines):
                deck_card.save()
            try:
                deck.validate_format()
            except ValidationError as error:
                result["format_errors"] = error.messages
        transaction.set_rollback(True)
    return result


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
