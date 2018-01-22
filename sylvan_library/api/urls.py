from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'cards', views.CardViewSet)

# Wire up our API using automatic URL routing
# Additionally, we include login URLs for the browsable API
urlpatterns = [
    url(r'^cards/$', views.card_list),
    url(r'^cards/(?P<pk>[0-9]+)$', views.card_detail),
]

urlpatterns = format_suffix_patterns(urlpatterns)