from django.shortcuts import render
from django.http import HttpResponse
from cards.models import Card, Set
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
import random

from cards.models import *
from cardsearch.card_search import *
from cardsearch.simplesearch import *


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
    results = []

    if request.GET.get('card_name'):
        search = SimpleSearch()
        search.text = request.GET.get('card_name')
        search.include_name = True
        results = search.get_query()

    return render(request, 'website/simple_search.html',
                  {'card_name': request.GET.get('card_name'), 'results': results})


def advanced_search(request):
    return 'advanced search'


def search_results(request):
    return 'search results'
