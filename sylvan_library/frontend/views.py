from django.conf import settings
from django.shortcuts import render


def index(request):
    print(settings.DEBUG)
    return render(request, "frontend/index.html", context={"debug": settings.DEBUG})
