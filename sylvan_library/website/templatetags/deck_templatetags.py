"""
Module for custom template filters to get the image paths of different card models
"""

from typing import List

from django import template

# pylint: disable=invalid-name
from cards.models.card import CardPrinting
from cards.models.decks import DeckCard, Deck

register = template.Library()


@register.filter(name="deck_group_count")
def deck_card_group_count(cards: List[DeckCard]) -> int:
    """
    Gets the total number of cards in the given list of deck cards
    :param cards: A QuerySet of DeckCards
    :return: The total number of cards
    """
    return sum(card.count for card in cards)


@register.filter(name="board_cards")
def decK_board_card_count(deck: Deck, board: str = "main") -> List[DeckCard]:
    """
    Gets the number of cards in the given decks board
    :param deck: The deck to get the
    :param board: The board to get the cards for
    :return: The number of cards in that board
    """
    return deck.get_cards(board)


@register.filter(name="owner_preferred_card")
def deck_owner_preferred_card(deck_card: DeckCard) -> CardPrinting:
    """
    Gets the latest card that the owner of the deck cards
    :param deck_card: The deck card
    :return: The preferred printing
    """
    try:
        return (
            deck_card.card.printings.filter(
                localisations__ownerships__owner=deck_card.deck.owner,
                set__release_date__lte=deck_card.deck.date_created,
            )
            .order_by("set__release_date")
            .last()
        )
    except CardPrinting.DoesNotExist:
        return deck_card.card.printings.order_by("set__release_date").last()
