from django.conf.urls import url

from . import views

app_name = 'spellbook'
urlpatterns = [
   url(r'^$', views.index, name='index'),
   
   url(r'^card/(?P<card_id>[0-9]+)/$', views.card_detail, name='card_detail'),
   url(r'^set/(?P<set_code>[a-zA-Z0-9]+)/$', views.set_detail, name='set_detail'),
]