"""
Card search views
"""

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from sylvan_library.cardsearch.parameters.base_parameters import QueryContext
from sylvan_library.cardsearch.parse_search import ParseSearch
from sylvan_library.cardsearch.serializers import SearchResultSerializer


class CardSearchView(ListAPIView):
    """
    An API view for searching for cards
    """

    permission_classes = [AllowAny]
    serializer_class = SearchResultSerializer

    def _build_search(self) -> ParseSearch:
        user = self.request.user if self.request.user.is_authenticated else None
        query = self.request.query_params.get("q", "")
        search = ParseSearch(query, user)
        search.build_parameters()
        query_context = QueryContext(
            user=user,
            search_mode=search.root_parameter.get_default_search_context(),
        )
        search.root_parameter.validate(query_context)
        search.search(query_context)
        return search

    def get_queryset(self):
        return self._build_search().results

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
