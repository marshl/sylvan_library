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

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.rarities = ['L', 'C', 'U', 'R', 'M']
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def handle(self, *args, **options):
        output_path = os.path.join('reports', 'output', 'deck_rarity_progression.png')
        if os.path.exists(output_path):
            os.remove(output_path)

        owner = User.objects.get(username='Test')
        decks = Deck.objects.filter(owner=owner).prefetch_related('cards__card__printings__set')
        dates = [d['date_created'] for d in decks.values('date_created').distinct()]
        rows = []
        for dt in dates:
            date_decks = decks.filter(date_created=dt)
            row = [0] * len(self.rarities)
            deck_count = 0
            for deck in date_decks:
                if sum(x.count for x in deck.cards.all()) < 60:
                    continue

                r = self.get_deck_rarity_ratios(deck)
                for idx, rarity in enumerate(self.rarities):
                    row[idx] += r[rarity]

                deck_count += 1

            if deck_count > 0:
                row = [x / deck_count for x in row]
                rows.append(row)

        sns.set(style="whitegrid")
        sns.set(rc={'figure.figsize': (10, 6)})
        sns.set(color_codes=True)

        date_index = pd.DatetimeIndex(dates)
        data = pd.DataFrame(rows, index=date_index, columns=self.rarities)
        data = data.resample('180D').mean()
        data = data.interpolate(method='cubic')
        palette = {'L': '#875438', 'C': '#0E0C0C', 'U': '#8A8D91', 'R': '#C1A15B', 'M': '#EC7802'}
        plt = sns.lineplot(data=data, palette=palette, linewidth=1.5, hue='A')
        plt.set(ylabel='Average Proportion of Deck')
        fig = plt.figure

        fig.savefig(output_path)

    def get_deck_rarity_ratios(self, deck: Deck) -> dict:
        counts = {r: 0 for r in self.rarities}
        total_count = 0
        for deck_card in deck.cards.all():
            if 'Basic' in deck_card.card.type:
                counts['L'] += deck_card.count
            else:
                closest_printing = None
                for printing in deck_card.card.printings.all():
                    if printing.set.type not in ['expansion', 'core', 'starter']:
                        continue
                    if closest_printing is None or \
                            abs(deck.date_created - printing.set.release_date) \
                            < abs(deck.date_created - closest_printing.set.release_date):
                        closest_printing = printing
                if not closest_printing:
                    raise Exception(f'Could not find a valid printing for {deck_card}')

                counts[closest_printing.rarity.symbol] += deck_card.count
            total_count += deck_card.count

        ratios = {key: value / total_count for key, value in counts.items()}
        return ratios
