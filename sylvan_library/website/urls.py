from django.conf.urls import url

from website import views

app_name = 'website'
urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^card/(?P<card_id>[0-9]+)/$', views.card_detail, name='card_detail'),
    url(r'^set/(?P<set_code>[a-zA-Z0-9]+)/$', views.set_detail, name='set_detail'),
    url(r'^add_card/(?P<printlang_id>[0-9]+)/$', views.add_card, name='add_card'),
    url(r'^usercard_form/$', views.usercard_form, name='usercard_form'),
    url(r'^random_card/$', views.random_card, name='random_card'),
    url(r'^simple_search/$', views.simple_search, name='simple_search'),
    url(r'^advanced_search/$', views.advanced_search, name='advanced_search'),
]
