from django.conf.urls import url

from spellbook import views

app_name = 'spellbook'
urlpatterns = [
   url(r'^$', views.index, name='index'),
]
