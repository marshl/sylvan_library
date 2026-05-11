"""
URLs
"""

from django.urls import path, include
from rest_framework import routers

from sylvan_library.cards import views

router = routers.DefaultRouter()
router.register(r"card", views.CardViewSet)
router.register(r"set", views.SetViewSet)
router.register(r"all-sets", views.AllSetsViewSet, basename="all-sets")
router.register(r"deck", views.DeckViewSet)

urlpatterns = [path("", include(router.urls))]
