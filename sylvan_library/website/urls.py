"""
Urls for the website app
"""
from django.urls import path

from website import views

# pylint: disable=invalid-name
app_name = 'website'
urlpatterns = [
    path('', views.index, name='index'),

    path('card/<int:card_id>/', views.card_detail, name='card_detail'),
    path('set/<str:set_code>/', views.set_detail, name='set_detail'),
    path('add_card/<int:printlang_id>/', views.add_card, name='add_card'),
    path('usercard_form/', views.usercard_form, name='usercard_form'),
    path('random_card/', views.random_card, name='random_card'),
    path('simple_search/', views.simple_search, name='simple_search'),
    path('name_search/', views.name_search, name='name_search'),
    path('advanced_search/', views.advanced_search, name='advanced_search'),
    path('ajax/search_result_details/<int:printing_id>/', views.ajax_search_result_details,
         name='ajax_search_result_details'),
    path('ajax/search_result_rulings/<int:card_id>/', views.ajax_search_result_rulings,
         name='ajax_search_result_rulings'),
    path('ajax/search_result_languages/<int:printing_id>/', views.ajax_search_result_languages,
         name='ajax_search_result_languages'),
    path('ajax/search_result_ownership/<int:card_id>/', views.ajax_search_result_ownership,
         name='ajax_search_result_ownership'),
    path('ajax/search_result_add/<int:printing_id>/', views.ajax_search_result_add,
         name='ajax_search_result_add'),
    path('ajax/card_printing_image/<int:printing_id>/', views.ajax_card_printing_image,
         name='ajax_card_printing_image'),
    path('ajax/change_card_ownership', views.ajax_change_card_ownership,
         name='ajax_change_card_ownership'),
    path('ajax/ownership_summary/<int:card_id>/', views.ajax_ownership_summary,
         name='ajax_ownership_summary'),
    path('ajax/search_result_set_summary/<int:printing_id>/', views.ajax_search_result_set_summary,
         name='ajax_search_result_set_summary'),

    # Decks
    path('decks/card/', views.deck_card_search, name='deck_card_search'),
    path('decks/', views.decks, name='decks'),
    path('decks/create/', views.create_deck, name='create_deck'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
]
