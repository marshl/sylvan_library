from cards.models import (
    Card,
    CardPrinting,
    Set,
)


class SearchResult:

    def __init__(self, card: Card, selected_printing: CardPrinting = None,
                 selected_set: Set = None):
        self.card = card
        self.selected_printing = selected_printing

        if self.card and selected_set and not self.selected_printing:
            self.selected_printing = self.card.printings.filter(set=selected_set).first()

        if self.card and not self.selected_printing:
            self.selected_printing = self.card.printings.order_by('release_date').last()

        assert self.selected_printing is None or self.card is None \
               or self.selected_printing in self.card.printings.all()
