"""
Card search views
"""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from sylvan_library.cardsearch.parameters.base_parameters import (
    QueryContext,
    QueryValidationError,
)
from sylvan_library.cardsearch.parse_search import ParseSearch
from sylvan_library.cardsearch.serializers import SearchResultSerializer

PAGE_SIZE = 25


class CardSearchView(APIView):
    """
    An API view for searching for cards.

    Pagination is done by ParseSearch itself (it needs the page before it can
    prefetch and pick the preferred printing), so this doesn't use DRF's
    paginator.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """
        Runs the search in the "q" param and returns one page of results
        """
        user = request.user if request.user.is_authenticated else None
        try:
            page_number = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page_number = 1

        search = ParseSearch(request.query_params.get("q", ""), user)
        search.build_parameters()
        query_context = QueryContext(
            user=user,
            search_mode=search.root_parameter.get_default_search_context(),
        )
        if not search.error_message:
            try:
                search.root_parameter.validate(query_context)
            except QueryValidationError as error:
                search.error_message = str(error)

        # A query that failed to parse or validate would otherwise search with
        # whatever is left of the parameter tree (often every card)
        if search.error_message:
            return Response(
                {
                    "count": 0,
                    "page": 1,
                    "page_size": PAGE_SIZE,
                    "num_pages": 1,
                    "pretty_query_message": None,
                    "error_message": search.error_message,
                    "results": [],
                }
            )

        search.search(query_context, page_number, PAGE_SIZE)
        return Response(
            {
                "count": search.paginator.count,
                "page": page_number,
                "page_size": PAGE_SIZE,
                "num_pages": search.paginator.num_pages,
                "pretty_query_message": search.get_pretty_str(query_context),
                "error_message": None,
                "results": SearchResultSerializer(
                    search.results, many=True, context={"request": request}
                ).data,
            }
        )
