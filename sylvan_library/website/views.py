"""
Module for all website views
"""
import datetime
import logging
import random
import urllib.parse
import urllib.request
from typing import Dict, Any

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Colour,
    Deck,
    DeckCard,
    Language,
    PhysicalCard,
    Set,
    UserCardChange,
    UserOwnedCard,
    UserProps,
)
from pagination import get_page_buttons
from website.forms import (
    FieldSearchForm,
    QuerySearchForm,
    ChangeCardOwnershipForm,
    DeckForm,
)

logger = logging.getLogger("django")


def index(request: WSGIRequest) -> HttpResponse:
    """
    The index page of this site
    :param request: The
    :return:
    """
    context = {"sets": Set.objects.all()}
    return render(request, "website/index.html", context)


def name_search(request: WSGIRequest) -> HttpResponse:
    """
    The view for when a user searches by card name
    :param request: The user's request
    :return: The HTTP Response
    """
    query_form = QuerySearchForm(request.GET)
    query_form.user = request.user
    search_form = FieldSearchForm()
    search = query_form.get_search()
    return render(
        request,
        "website/simple_search.html",
        {
            "query_form": query_form,
            "form": search_form,
            "results": search.results,
            "result_count": search.paginator.count,
            "page": search.page,
            "page_buttons": get_page_buttons(
                search.paginator, query_form.get_page_number(), 3
            ),
            "pretty_query_message": search.get_pretty_str(),
            "error_message": search.error_message,
        },
    )


def simple_search(request: WSGIRequest) -> HttpResponse:
    """
    The simple search form
    :param request: The user's request
    :return: The HTTP Response
    """
    form = FieldSearchForm(request.GET)
    search = form.get_field_search()

    return render(
        request,
        "website/simple_search.html",
        {
            "form": form,
            "results": search.results,
            "result_count": search.paginator.count,
            "page": search.page,
            "page_buttons": get_page_buttons(
                search.paginator, form.get_page_number(), 3
            ),
        },
    )


# pylint: disable=unused-argument, missing-docstring
def advanced_search(request: WSGIRequest):
    return "advanced search"


# pylint: disable=unused-argument, missing-docstring
def search_results(request: WSGIRequest):
    return "search results"


def ajax_search_result_details(request: WSGIRequest, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request, "website/results/search_result_details.html", {"printing": printing}
    )


def ajax_search_result_rulings(request: WSGIRequest, card_id: int) -> HttpResponse:
    card = Card.objects.get(id=card_id)
    return render(request, "website/results/search_result_rulings.html", {"card": card})


def ajax_search_result_languages(
    request: WSGIRequest, printing_id: int
) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request, "website/results/search_result_languages.html", {"printing": printing}
    )


def ajax_card_printing_image(request: WSGIRequest, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, "website/card_image.html", {"printing": printing})


def ajax_search_result_add(request: WSGIRequest, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    form = ChangeCardOwnershipForm(printing)
    return render(
        request,
        "website/results/search_result_add.html",
        {"form": form, "printing": printing},
    )


def ajax_search_result_ownership(request: WSGIRequest, card_id: int) -> HttpResponse:
    card = Card.objects.get(id=card_id)
    ownerships = (
        UserOwnedCard.objects.filter(owner_id=request.user.id)
        .filter(physical_card__printed_languages__card_printing__card__id=card_id)
        .order_by("physical_card__printed_languages__card_printing__set__release_date")
    )
    changes = (
        UserCardChange.objects.filter(owner_id=request.user.id)
        .filter(physical_card__printed_languages__card_printing__card__id=card_id)
        .order_by("date")
    )
    return render(
        request,
        "website/results/search_result_ownership.html",
        {"card": card, "ownerships": ownerships, "changes": changes},
    )


def ajax_change_card_ownership(request: WSGIRequest) -> HttpResponse:
    if not request.POST.get("count"):
        return JsonResponse({"result": False, "error": "Invalid count"})

    try:
        with transaction.atomic():
            change_count = int(request.POST.get("count"))
            physical_card_id = int(request.POST.get("printed_language"))
            physical_card = PhysicalCard.objects.get(id=physical_card_id)
            physical_card.apply_user_change(change_count, request.user)
            return JsonResponse({"result": True})
    except PhysicalCard.DoesNotExist as ex:
        return JsonResponse({"result": False, "error": str(ex)})


def ajax_ownership_summary(request: WSGIRequest, card_id: int) -> HttpResponse:
    card = Card.objects.get(id=card_id)
    return render(request, "website/results/ownership_summary.html", {"card": card})


def ajax_search_result_set_summary(
    request: WSGIRequest, printing_id: int
) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request,
        "website/results/search_result_sets.html",
        {"card": printing.card, "selected_printing": printing},
    )


def ajax_search_result_decks(request: WSGIRequest, card_id: int) -> HttpResponse:
    card = Card.objects.get(pk=card_id)
    deck_cards = (
        DeckCard.objects.filter(deck__owner=request.user)
        .filter(card__in=card.get_all_sides())
        .order_by("-deck__date_created")
    )
    card_count = deck_cards.aggregate(card_count=Sum("count"))["card_count"]
    deck_count = deck_cards.aggregate(deck_count=Count("deck_id"))["deck_count"]

    return render(
        request,
        "website/results/search_result_decks.html",
        {"deck_cards": deck_cards, "card_count": card_count, "deck_count": deck_count},
    )


def ajax_search_result_links(request: WSGIRequest, card_id: int) -> HttpResponse:
    card = Card.objects.get(pk=card_id)
    linked_card_name = (
        card.display_name if card.layout != "split" else card.get_linked_name()
    )

    links = [
        {
            "name": "Search on Channel Fireball",
            "url": "https://store.channelfireball.com/products/search?{}".format(
                urllib.parse.urlencode({"q": card.display_name})
            ),
        },
        {
            "name": "TCGPlayer Decks",
            "url": "https://decks.tcgplayer.com/magic/deck/search?{}".format(
                urllib.parse.urlencode({"contains": card.display_name, "page": 1})
            ),
        },
        {
            "name": "Card Analysis on EDHREC",
            "url": "http://edhrec.com/route/?{}".format(
                urllib.parse.urlencode({"cc": card.display_name})
            ),
        },
        {
            "name": "Search on DeckStats",
            "url": "https://deckstats.net/decks/search/?{}".format(
                urllib.parse.urlencode({"search_cards[]": card.display_name})
            ),
        },
        {
            "name": "MTGTop8 decks",
            "url": "http://mtgtop8.com/search?{}".format(
                urllib.parse.urlencode(
                    {"MD_check": 1, "SB_check": 1, "cards": linked_card_name}
                )
            ),
        },
        {
            "name": "Search on Starcity Games",
            "url": "https://starcitygames.com/search.php?{}".format(
                urllib.parse.urlencode({"search_query": card.display_name})
            ),
        },
        {
            "name": "Search on Scryfall",
            "url": "https://scryfall.com/search?q={}".format(
                urllib.parse.urlencode({"name": card.display_name})
            ),
        },
    ]

    printlang = (
        CardPrintingLanguage.objects.filter(card_printing__card=card)
        .filter(multiverse_id__isnull=False)
        .filter(language=Language.english())
        .order_by("card_printing__set__release_date")
        .last()
    )
    if printlang:
        links.insert(
            0,
            {
                "name": "View on Gatherer",
                "url": "https://gatherer.wizards.com/Pages/Card/Details.aspx?{}".format(
                    urllib.parse.urlencode({"multiverseid": printlang.multiverse_id})
                ),
            },
        )

    return render(request, "website/results/search_result_links.html", {"links": links})


def get_page_number(request: WSGIRequest) -> int:
    try:
        return int(request.GET.get("page"))
    except (TypeError, ValueError):
        return 1


def deck_stats(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("website:index")

    users_deck_cards = Card.objects.filter(deck_cards__deck__owner=request.user)
    users_cards = (
        Card.objects.filter(
            printings__printed_languages__physical_cards__ownerships__owner=request.user,
            is_token=False,
        )
        .exclude(side="b")
        .exclude(side="c")
        .distinct()
    )
    if not hasattr(request.user, "userprops"):
        UserProps.add_to_user(request.user)

    rand = random.Random(request.user.userprops.unused_cards_seed)
    unused_cards = list(users_cards.exclude(id__in=users_deck_cards).order_by("id"))
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:10]
    unused_cards = [
        {
            "card": card,
            "preferred_printing": card.printings.filter(
                printed_languages__physical_cards__ownerships__owner=request.user
            )
            .order_by("set__release_date")
            .last(),
        }
        for card in unused_cards
    ]

    deck_count = Deck.objects.filter(owner=request.user).count()

    deck_warnings = []
    for deck in Deck.objects.filter(owner=request.user, is_prototype=False):
        try:
            deck.validate_format()
        except ValidationError as error:
            deck_warnings.append({"deck": deck, "msg": error.message})

    return render(
        request,
        "website/decks/deck_stats.html",
        {
            "unused_cards": unused_cards,
            "deck_count": deck_count,
            "deck_warnings": deck_warnings,
        },
    )


def change_unused_decks(request: WSGIRequest) -> HttpResponse:
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
    page_size = 15
    users_decks = Deck.objects.filter(owner=request.user).order_by(
        "-date_created", "-last_modified", "-id"
    )
    paginator = Paginator(users_decks, page_size)
    page_number = get_page_number(request)
    page_buttons = get_page_buttons(paginator, page_number, 3)
    return render(
        request,
        "website/decks/decks.html",
        {"decks": list(paginator.page(page_number)), "page_buttons": page_buttons},
    )


def deck_view(request: WSGIRequest, deck_id: int) -> HttpResponse:
    try:
        deck = Deck.objects.get(id=deck_id, owner=request.user)
    except Deck.DoesNotExist:
        return redirect("website:decks")
    return render(request, "website/decks/deck_view.html", {"deck": deck})


def deck_edit(request: WSGIRequest, deck_id: int) -> HttpResponse:
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
    return render(request, "website/decks/deck_edit.html", {"deck_form": deck_form})


def deck_create(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        deck_form = DeckForm(request.POST)

        if deck_form.is_valid():
            try:
                deck = deck_form.instance
                deck.owner = request.user
                # deck_form.full_clean()
                with transaction.atomic():
                    deck.full_clean()
                    deck.save()
                    deck.cards.all().delete()
                    for deck_card in deck_form.get_cards():
                        deck_card.full_clean()
                        deck_card.save()

                    if not deck_form.cleaned_data.get("skip_validation"):
                        deck.validate_format()
                if not request.POST.get("save_continue"):
                    return redirect("website:deck_view", deck_id=deck.id)
            except ValidationError as err:
                deck_form.add_error(None, err)
                deck_form.instance.id = None
                # deck_form = DeckForm(request.POST)
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
    try:
        deck = Deck.objects.get(pk=deck_id)
    except Deck.DoesNotExist:
        return JsonResponse({"error": "Deck not found"})

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


def get_colour_info() -> Dict[int, Dict[str, Any]]:
    return {
        colour.symbol: {
            "name": colour.name,
            "symbol": colour.symbol,
            "display_order": colour.display_order,
            "chart_colour": colour.chart_colour,
        }
        for colour in Colour.objects.all().order_by("display_order")
    }
