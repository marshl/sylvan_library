"""
Module for all website views
"""
import logging
import random

from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    PhysicalCard,
    Set,
    UserCardChange,
    UserOwnedCard,
)
from website.forms import FieldSearchForm, NameSearchForm, ChangeCardOwnershipForm

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

    return HttpResponseRedirect(f'../card/{card.id}')


def name_search(request) -> HttpResponse:
    """
    The view for when a user searches by card name
    :param request: The user's request
    :return: The HTTP Response
    """
    name_form = NameSearchForm(request.GET)
    search_form = FieldSearchForm()
    search = name_form.get_search()
    return render(request, 'website/simple_search.html', {
        'name_form': name_form, 'form': search_form, 'results': search.results,
        'result_count': search.paginator.count,
        'page': search.page,
        'page_buttons': search.get_page_buttons(name_form.get_page_number(), 3)})


def simple_search(request) -> HttpResponse:
    """
    The simple search form
    :param request: The user's request
    :return: The HTTP Response
    """
    form = FieldSearchForm(request.GET)
    search = form.get_field_search()

    return render(request, 'website/simple_search.html', {
        'form': form, 'results': search.results,
        'result_count': search.paginator.count,
        'page': search.page,
        'page_buttons': search.get_page_buttons(form.get_page_number(), 3)})


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


def ajax_search_result_rulings(request, card_id: int) -> HttpResponse:
    card = Card.objects.get(id=card_id)
    return render(request, 'website/search_result_rulings.html', {'card': card})


def ajax_search_result_languages(request, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, 'website/search_result_languages.html',
                  {'printing': printing})


def ajax_card_printing_image(request, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, 'website/card_image.html',
                  {'printing': printing})


def ajax_search_result_add(request, printing_id: int) -> HttpResponse:
    printing = CardPrinting.objects.get(id=printing_id)
    form = ChangeCardOwnershipForm(printing)
    return render(request, 'website/search_result_add.html',
                  {'form': form})


def ajax_search_result_ownership(request, card_id: int) -> HttpResponse:
    card = Card.objects.get(id=card_id)
    ownerships = UserOwnedCard.objects.filter(owner_id=request.user.id) \
        .filter(physical_card__printed_languages__card_printing__card__id=card_id) \
        .order_by('physical_card__printed_languages__card_printing__set__release_date')
    changes = UserCardChange.objects.filter(owner_id=request.user.id) \
        .filter(physical_card__printed_languages__card_printing__card__id=card_id) \
        .order_by('date')
    return render(request, 'website/search_result_ownership.html',
                  {'card': card, 'ownerships': ownerships, 'changes': changes})


def ajax_change_card_ownership(request):
    if not request.POST.get('count'):
        return JsonResponse({'result': False, 'error': 'Invalid count'})

    try:
        with transaction.atomic():
            change_count = int(request.POST.get('count'))
            physical_card_id = int(request.POST.get('printed_language'))
            physical_card = PhysicalCard.objects.get(id=physical_card_id)
            physical_card.apply_user_change(change_count, request.user)
            return JsonResponse({'result': True})
    except PhysicalCard.DoesNotExist as ex:
        return JsonResponse({'result': False, 'error': str(ex)})


def ajax_ownership_summary(request, card_id: int):
    card = Card.objects.get(id=card_id)
    return render(request, 'website/ownership_summary.html', {
        'card': card,
    })


def ajax_search_result_set_summary(request, printing_id: int):
    printing = CardPrinting.objects.get(id=printing_id)
    return render(request, 'website/search_result_sets.html', {
        'card': printing.card,
        'selected_printing': printing,
    })
