"""
URLs for the cardsearch app
"""

from django.urls import path

from sylvan_library.cardsearch import views

urlpatterns = [
    path("search/", views.CardSearchView.as_view(), name="card_search"),
]
