from django.shortcuts import render
from django.http import HttpResponse
from spellbook.models import Card, Set
from django.shortcuts import get_object_or_404


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def card_detail(request, card_id):
    card = get_object_or_404(Card, pk=card_id)
    context = {'card': card}
    return render(request, 'spellbook/card_detail.html', context)


def set_detail(request, set_code):

    set_obj = get_object_or_404(Set, code=set_code)
    context = {'set': set_obj}
    return render(request, 'spellbook/set.html', context)
