"""
Views
"""

from django.db.models import Prefetch
from rest_framework import viewsets, mixins

from sylvan_library.cards.models.card import Card, CardPrinting
from sylvan_library.cards.models.sets import Set
from sylvan_library.cards.serializers import (
    CardSerializer,
    card_prefetches,
    SetSerializer,
    CardPrintingDetailsSerializer,
)


# pylint: disable=too-many-ancestors
class CardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Card.objects.order_by("id")
    serializer_class = CardSerializer

    def get_queryset(self):
        user = self.request.user if self.request.user.is_authenticated else None
        return super().get_queryset().prefetch_related(*card_prefetches(user))


class SetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Set model
    """

    queryset = Set.objects.filter().order_by("-release_date")
    serializer_class = SetSerializer


class AllSetsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ALL sets, grouped by parent set
    """

    queryset = (
        Set.objects.filter(parent_set__isnull=True)
        .prefetch_related(
            *(
                Prefetch(lookup, queryset=Set.objects.order_by("-release_date"))
                for lookup in (
                    "child_sets",
                    "child_sets__child_sets",
                    "child_sets__child_sets__child_sets",
                )
            )
        )
        .order_by("-release_date")
    )
    serializer_class = SetSerializer
    pagination_class = None


class CardPrintingDetailsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Read-only endpoint that surfaces the data for the search-result Details tab.
    """

    queryset = CardPrinting.objects.select_related("set", "card").prefetch_related(
        "face_printings", "card__legalities__format"
    )
    serializer_class = CardPrintingDetailsSerializer
