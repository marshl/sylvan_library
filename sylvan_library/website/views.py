from django.shortcuts import render
from django.http import HttpResponse
from cards.models import Card, Set
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
import random
import logging

from cards.models import *
from cardsearch.card_search import *
from cardsearch.simplesearch import *
from cardsearch.fieldsearch import *
from .forms import *

logger = logging.getLogger('django')


def index(request):
    context = {'sets': Set.objects.all()}
    return render(request, 'website/index.html', context)


def card_detail(request, card_id):
    card = get_object_or_404(Card, pk=card_id)
    context = {'card': card}
    return render(request, 'website/card_detail.html', context)


def set_detail(request, set_code):
    set_obj = get_object_or_404(Set, code=set_code)
    context = {'set': set_obj}
    return render(request, 'website/set.html', context)


def usercard_form(request):
    return render(request, 'website/usercard_form.html')


def add_card(request, printlang_id):
    cardlang = CardPrintingLanguage.objects.get(id=printlang_id)
    phys = cardlang.physicalcardlink_set.first().physical_card

    uoc = UserOwnedCard(physical_card=phys, owner=request.user, count=1)
    uoc.save()

    return render(request, 'website/add_card.html')


def random_card(request):
    card = random.choice(Card.objects.all())

    return HttpResponseRedirect('../card/{0}'.format(card.id))


def simple_search(request):
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

        results = search.get_query()[:10]

    return render(request, 'website/simple_search.html',
                  {'form': form, 'results': results})


def advanced_search(request):
    return 'advanced search'


def search_results(request):
    return 'search results'
