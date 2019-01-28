"""
Module for all website views
"""
import logging
import random

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Set,
    UserOwnedCard,
)
from website.forms import SearchForm
from cardsearch.fieldsearch import FieldSearch

logger = logging.getLogger('django')


def index(request) -> HttpResponse:
    """
    The index page of this site
    :param request: The
    :return:
    """
    context = {'sets': Set.objects.all()}
    return render(request, 'website/index.html', context)


def card_detail(request, card_id) -> HttpResponse:
    """

    :param request:
    :param card_id:
    :return:
    """
    card = get_object_or_404(Card, pk=card_id)
    context = {'card': card}
    return render(request, 'website/card_detail.html', context)


def set_detail(request, set_code) -> HttpResponse:
    """
    The
    :param request:
    :param set_code:
    :return:
    """
    set_obj = get_object_or_404(Set, code=set_code)
    context = {'set': set_obj}
    return render(request, 'website/set.html', context)


def usercard_form(request) -> HttpResponse:
    """
    The form where a user can update their list of cards
    :param request: The user's request
    :return: The HTTP response
    """
    return render(request, 'website/usercard_form.html')


def add_card(request, printlang_id) -> HttpResponse:
    """
    Adds a card to the user's cards
    :param request: The user's request
    :param printlang_id: The CardPrintingLanguage ID
    :return: The HTTP response
    """
    cardlang = CardPrintingLanguage.objects.get(id=printlang_id)
    phys = cardlang.physicalcardlink_set.first().physical_card

    uoc = UserOwnedCard(physical_card=phys, owner=request.user, count=1)
    uoc.save()

    return render(request, 'website/add_card.html')


# pylint: disable=unused-argument
def random_card(request) -> HttpResponse:
    """
    Gets a random card and redirects the user to that page
    :param request: The user's request
    :return: The HTTP response
    """
    card = random.choice(Card.objects.all())

    return HttpResponseRedirect('../card/{0}'.format(card.id))


def simple_search(request) -> HttpResponse:
    """
    The simple search form
    :param request: The user's request
    :return: The HTTP Response
    """
    form = SearchForm(request.GET)
    results = []
    if form.is_valid():
        search = FieldSearch()
        search.card_name = form.data.get('card_name')
        search.rules_text = form.data.get('rules_text')

        if form.data.get('cmc'):
            logger.info('wasd')
            search.cmc = int(form.data.get('cmc'))
            search.cmc_operator = form.data.get('cmc_operator')

        if form.data.get('colour_white'):
            search.colours.append(Card.colour_flags.white)
        if form.data.get('colour_blue'):
            search.colours.append(Card.colour_flags.blue)
        if form.data.get('colour_black'):
            search.colours.append(Card.colour_flags.black)
        if form.data.get('colour_red'):
            search.colours.append(Card.colour_flags.red)
        if form.data.get('colour_green'):
            search.colours.append(Card.colour_flags.green)

        search.exclude_unselected_colours = bool(form.data.get('exclude_colours'))
        search.match_colours_exactly = bool(form.data.get('match_colours'))

        if form.data.get('colourid_white'):
            search.colour_identities.append(Card.colour_flags.white)
        if form.data.get('colourid_blue'):
            search.colour_identities.append(Card.colour_flags.blue)
        if form.data.get('colourid_black'):
            search.colour_identities.append(Card.colour_flags.black)
        if form.data.get('colourid_red'):
            search.colour_identities.append(Card.colour_flags.red)
        if form.data.get('colourid_green'):
            search.colour_identities.append(Card.colour_flags.green)
        if form.data.get('colourid_colourless'):
            search.colour_identities.append(Card.colour_flags.colourless)

        search.exclude_unselected_colour_identities = bool(form.data.get('exclude_colours'))
        search.match_colour_identities_exactly = bool(form.data.get('match_colours'))

        search.build_parameters()
        results = search.get_results()

    return render(request, 'website/simple_search.html',
                  {'form': form, 'results': results})


# pylint: disable=unused-argument, missing-docstring
def advanced_search(request):
    return 'advanced search'


# pylint: disable=unused-argument, missing-docstring
def search_results(request):
    return 'search results'


def ajax_search_result_details(request, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, 'website/search_result_details.html',
                  {'printing': printing})
