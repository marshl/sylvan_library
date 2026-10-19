"""sylvan_library URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from sylvan_library.frontend import views as frontend_views

urlpatterns = [
    # Django and API routes should come first
    path("api/cards/", include("sylvan_library.cards.urls")),
    path("api/search/", include("sylvan_library.cardsearch.urls")),
    path("api/me/", frontend_views.CurrentUserView.as_view(), name="current_user"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

if settings.DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))

# Every other path is a page in the React app, which does its own routing. Unknown
# API, admin and static paths are left to 404 rather than get the app's HTML.
# This should be the last pattern in the list.
urlpatterns.append(
    re_path(
        r"^(?!api/|api-auth/|admin/|static/|__debug__/).*$",
        frontend_views.index,
        name="react-app",
    )
)
