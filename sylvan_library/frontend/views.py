from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


BUILT_INDEX = Path(__file__).resolve().parent / "static" / "react" / "index.html"

VITE_DEV_ORIGIN = "http://localhost:5173"


@never_cache
def index(request):
    if settings.DEBUG:
        # In dev, hand off to the Vite dev server which owns HMR and the
        # React Router entry graph.  Run `npm run dev` inside sylvan-react/.
        return HttpResponseRedirect(f"{VITE_DEV_ORIGIN}{request.get_full_path()}")

    try:
        html = BUILT_INDEX.read_text(encoding="utf-8")
    except FileNotFoundError:
        return HttpResponse(
            "React build not found. Run `npm run build` inside sylvan-react/.",
            status=503,
            content_type="text/plain",
        )
    return HttpResponse(html, content_type="text/html")


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    """
    Tells the React app who is logged in. This is the first request the app
    makes, so it also sets the csrftoken cookie that later POSTs need.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Returns the current user, or is_authenticated: false for anonymous users
        """
        user = request.user
        if not user.is_authenticated:
            return Response(
                {
                    "is_authenticated": False,
                    "username": None,
                    "email": None,
                    "date_joined": None,
                    "is_staff": False,
                }
            )
        return Response(
            {
                "is_authenticated": True,
                "username": user.get_username(),
                "email": user.email or None,
                "date_joined": user.date_joined.date(),
                "is_staff": user.is_staff,
            }
        )
