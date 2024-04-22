"""
Module for the verify_database command
"""

import os
import re
import json
import time
from datetime import datetime
from typing import List, Set
import requests
from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand
from django.db import transaction
from bs4 import BeautifulSoup

from cards.models.card import Card, CardFace
from cards.models.decks import Deck, DeckCard


class Command(BaseCommand):
    """
    THe command for downloading major tournament decks from MTGTop8
    """

    help = "Downloads tournament decks from MTGTop8"

    deck_owner_username = "MTGTOP8_TOURNAMENT_DECK_OWNER"

    def __init__(self):
        self.base_uri = "https://www.mtgtop8.com/"
        self.output_path = os.path.join("reports", "output", "parsed_decks.json")
        if not os.path.exists(self.output_path):
            with open(self.output_path, "w", encoding="utf8") as json_file:
                json.dump({"decks": [], "events": []}, json_file)

        with open(self.output_path, encoding="utf8") as json_file:
            json_data = json.load(json_file)
            self.parsed_deck_uris = json_data["decks"]
            self.parsed_event_uris = json_data["events"]

        try:
            self.deck_user = get_user_model().objects.get(
                username=Command.deck_owner_username
            )
        except get_user_model().DoesNotExist:
            self.deck_user = get_user_model().objects.create(
                username=Command.deck_owner_username, is_active=False
            )

        super().__init__()

    def handle(self, *args, **options) -> None:
        # worlds_uri = "format?f=ST&meta=97"
        # pro_tour_uri = "format?f=ST&meta=91"
        # grand_prix_uri = "format?f=ST&meta=96"
        all_standard_decks_uri = "format?f=ST&meta=58"
        # for uri in [worlds_uri, pro_tour_uri, grand_prix_uri]:
        #     self.parse_event_summary(self.base_uri + uri)
        self.parse_format_summary_page(self.base_uri + all_standard_decks_uri)

    def parse_format_summary_page(self, format_summary_uri: str) -> None:
        """
        Parses an event summary page (which contains a list of events)
        :param format_summary_uri: The URI of the event summary page
        """
        visited_pages = set()
        pages_to_visit = {1}
        while pages_to_visit:
            page = pages_to_visit.pop()
            visited_pages.add(page)
            print(f"Parsing event list {format_summary_uri} on page {page}")
            resp = requests.get(format_summary_uri, {"cp": page})
            resp.raise_for_status()

            soup = BeautifulSoup(resp.content, features="html.parser")
            pages_to_visit.update(self.find_event_summary_pages(soup, visited_pages))
            event_list = soup.select("table.Stable")[1]
            event_trs = event_list.find_all("tr", class_="hover_tr")
            for event in event_trs:
                href_td = event.select("td")[1]
                link = href_td.find("a")
                href = link.attrs["href"]

                star_td = event.select("td")[2]
                star_count = len(star_td.find_all("img"))
                if (
                    star_count >= 3
                    or star_td.find("img")
                    and star_td.find("img").attrs["src"] == "/graph/bigstar.png"
                ):
                    self.parse_event(self.base_uri + href)

    # pylint: disable=no-self-use
    def find_event_summary_pages(
        self, soup: BeautifulSoup, visited_pages: Set[int]
    ) -> List[int]:
        """
        Finds the page numbers of the event type that haven't been parsed yet
        :param soup: THe page soup to parse
        :param visited_pages: Pages that have already been visited
        :return: A list of pages to visit
        """
        nav_buttons = soup.select(".Nav_norm")
        for button in nav_buttons:
            try:
                button_page = int(button.text)
            except ValueError:
                continue
            if button_page not in visited_pages:
                yield button_page

    def parse_event(self, event_uri: str) -> None:
        """
        Parses a single event (a tournament at a specific date with usually 8 decks)
        :param event_uri: The URI of te event page
        """
        if event_uri in self.parsed_event_uris:
            print(f"Skipping event {event_uri}")
            return

        print(f"Parsing event {event_uri}")
        resp = requests.get(event_uri)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, features="html.parser")
        summary_div = soup.select_one("div.S14")
        if not summary_div:
            print("No content in event")
            return
        summary = summary_div.select("div")[1]
        date_match = re.search(r"(?P<date>\d+/\d+/\d+)", summary.text)
        if not date_match:
            raise Exception("Could not find the date")
        event_date = datetime.strptime(date_match["date"], "%d/%m/%y")

        deck_links = soup.select("div.hover_tr div.S14 a, div.chosen_tr div.S14 a")
        for link in deck_links[:8]:
            href = link.attrs["href"]
            matches = re.search(r"d=(?P<deck_id>\d+)", href)
            deck_name = link.getText()
            deck_id = matches["deck_id"]

            self.parse_deck(
                self.base_uri + "event" + href, event_date, deck_name, deck_id
            )

        self.parsed_event_uris.append(event_uri)
        self.write_parsed_decks_to_file()
        time.sleep(1)

    def parse_deck(
        self, deck_uri: str, event_date: datetime.date, deck_name: str, deck_id: str
    ) -> None:
        """
        Parses a single deck URI, creating a new Deck object
        :param deck_uri: The URI of the deck
        """
        download_uri = f"https://www.mtgtop8.com/dec?d={deck_id}"

        if deck_uri in self.parsed_deck_uris:
            print(f"Skipping deck {deck_uri}")
            return

        print(f"Parsing deck {deck_uri}")

        resp = requests.get(download_uri)
        resp.raise_for_status()

        with transaction.atomic():
            deck = Deck()
            deck.name = deck_name
            deck.owner = self.deck_user
            deck.description = deck_uri
            deck.date_created = deck.last_modified = event_date
            deck.save()

            for line in resp.text.split("\n"):
                if line.startswith("// FORMAT"):
                    deck.format = line.split(":")[-1].lower().strip()
                    deck.save()
                    continue

                if line.startswith("// CREATOR"):
                    deck.subtitle = line.split(":")[-1]
                    deck.save()
                    continue

                if line.startswith("//") or line.strip() == "":
                    continue

                self.parse_deck_card(line, deck)

            self.parsed_deck_uris.append(deck_uri)
            self.write_parsed_decks_to_file()
        time.sleep(1)

    @staticmethod
    def parse_deck_card(row_text: str, deck: Deck) -> None:
        """
        Parses a row of card text and adds it to the given deck
        :param row_text: The row of card text
        :param deck: The deck to add the card to
        :return: The created DeckCard
        """
        matches = re.match(
            r"(?P<sb>SB: +)?(?P<count>\d+) \[.*?\] (?P<name>.+)", row_text
        )

        if not matches:
            raise Exception(f"Could not parse {row_text}")

        card_name = matches["name"].strip()

        print(matches["count"] + " x " + card_name)
        if card_name == "Unknown Card":
            return
        if " / " in card_name:
            card_name = card_name.replace(" / ", " // ")
        deck_card = DeckCard()
        deck_card.deck = deck
        deck_card.count = int(matches["count"])
        card = (
            Card.objects.filter(name=card_name, is_token=False)
            .exclude(printings__set__name__startswith="Mystery Booster Playtest Cards")
            .first()
        )
        if not card:
            print(f"Couldn't find card {card_name}. Testing split card")
            first_name = card_name.split("/")[0].strip()
            # card = Card.objects.get(name=first_name, is_token=False)
            card_faces = CardFace.objects.filter(name=first_name).exclude(
                card__layout="art_series"
            )
            assert card_faces.count() == 1
            card = card_faces.first().card

        if matches["sb"]:
            deck_card.board = "side"

        deck_card.card = card
        deck_card.save()

    def write_parsed_decks_to_file(self) -> None:
        """
        WRite out the list of decks and events that have already been parsed to file
        (this is performed periodically so that decks aren't duplicated if an error occurred.
        """
        with open(self.output_path, "w", encoding="utf8") as json_file:
            json.dump(
                {"decks": self.parsed_deck_uris, "events": self.parsed_event_uris},
                json_file,
            )
