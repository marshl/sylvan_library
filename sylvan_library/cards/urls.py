"""
URLs
"""

from django.urls import path, include
from rest_framework import routers

from cards import views

router = routers.DefaultRouter()
router.register(r"card", views.CardViewSet)

urlpatterns = [path("", include(router.urls))]
