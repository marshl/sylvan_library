
import datetime
import random

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from cards.models.card import (
    Card,
)
from cards.models.decks import Deck
from cards.models.user import UserProps
from website.forms import (
    DeckForm,
)
from website.pagination import get_page_buttons
from website.views.utils import get_unused_cards, get_page_number, get_unused_commanders, \
    get_colour_info, get_unused_partner_commanders


def deck_stats(request: WSGIRequest) -> HttpResponse:
    """
    Gets the stats page for a user's decks
    :param request: The user's request
    :return: The deck stats HTML page
    """
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return redirect("website:index")

    deck_count = Deck.objects.filter(owner=request.user).count()

    deck_warnings = []

    partner_pairs, background_pairs = get_unused_partner_commanders(request.user)

    return render(
        request,
        "website/decks/deck_stats.html",
        {
            "unused_cards": get_unused_cards(request.user),
            "unused_commanders": get_unused_commanders(request.user),
            "partner_pairs": partner_pairs,
            "background_pairs": background_pairs,
            "deck_count": deck_count,
            "deck_warnings": deck_warnings,
        },
    )


def change_unused_decks(request: WSGIRequest) -> HttpResponse:
    """
    Rerolls the random number seed for which unused cards should be shown in the user's deck stats
    :param request: The request
    :return: A redirect back to decks stats
    """
    if not isinstance(request.user, User):
        return redirect("website:deck_stats")
    if request.user.is_anonymous:
        return redirect("website:index")

    if not hasattr(request.user, "userprops"):
        UserProps.add_to_user(request.user)

    props = request.user.userprops
    props.unused_cards_seed = random.randint(
        0, abs(UserProps._meta.get_field("unused_cards_seed").validators[0].limit_value)
    )
    props.full_clean()
    props.save()
    return redirect("website:deck_stats")


def deck_list(request: WSGIRequest) -> HttpResponse:
    """
    Shows the list of all decks the user owns
    :param request: The HttpRequest
    :return: THe HttpResponse
    """
    if not isinstance(request.user, User) or request.user.is_anonymous:
        return redirect("website:index")
    page_size = 10
    users_decks = Deck.objects.filter(owner=request.user).order_by(
        "-is_prototype", "-date_created", "-last_modified", "-id"
    )
    final_decks = users_decks.filter(is_prototype=False)
    prototype_decks = users_decks.filter(is_prototype=True)

    final_paginator = Paginator(final_decks, page_size)
    final_page_number = get_page_number(request)
    final_page_buttons = get_page_buttons(final_paginator, final_page_number, 3)

    prototype_paginator = Paginator(prototype_decks, page_size)
    prototype_page_number = get_page_number(request, param_name="prototype_page")
    prototype_page_buttons = get_page_buttons(
        prototype_paginator, prototype_page_number, 3
    )

    return render(
        request,
        "website/decks/decks.html",
        {
            "final_decks": list(final_paginator.page(final_page_number)),
            "final_page_buttons": final_page_buttons,
            "prototype_decks": list(prototype_paginator.page(prototype_page_number)),
            "prototype_page_buttons": prototype_page_buttons,
        },
    )


def deck_view(request: WSGIRequest, deck_id: int) -> HttpResponse:
    """
    Read-only view of a deck
    :param request: The user's request
    :param deck_id: The ID of th deck
    :return: The HTTP response
    """
    if not isinstance(request.user, User) or request.user.is_anonymous:
        return redirect("website:index")

    try:
        deck = Deck.objects.get(id=deck_id, owner=request.user)
    except Deck.DoesNotExist:
        return redirect("website:decks")

    return render(
        request,
        "website/decks/deck_view.html",
        {"deck": deck, "page_title": f"{deck.name or 'View Deck'} - Sylvan Library"},
    )


def deck_edit(request: WSGIRequest, deck_id: int) -> HttpResponse:
    """
    The deck edit form
    :param request: The user's request
    :param deck_id: The ID of the deck
    :return: The response
    """
    deck = Deck.objects.get(pk=deck_id)
    if deck.owner != request.user:
        return redirect("website:decks")

    if request.method == "POST":
        deck_form = DeckForm(request.POST, instance=deck)
        try:
            deck_form.full_clean()
            with transaction.atomic():
                deck.full_clean()
                deck.save()
                deck.cards.all().delete()

                deck_cards = deck_form.get_cards()
                for deck_card in deck_cards:
                    deck_card.full_clean()
                    deck_card.save()

                if not deck_form.cleaned_data.get(
                    "skip_validation"
                ) and not deck_form.cleaned_data.get("is_prototype"):
                    deck.validate_format()

            if not request.POST.get("save_continue"):
                return redirect("website:deck_view", deck_id=deck.id)

        except ValidationError as err:
            deck_form.add_error(None, err)
            deck_form.instance.id = deck_id
        else:
            deck_form = DeckForm(instance=deck)
    else:
        deck_form = DeckForm(instance=deck)
        deck_form.populate_boards()
    return render(
        request,
        "website/decks/deck_edit.html",
        {
            "deck_form": deck_form,
            "page_title": f"Edit {deck.name or 'new deck'} - Sylvan Library",
        },
    )


def deck_create(request: WSGIRequest) -> HttpResponse:
    """
    Deck creation form
    :param request: The user's request
    :return: Either the deck page, or the deck view page, depending on errors and settings
    """
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return redirect("website:index")

    if request.method == "POST":
        deck_form = DeckForm(request.POST)
        if deck_form.is_valid():
            try:
                deck = deck_form.instance
                deck.owner = request.user
                with transaction.atomic():
                    deck.full_clean()
                    deck.save()
                    deck.cards.all().delete()
                    for deck_card in deck_form.get_cards():
                        deck_card.full_clean()
                        deck_card.save()

                    if not deck_form.cleaned_data.get(
                        "skip_validation"
                    ) and not deck_form.cleaned_data.get("is_prototype"):
                        deck.validate_format()
                if not request.POST.get("save_continue"):
                    return redirect("website:deck_view", deck_id=deck.id)
            except ValidationError as err:
                deck_form.add_error(None, err)
                deck_form.instance.id = None
    else:
        deck = Deck()
        deck.owner = request.user
        deck.date_created = datetime.date.today()
        deck_form = DeckForm(instance=deck)

    return render(request, "website/decks/deck_edit.html", {"deck_form": deck_form})


def deck_card_search(request: WSGIRequest) -> JsonResponse:
    """
    Returns a list of cards that can used in a deck
    :param request: The Http Request
    :return: A Json response with a list of cards that match the search
    """
    if "card_name" not in request.GET:
        return JsonResponse({"cards": []})

    card_name = request.GET.get("card_name", "")
    cards = list(Card.objects.filter(name__icontains=card_name, is_token=False).all())
    cards.sort(
        key=lambda card: "0" + card.name.lower()
        if card.name.lower().startswith(card_name.lower())
        else "1" + card.name.lower()
    )
    result = [
        {"label": card.name, "value": card.name, "id": card.id} for card in cards[:10]
    ]
    return JsonResponse({"cards": result})


def deck_colour_weights(request: WSGIRequest, deck_id: int) -> JsonResponse:
    """
    Gets the colour weights of a given deck
    :param request: The user's request
    :param deck_id: The ID of the deck
    :return: The colour weights in JSON
    """
    try:
        deck = Deck.objects.get(pk=deck_id)
    except Deck.DoesNotExist:
        return JsonResponse({"error": "Deck not found"}, 404)

    if deck.is_private and request.user != deck.owner:
        raise PermissionDenied()

    colours = get_colour_info()
    land_symbols = deck.get_land_symbol_counts()
    mana_symbols = deck.get_cost_symbol_counts()
    land_symbols = [
        {"count": count, **colours[symbol]} for symbol, count in land_symbols.items()
    ]
    mana_symbols = [
        {"count": count, **colours[symbol]} for symbol, count in mana_symbols.items()
    ]

    return JsonResponse({"land_symbols": land_symbols, "mana_symbols": mana_symbols})

