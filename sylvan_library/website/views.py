"""
Module for all website views
"""
import datetime
import logging
import random
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Dict, Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Count, Q
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
from website.forms import (
    FieldSearchForm,
    QuerySearchForm,
    ChangeCardOwnershipForm,
    DeckForm,
)
from website.pagination import get_page_buttons

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


def ajax_search_result_details(request: WSGIRequest, printing_id: int) -> HttpResponse:
    """
    Gets the details of a card in the result page
    :param request: The user's request
    :param printing_id: The ID of the CardPrinting
    :return: The HTTP response
    """
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request, "website/results/search_result_details.html", {"printing": printing}
    )


def ajax_search_result_rulings(request: WSGIRequest, card_id: int) -> HttpResponse:
    """
    Returns the rulings of a card
    :param request: The user's request
    :param card_id: The ID of the Card
    :return: The rulings HTML
    """
    card = Card.objects.get(id=card_id)
    return render(request, "website/results/search_result_rulings.html", {"card": card})


def ajax_search_result_languages(
    request: WSGIRequest, printing_id: int
) -> HttpResponse:
    """
    Gets the languages HTML of a printing
    :param request: The user's request
    :param printing_id: The CardPrinting ID
    :return: The languages HTML
    """
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request, "website/results/search_result_languages.html", {"printing": printing}
    )


def ajax_card_printing_image(request: WSGIRequest, printing_id: int) -> HttpResponse:
    """
    Gets the image view of a printing
    :param request: The user's request
    :param printing_id: The CardPrinting ID
    :return: The image HTML
    """
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, "website/card_image.html", {"printing": printing})


def ajax_search_result_add(request: WSGIRequest, printing_id: int) -> HttpResponse:
    """
    Gets the "Add card" form for a card printing
    :param request: The user's request
    :param printing_id: The CardPrinting ID
    :return: The add form HTML
    """
    printing = CardPrinting.objects.get(id=printing_id)
    form = ChangeCardOwnershipForm(printing)
    return render(
        request,
        "website/results/search_result_add.html",
        {"form": form, "printing": printing},
    )


def ajax_search_result_ownership(request: WSGIRequest, card_id: int) -> HttpResponse:
    """
    Gets the ownership list for a Card
    :param request: The user's request
    :param card_id: The Card ID
    :return: The ownership HTML
    """
    card = Card.objects.get(id=card_id)
    ownerships = (
        UserOwnedCard.objects.filter(owner=request.user)
        .filter(physical_card__printed_languages__card_printing__card__id=card_id)
        .order_by("physical_card__printed_languages__card_printing__set__release_date")
    )
    changes = (
        UserCardChange.objects.filter(owner=request.user)
        .filter(physical_card__printed_languages__card_printing__card__id=card_id)
        .order_by("date")
    )
    return render(
        request,
        "website/results/search_result_ownership.html",
        {"card": card, "ownerships": ownerships, "changes": changes},
    )


def ajax_change_card_ownership(request: WSGIRequest) -> HttpResponse:
    """
    Applies an ownership change (adding or removing the amount that a card owns)
    :param request: The user's request
    :return: JSON containing whether the change was successful or not
    """
    if not request.POST.get("count"):
        return JsonResponse({"result": False, "error": "Invalid count"})

    try:
        with transaction.atomic():
            change_count = int(request.POST["count"])
            physical_card_id = int(request.POST["printed_language"])
            physical_card = PhysicalCard.objects.get(id=physical_card_id)
            physical_card.apply_user_change(change_count, request.user)
            return JsonResponse({"result": True})
    except PhysicalCard.DoesNotExist as ex:
        return JsonResponse({"result": False, "error": str(ex)})


def ajax_ownership_summary(request: WSGIRequest, card_id: int) -> HttpResponse:
    """
    Gets the ownership HTML summary
    :param request: The user's request
    :param card_id: The Card ID
    :return: The ownership summary HTML
    """
    card = Card.objects.get(id=card_id)
    return render(request, "website/results/ownership_summary.html", {"card": card})


def ajax_search_result_set_summary(
    request: WSGIRequest, printing_id: int
) -> HttpResponse:
    """
    Gets the set summary for a given CardPrinting
    :param request: The user's request
    :param printing_id: The CardPrinting ID
    :return: The set summary HTML
    """
    printing = CardPrinting.objects.get(id=printing_id)
    return render(
        request,
        "website/results/search_result_sets.html",
        {"card": printing.card, "selected_printing": printing},
    )


def ajax_search_result_decks(request: WSGIRequest, card_id: int) -> HttpResponse:
    """
    Gets the deck list used by a given card
    :param request: The user's request
    :param card_id: The ID of the Card to get the HTML for
    :return: THe deck list HTML
    """
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
    """
    Gets the links HTML of a Card
    :param request: The user's request
    :param card_id: The ID of the Card
    :return: The link HTML
    """
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
            "url": "https://starcitygames.com/search/?{}".format(
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


def ajax_search_result_prices(
    request: WSGIRequest, card_printing_id: int
) -> HttpResponse:
    """
    Gets the prices HTML of a Card
    :param request: The user's request
    :param card_printing_id: The ID of the CardPrinting
    :return: The price HTML
    """
    printing = CardPrinting.objects.get(pk=card_printing_id)
    price_dict = defaultdict(list)
    for price in printing.prices.all():
        price_dict[price.price_type].append(price)

    results = {}
    for price_type, prices in price_dict.items():
        results[price_type] = {
            "prices": sorted(prices, key=lambda x: x.date, reverse=True),
            "name": prices[0].get_price_type_display(),
        }

    return render(
        request, "website/results/search_result_prices.html", {"prices": results}
    )


def ajax_search_result_price_json(
    request: WSGIRequest, card_printing_id: int
) -> JsonResponse:
    printing = CardPrinting.objects.get(pk=card_printing_id)
    prices = printing.prices.order_by("date").all()
    result = {
        price_type: {
            "label": price_type,
            "currency": "tickets" if price_type.startswith("mtgo") else "dollars",
            "prices": [
                {"date": price.date.isoformat(), "value": price.price}
                for price in prices.all()
                if price.price_type == price_type
            ],
        }
        for price_type in set(price.price_type for price in prices.all())
    }
    return JsonResponse(result)


def get_page_number(request: WSGIRequest) -> int:
    """
    Gets the page number of a given request
    :param request: The request to get the page from
    :return: The page number
    """
    try:
        return int(request.GET.get("page"))
    except (TypeError, ValueError):
        return 1


def get_unused_cards(user: User):
    """
    Gets all cards that the given user has never used in a deck
    :param user: The user to get the unused cards for
    :return:
    """
    users_deck_cards = Card.objects.filter(
        deck_cards__deck__owner=user,
        deck_cards__deck__is_prototype=False,
        deck_cards__board="main",
    )
    users_cards = (
        Card.objects.filter(
            printings__printed_languages__physical_cards__ownerships__owner=user,
            is_token=False,
        )
        .exclude(side="b")
        .exclude(side="c")
        .distinct()
    )
    if not hasattr(user, "userprops"):
        UserProps.add_to_user(user)

    rand = random.Random(user.userprops.unused_cards_seed)
    unused_cards = list(users_cards.exclude(id__in=users_deck_cards).order_by("id"))
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:10]
    unused_cards = [
        {
            "card": card,
            "preferred_printing": card.printings.filter(
                printed_languages__physical_cards__ownerships__owner=user
            )
            .order_by("set__release_date")
            .last(),
        }
        for card in unused_cards
    ]
    return unused_cards


def get_unused_commanders(user: User):
    users_deck_cards = Card.objects.filter(
        deck_cards__deck__owner=user,
        deck_cards__deck__is_prototype=False,
        deck_cards__is_commander=True,
    )
    users_commanders = (
        Card.objects.filter(
            printings__printed_languages__physical_cards__ownerships__owner=user,
            is_token=False,
        )
        .filter(
            (Q(type__contains="Legend") & Q(type__contains="Creature"))
            | Q(rules_text__contains="can be your commander")
        )
        .exclude(side="b")
        .exclude(side="c")
        .distinct()
    )
    rand = random.Random(user.userprops.unused_cards_seed)
    unused_cards = list(
        users_commanders.exclude(id__in=users_deck_cards).order_by("id")
    )
    rand.shuffle(unused_cards)
    unused_cards = unused_cards[:10]
    unused_cards = [
        {
            "card": card,
            "preferred_printing": card.printings.filter(
                printed_languages__physical_cards__ownerships__owner=user
            )
            .order_by("set__release_date")
            .last(),
        }
        for card in unused_cards
    ]
    return unused_cards


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
    # for deck in Deck.objects.filter(owner=request.user, is_prototype=False):
    #     try:
    #         deck.validate_format()
    #     except ValidationError as error:
    #         deck_warnings.append({"deck": deck, "msg": error.message})

    return render(
        request,
        "website/decks/deck_stats.html",
        {
            "unused_cards": get_unused_cards(request.user),
            "unused_commanders": get_unused_commanders(request.user),
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
    page_size = 15
    users_decks = Deck.objects.filter(owner=request.user).order_by(
        "-is_prototype", "-date_created", "-last_modified", "-id"
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
    return render(request, "website/decks/deck_view.html", {"deck": deck})


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
    return render(request, "website/decks/deck_edit.html", {"deck_form": deck_form})


def deck_create(request: WSGIRequest) -> HttpResponse:
    """
    Deck creation form
    :param request: The user's request
    :return: Either the deck page, or the deck view page, depending on errors and settings
    """
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
        return JsonResponse({"error": "Deck not found"})

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


def get_colour_info() -> Dict[int, Dict[str, Any]]:
    """
    Gets information about all colours
    :return: The colour information as a dict
    """
    return {
        colour.symbol: {
            "name": colour.name,
            "symbol": colour.symbol,
            "display_order": colour.display_order,
            "chart_colour": colour.chart_colour,
        }
        for colour in Colour.objects.all().order_by("display_order")
    }
