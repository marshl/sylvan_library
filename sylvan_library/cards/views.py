from rest_framework import viewsets

from cards.models import Card
from cards.serializers import CardSerializer


class CardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Card.objects.all()
    serializer_class = CardSerializer
    # permission_classes = [permissions.IsAuthenticated]
