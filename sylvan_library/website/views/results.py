import logging
import urllib.parse
import urllib.request

from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from cards.models.card import (
    CardPrinting,
    Card,
    UserOwnedCard,
    CardLocalisation,
    UserCardChange,
)
from cards.models.decks import DeckCard
from cards.models.language import Language
from website.forms import (
    ChangeCardOwnershipForm,
)
from website.views.utils import (
    TCGPlayerLink,
    EDHRecLink,
    DeckStatsLink,
    MTGTop8Link,
    ScryfallLink,
    CardKingdomLink,
    StarCityGamesLink,
    ChannelFireballLink,
)

logger = logging.getLogger("django")


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
        .filter(card_localisation__card_printing__card__id=card_id)
        .order_by("card_localisation__card_printing__set__release_date")
    )
    changes = (
        UserCardChange.objects.filter(owner=request.user)
        .filter(card_localisation__card_printing__card__id=card_id)
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
            localisation_id = int(request.POST["localisation"])
            localisation = CardLocalisation.objects.get(pk=localisation_id)
            localisation.apply_user_change(change_count, request.user)
            return JsonResponse({"result": True})
    except CardLocalisation.DoesNotExist as ex:
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
    printing = CardPrinting.objects.prefetch_related(
        "card__printings__rarity",
        "card__printings__localisations__ownerships",
        "card__printings__localisations__language",
        "card__printings__localisations__localised_faces__image",
        "card__printings__face_printings__localised_faces__image",
        "card__printings__face_printings__localised_faces__localisation",
        "card__printings__set",
        "card__printings__rarity",
    ).get(id=printing_id)

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
        .filter(card=card)
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
    card: Card = Card.objects.get(pk=card_id)
    link_builders = [
        ChannelFireballLink(),
        TCGPlayerLink(),
        EDHRecLink(),
        DeckStatsLink(),
        MTGTop8Link(),
        StarCityGamesLink(),
        ScryfallLink(),
        CardKingdomLink(),
    ]

    links = [
        link_builder.build_link(card) for link_builder in link_builders
    ]

    localisation = (
        CardLocalisation.objects.filter(card_printing__card=card)
        .filter(multiverse_id__isnull=False)
        .filter(language=Language.english())
        .order_by("card_printing__set__release_date")
        .last()
    )
    if localisation:
        links.insert(
            0,
            {
                "name": "View on Gatherer",
                "url": f"https://gatherer.wizards.com/Pages/Card/Details.aspx?{urllib.parse.urlencode({'multiverseid': localisation.multiverse_id})}",
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
    return render(
        request, "website/results/search_result_prices.html", {"printing": printing}
    )


def ajax_search_result_price_json(
    request: WSGIRequest, card_printing_id: int
) -> JsonResponse:
    """
    Gets the pricing data for the given search result
    :param request: The users request
    :param card_printing_id: The ID of the CardPrinting
    :return: The pricing data for the printing
    """
    printing = CardPrinting.objects.get(pk=card_printing_id)
    prices = list(printing.prices.order_by("date").all())

    result = {
        "paper": {
            "label": "paper",
            "currency": "dollars",
            "prices": [
                {"date": price.date.isoformat(), "value": price.paper_value}
                for price in prices
                if price.paper_value
            ],
        }
    }
    return JsonResponse(result)
