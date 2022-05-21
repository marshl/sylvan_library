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
    links = [
        {
            "name": "Search on Channel Fireball",
            "url": f"https://store.channelfireball.com/products/search?{urllib.parse.urlencode({'q': card.name})}",
        },
        {
            "name": "TCGPlayer Decks",
            "url": f"https://decks.tcgplayer.com/magic/deck/search?{urllib.parse.urlencode({'contains': card.name, 'page': 1})}",
        },
        {
            "name": "Card Analysis on EDHREC",
            "url": f"https://edhrec.com/route/?{urllib.parse.urlencode({'cc': card.faces.first().name})}",
        },
        {
            "name": "Search on DeckStats",
            "url": f"https://deckstats.net/decks/search/?{urllib.parse.urlencode({'search_cards[]': card.name})}",
        },
        {
            "name": "MTGTop8 decks",
            "url": "https://mtgtop8.com/search?{}".format(
                urllib.parse.urlencode(
                    {"MD_check": 1, "SB_check": 1, "cards": card.faces.first().name}
                )
            ),
        },
        {
            "name": "Search on Starcity Games",
            "url": f"https://starcitygames.com/search/?{urllib.parse.urlencode({'search_query': card.name})}",
        },
        {
            "name": "Search on Scryfall",
            "url": f"https://scryfall.com/search?q={urllib.parse.urlencode({'name': card.name})}",
        },
        {
            "name": "Card Kingdom",
            "url": "https://www.cardkingdom.com/catalog/search?{}".format(
                urllib.parse.urlencode(
                    {
                        "search": "header",
                        "filter[name]": get_website_card_filter(card, "Card Kingdom"),
                    }
                )
            ),
        },
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




def get_website_card_filter(card: Card, website: str) -> str:
    """
    Gets the website specific filter used to query for a card.
    :param card: The card to search for
    :param website: The website the link is for
    :return: The filter string used for that website
    """
    if website == "Card Kingdom":
        if not card.is_token:
            if card.layout in ("aftermath", "split"):
                face_names = [f.name for f in card.faces.all()]
                return " // ".join(face_names)
            return card.faces.first().name
        if card.faces.filter(types__name="Emblem").exists():
            return f'Emblem ({card.name.replace(" Emblem", "")})'
        return f"{card.name} token"
    return ""



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
