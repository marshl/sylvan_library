"""
Urls for the website app
"""
from django.urls import path

from website import views

# pylint: disable=invalid-name
app_name = 'website'
urlpatterns = [
    path(r'^$', views.index, name='index'),

    path('card/<int:card_id>/', views.card_detail, name='card_detail'),
    path('set/<str:set_code>/', views.set_detail, name='set_detail'),
    path('add_card/<int:printlang_id>/', views.add_card, name='add_card'),
    path('usercard_form/', views.usercard_form, name='usercard_form'),
    path('random_card/', views.random_card, name='random_card'),
    path('simple_search/', views.simple_search, name='simple_search'),
    path('advanced_search/', views.advanced_search, name='advanced_search'),
    path('ajax/search_result_details/<int:printing_id>/', views.ajax_search_result_details,
         name='ajax_search_result_details'),
]
