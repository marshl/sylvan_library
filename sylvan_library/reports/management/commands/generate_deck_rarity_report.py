"""
Module for the verify_database command
"""
from django.core.management.base import BaseCommand
from cards.models import (
    Deck,
    User,
)

import os
import pandas as pd
import seaborn as sns


class Command(BaseCommand):
    """

    """
    help = 'Verifies that database update was successful'

    def __init__(self):
        self.rarities = ['C', 'U', 'R', 'M']
        super().__init__()

    def handle(self, *args, **options):
        owner = User.objects.get(username='Test')
        decks = Deck.objects.filter(owner=owner).prefetch_related('cards__card__printings__set')
        dates = [d['date_created'] for d in decks.values('date_created').distinct()]
        rows = []
        for dt in dates:
            date_decks = decks.filter(date_created=dt)
            row = [0] * len(self.rarities)
            for deck in date_decks:
                r = self.get_deck_rarity_ratios(deck)
                for idx, rarity in enumerate(self.rarities):
                    row[idx] += r[rarity]

            row = [x / len(date_decks) for x in row]
            rows.append(row)

        sns.set(style="whitegrid")

        sns.set(rc={'figure.figsize': (12, 8)})
        sns.set(color_codes=True)

        date_index = pd.DatetimeIndex(dates)
        data = pd.DataFrame(rows, index=date_index, columns=self.rarities)
        data = data.resample('90D').mean()
        data = data.interpolate(method='cubic')

        plt = sns.lineplot(data=data, palette={'C': '#0E0C0C', 'U': '#8A8D91','R': '#C1A15B','M': '#EC7802',}, linewidth=1.5, hue='A')
        fig = plt.figure

        fig.savefig(os.path.join('reports', 'output', 'test.png'))

    def get_deck_rarity_ratios(self, deck: Deck) -> dict:
        counts = {r: 0 for r in self.rarities}
        total_count = 0
        for deck_card in deck.cards.all():
            #if 'Land' in deck_card.card.type:
            #    continue
            closest_printing = deck_card.card.printings.first()
            for printing in deck_card.card.printings.all():
                if abs(deck.date_created - printing.set.release_date) \
                        < abs(deck.date_created - closest_printing.set.release_date):
                    closest_printing = printing

            counts[closest_printing.rarity.symbol] += deck_card.count
            total_count += deck_card.count

        ratios = {key: value / total_count for key, value in counts.items()}
        return ratios
