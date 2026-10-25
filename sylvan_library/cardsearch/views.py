"""
Card search views
"""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from sylvan_library.cardsearch.search import run_search
from sylvan_library.cardsearch.serializers import SearchResultSerializer

PAGE_SIZE = 25


class CardSearchView(APIView):
    """
    An API view for searching for cards
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Runs the search in the "q" param and returns one page of results
        """
        user = request.user if request.user.is_authenticated else None
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        outcome = run_search(request.query_params.get("q", ""), user, page, PAGE_SIZE)
        return Response(
            {
                "count": outcome.count,
                "page": outcome.page,
                "page_size": PAGE_SIZE,
                "num_pages": outcome.num_pages,
                "pretty_query_message": outcome.pretty_query,
                "error_message": outcome.error,
                "results": SearchResultSerializer(
                    outcome.results, many=True, context={"request": request}
                ).data,
            }
        )
