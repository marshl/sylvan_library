"""
Urls for the website app
"""
from django.urls import path

from sylvan_library.website import views

# pylint: disable=invalid-name
app_name = "website"
urlpatterns = [
    path("", views.index, name="index"),
    path("name_search/", views.name_search, name="name_search"),
    path("set_list/", views.set_list, name="set_list"),
    path(
        "ajax/search_result_details/<int:printing_id>/",
        views.ajax_search_result_details,
        name="ajax_search_result_details",
    ),
    path(
        "ajax/search_result_rulings/<int:card_id>/",
        views.ajax_search_result_rulings,
        name="ajax_search_result_rulings",
    ),
    path(
        "ajax/search_result_languages/<int:printing_id>/",
        views.ajax_search_result_languages,
        name="ajax_search_result_languages",
    ),
    path(
        "ajax/search_result_ownership/<int:card_id>/",
        views.ajax_search_result_ownership,
        name="ajax_search_result_ownership",
    ),
    path(
        "ajax/search_result_add/<int:printing_id>/",
        views.ajax_search_result_add,
        name="ajax_search_result_add",
    ),
    path(
        "ajax/card_printing_image/<int:printing_id>/",
        views.ajax_card_printing_image,
        name="ajax_card_printing_image",
    ),
    path(
        "ajax/change_card_ownership",
        views.ajax_change_card_ownership,
        name="ajax_change_card_ownership",
    ),
    path(
        "ajax/ownership_summary/<int:card_id>/",
        views.ajax_ownership_summary,
        name="ajax_ownership_summary",
    ),
    path(
        "ajax/search_result_set_summary/<int:printing_id>/",
        views.ajax_search_result_set_summary,
        name="ajax_search_result_set_summary",
    ),
    path(
        "ajax/search_result_decks/<int:card_id>/",
        views.ajax_search_result_decks,
        name="ajax_search_result_decks",
    ),
    path(
        "ajax/search_result_links/<int:card_id>/",
        views.ajax_search_result_links,
        name="ajax_search_result_links",
    ),
    path(
        "ajax/search_result_prices/<int:card_printing_id>/",
        views.ajax_search_result_prices,
        name="ajax_search_result_prices",
    ),
    path(
        "ajax/search_result_price_json/<int:card_printing_id>/",
        views.ajax_search_result_price_json,
        name="ajax_search_result_price_json",
    ),
    # Decks
    path("decks/card/", views.deck_card_search, name="deck_card_search"),
    path("decks/", views.deck_list, name="decks"),
    path("decks/create/", views.deck_create, name="create_deck"),
    path("decks/stats", views.deck_stats, name="deck_stats"),
    path("decks/<int:deck_id>/", views.deck_view, name="deck_view"),
    path("decks/<int:deck_id>/edit", views.deck_edit, name="deck_edit"),
    path(
        "decks/<int:deck_id>/colour_weights",
        views.deck_colour_weights,
        name="deck_colour_weights",
    ),
    path(
        "decks/change_unused_decks",
        views.change_unused_decks,
        name="change_unused_decks",
    ),
]
