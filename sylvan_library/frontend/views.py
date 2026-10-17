from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache


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
