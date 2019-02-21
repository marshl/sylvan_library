"""
Module for the verify_database command
"""

import os
import re
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from cards.models import (
    Card,
    Deck,
    DeckCard,
    User,
)

import json

from bs4 import BeautifulSoup
import requests


class Command(BaseCommand):
    """

    """
    help = 'Verifies that database update was successful'

    def __init__(self):
        self.base_uri = 'https://www.mtgtop8.com/'
        self.output_path = os.path.join('reports', 'output', 'parsed_decks.json')
        if not os.path.exists(self.output_path):
            with open(self.output_path, 'w') as json_file:
                json.dump({'uris': []}, json_file)

        with open(self.output_path) as json_file:
            self.parsed_deck_uris = json.load(json_file)['uris']

        super().__init__()

    def handle(self, *args, **options):
        worlds_uri = 'format?f=ST&meta=97'
        pro_tour_uri = 'format?f=ST&meta=91'
        grand_prix_uri = 'format?f=ST&meta=96'
        for uri in [worlds_uri, pro_tour_uri, grand_prix_uri]:
            self.parse_event_summary(self.base_uri + uri)

    def parse_event_summary(self, event_summary_uri):
        visited_pages = set()
        pages_to_visit = {1}
        while pages_to_visit:
            page = pages_to_visit.pop()
            visited_pages.add(page)
            print(f'Parsing event list {event_summary_uri} on page{page}')
            resp = requests.post(event_summary_uri, {'cp': page})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content)
            event_list = soup.select('table.Stable')[2]
            nav_buttons = soup.select('form[name="format_form"] .Nav_norm')
            for button in nav_buttons:
                button_page = int(button.text)
                if button_page not in visited_pages:
                    pages_to_visit.add(button_page)

            event_trs = event_list.find_all('tr', class_='hover_tr')
            for event in event_trs:
                link = event.find('a')
                href = link.attrs['href']
                self.parse_event(self.base_uri + href)

    def parse_event(self, event_uri):
        print(f'Parsing event {event_uri}')
        resp = requests.get(event_uri)
        resp.raise_for_status()

        self.parse_deck(event_uri)

        soup = BeautifulSoup(resp.text)
        deck_links = soup.select('div.hover_tr div.S14 a')
        for link in deck_links:
            href = link.attrs['href']
            self.parse_deck(self.base_uri + 'event' + href)

    def parse_deck(self, deck_uri):

        if deck_uri in self.parsed_deck_uris:
            print(f'Skipping deck {deck_uri}')
            return

        print(f'Parsing deck {deck_uri}')

        resp = requests.get(deck_uri)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text)
        deck_table = soup.select('table.Stable')[1]
        tables = deck_table.find_all('table')
        with transaction.atomic():
            deck = Deck()
            deck.owner = User.objects.get(username='Test')
            deck.name = soup.select_one('div.w_title').text
            deck.name = re.sub('\s+', ' ', deck.name).strip()

            summary = soup.select_one('td.S14')
            date_match = re.search(r'(?P<date>\d+/\d+/\d+)', summary.text)
            if not date_match:
                raise Exception('Could not find the date')
            deck.date_created = deck.last_modified = datetime.datetime.strptime(date_match['date'], '%d/%m/%y')
            deck.save()

            for table in tables:
                card_rows = table.select('td.G14')
                for card_row in card_rows:
                    text = card_row.text
                    matches = re.match(r'(?P<count>\d+) +(?P<name>.+)', text)
                    if not matches:
                        raise Exception(f'Could not parse {text}')

                    print(matches['count'] + ' x ' + matches['name'])
                    if matches['name'] == 'Unknown Card':
                        continue
                    deck_card = DeckCard()
                    deck_card.deck = deck
                    deck_card.count = int(matches['count'])
                    try:
                        card = Card.objects.get(name=matches['name'])
                    except Card.DoesNotExist:
                        print(f"Couldn't find card {matches['name']}. Testing split card")
                        first_name = matches['name'].split('/')[0].strip()
                        card = Card.objects.get(name=first_name)

                    deck_card.card = card
                    deck_card.save()

        self.parsed_deck_uris.append(deck_uri)
        with open(self.output_path, 'w') as json_file:
            json.dump({'uris': self.parsed_deck_uris}, json_file)
