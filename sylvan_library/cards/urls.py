"""
URLs
"""

from django.urls import path, include
from rest_framework import routers

from sylvan_library.cards import deck_views, result_views, views

router = routers.DefaultRouter()
router.register(r"card", views.CardViewSet)
router.register(r"set", views.SetViewSet)
router.register(r"all-sets", views.AllSetsViewSet, basename="all-sets")
router.register(
    r"printing-details",
    views.CardPrintingDetailsViewSet,
    basename="printing-details",
)
router.register(r"deck", deck_views.DeckViewSet, basename="deck")

urlpatterns = [
    path("card/<int:card_id>/rulings/", result_views.card_rulings),
    path("card/<int:card_id>/ownership/", result_views.card_ownership),
    path("card/<int:card_id>/decks/", result_views.card_decks),
    path("card/<int:card_id>/links/", result_views.card_links),
    path("printing/<int:printing_id>/languages/", result_views.printing_languages),
    path("printing/<int:printing_id>/prices/", result_views.printing_prices),
    path("ownership-changes/", result_views.change_card_ownership),
    path("deck-options/", deck_views.deck_options),
    path("card-names/", deck_views.card_names),
    path("deck-stats/", deck_views.deck_stats),
    path("deck-stats/reroll/", deck_views.reroll_deck_stats),
    path("", include(router.urls)),
]
