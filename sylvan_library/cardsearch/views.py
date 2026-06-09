"""
Card search views
"""
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from sylvan_library.cardsearch.base_search import SearchResult
from sylvan_library.cardsearch.parse_search import ParseSearch
from sylvan_library.cardsearch.serializers import SearchResultSerializer


class CardSearchView(ListAPIView):
    """
    An API view for searching for cards
    """

    serializer_class = SearchResultSerializer

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        search = ParseSearch(query)
        search.search()
        return search.results

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
