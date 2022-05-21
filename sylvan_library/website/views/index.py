from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from cards.models.sets import Set


def index(request: WSGIRequest) -> HttpResponse:
    """
    The index page of this site
    :param request: The
    :return:
    """
    context = {"sets": Set.objects.all()}
    return render(request, "website/index.html", context)