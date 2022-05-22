"""
Module for all website views
"""

from website.views.decks import (
    deck_card_search,
    deck_list,
    deck_create,
    deck_stats,
    deck_view,
    deck_edit,
    deck_colour_weights,
    change_unused_decks,
)
from website.views.index import index
from website.views.results import (
    ajax_search_result_links,
    ajax_search_result_add,
    ajax_search_result_decks,
    ajax_search_result_details,
    ajax_search_result_languages,
    ajax_search_result_prices,
    ajax_search_result_ownership,
    ajax_ownership_summary,
    ajax_search_result_set_summary,
    ajax_search_result_rulings,
    ajax_search_result_price_json,
    ajax_change_card_ownership,
    ajax_card_printing_image,
)
from website.views.search import name_search
from website.views.sets import set_list
