"""
Tests that run searches through the search API, so they check what the user gets
back rather than how the search is put together
"""

import datetime
import uuid
from decimal import Decimal
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from sylvan_library.cards.models.card import (
    Card,
    CardFace,
    CardFacePrinting,
    CardLocalisation,
    CardPrinting,
    CardSubtype,
    CardSupertype,
    CardType,
    UserOwnedCard,
)
from sylvan_library.cards.models.decks import Deck, DeckCard
from sylvan_library.cards.models.card_price import CardPrice
from sylvan_library.cards.models.colour import Colour
from sylvan_library.cards.models.language import Language
from sylvan_library.cards.models.rarity import Rarity
from sylvan_library.cards.models.sets import Set

RED = 8
GREEN = 16


class SearchApiTestCase(TestCase):
    """
    A small made-up collection of cards to search:

    - Lightning Bolt: LEA (art by Christopher Rush), M10 and a newer promo, all common.
      The user owns 2 of the LEA printing.
    - Llanowar Elves: LEA and M10, common
    - Goblin King: rare in LEA, uncommon in M10
    - Black Lotus: only in LEA, rare
    - Forest: LEA, M10 and MH2, common
    - Fire // Ice: only in MH2, uncommon, a split card
    """

    fixtures = ["colours.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        # Language.english() is cached on the class, and each test database has its own
        Language.ENGLISH = None
        cls.english = Language.objects.create(name="English", code="en")
        cls.user = get_user_model().objects.create_user(username="tester")

        cls.common = Rarity.objects.create(name="Common", symbol="C", display_order=1)
        cls.uncommon = Rarity.objects.create(
            name="Uncommon", symbol="U", display_order=2
        )
        cls.rare = Rarity.objects.create(name="Rare", symbol="R", display_order=3)

        cls.lea = cls.make_set("Limited Edition Alpha", "LEA", "core", 1993)
        cls.m10 = cls.make_set("Magic 2010", "M10", "core", 2009)
        cls.mh2 = cls.make_set("Modern Horizons 2", "MH2", "draft_innovation", 2021)
        cls.promo = cls.make_set("Magic Promos", "PRM", "promo", 2023)

        cls.bolt = cls.make_card(
            "Lightning Bolt", 1, RED, ["Instant"], [], "Lightning Bolt deals 3 damage"
        )
        cls.bolt_lea = cls.make_printing(
            cls.bolt, cls.lea, cls.common, "1", artist="Christopher Rush"
        )
        cls.make_printing(cls.bolt, cls.m10, cls.common, "2")
        cls.make_printing(cls.bolt, cls.promo, cls.common, "3")

        cls.elves = cls.make_card("Llanowar Elves", 1, GREEN, ["Creature"], ["Elf"])
        cls.make_printing(cls.elves, cls.lea, cls.common, "4")
        cls.make_printing(cls.elves, cls.m10, cls.common, "5")

        cls.goblin_king = cls.make_card("Goblin King", 3, RED, ["Creature"], ["Goblin"])
        cls.make_printing(cls.goblin_king, cls.lea, cls.rare, "6")
        cls.make_printing(cls.goblin_king, cls.m10, cls.uncommon, "7")

        cls.lotus = cls.make_card("Black Lotus", 0, 0, ["Artifact"], [])
        cls.make_printing(cls.lotus, cls.lea, cls.rare, "8")

        cls.forest = cls.make_card(
            "Forest", 0, 0, ["Land"], ["Forest"], supertypes=["Basic"]
        )
        for set_obj, number in ((cls.lea, "9"), (cls.m10, "10"), (cls.mh2, "11")):
            cls.make_printing(cls.forest, set_obj, cls.common, number)

        cls.fire_ice = cls.make_card(
            "Fire // Ice", 2, RED, ["Instant"], [], layout="split"
        )
        cls.make_printing(cls.fire_ice, cls.mh2, cls.uncommon, "12")

        UserOwnedCard.objects.create(
            owner=cls.user,
            count=2,
            card_localisation=cls.bolt_lea.localisations.get(),
        )

    @classmethod
    def make_set(cls, name: str, code: str, set_type: str, year: int) -> Set:
        return Set.objects.create(
            name=name,
            code=code,
            type=set_type,
            release_date=datetime.date(year, 1, 1),
            total_set_size=0,
            keyrune_code=code,
        )

    @classmethod
    def make_card(
        cls,
        name: str,
        mana_value: float,
        colour: int,
        types: List[str],
        subtypes: List[str],
        rules_text: Optional[str] = None,
        supertypes: Optional[List[str]] = None,
        layout: str = "normal",
    ) -> Card:
        colour_count = bin(colour).count("1")
        card = Card.objects.create(
            scryfall_oracle_id=uuid.uuid4(),
            name=name,
            mana_value=mana_value,
            layout=layout,
            colour_identity=colour,
            colour_identity_count=colour_count,
        )
        face = CardFace.objects.create(
            card=card,
            name=name,
            mana_value=mana_value,
            colour=colour,
            colour_count=colour_count,
            colour_weight=0,
            colour_sort_key=0,
            rules_text=rules_text,
        )
        face.types.set(CardType.objects.get_or_create(name=t)[0] for t in types)
        face.subtypes.set(
            CardSubtype.objects.get_or_create(name=t)[0] for t in subtypes
        )
        face.supertypes.set(
            CardSupertype.objects.get_or_create(name=t)[0] for t in supertypes or []
        )
        return card

    @classmethod
    def make_printing(
        cls,
        card: Card,
        set_obj: Set,
        rarity: Rarity,
        number: str,
        artist: Optional[str] = None,
    ) -> CardPrinting:
        printing = CardPrinting.objects.create(
            scryfall_id=uuid.uuid4(),
            card=card,
            set=set_obj,
            rarity=rarity,
            number=number,
            numerical_number=int(number),
            is_starter=False,
            is_timeshifted=False,
            is_reprint=card.printings.exists(),
        )
        for face in card.faces.all():
            CardFacePrinting.objects.create(
                uuid=uuid.uuid4(),
                card_face=face,
                card_printing=printing,
                artist=artist,
            )
        CardLocalisation.objects.create(
            card_printing=printing, language=cls.english, card_name=card.name
        )
        return printing

    def search(self, query: str, logged_in: bool = False, mode: str = "cards") -> dict:
        client = APIClient()
        if logged_in:
            client.force_authenticate(self.user)
        response = client.get("/api/search/search/", {"q": query, "mode": mode})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def result_names(self, query: str, logged_in: bool = False) -> List[str]:
        return [r["card"]["name"] for r in self.search(query, logged_in)["results"]]

    def result_printings(self, query: str, logged_in: bool = False) -> List[str]:
        """
        The name and set code of each result when searching by printing
        """
        response = self.search(query, logged_in, mode="printings")
        self.assertEqual(response["mode"], "printings")
        return [
            f'{r["card"]["name"]} {r["selected_printing"]["set"]["code"]}'
            for r in response["results"]
        ]

    def test_name(self) -> None:
        self.assertEqual(self.result_names("bolt"), ["Lightning Bolt"])

    def test_results_are_sorted_by_name(self) -> None:
        self.assertEqual(
            self.result_names("t:creature or t:artifact"),
            ["Black Lotus", "Goblin King", "Llanowar Elves"],
        )

    def test_type(self) -> None:
        self.assertEqual(self.result_names("t:goblin"), ["Goblin King"])

    def test_colour(self) -> None:
        self.assertEqual(self.result_names("c:g"), ["Llanowar Elves"])

    def test_mana_value(self) -> None:
        self.assertEqual(
            self.result_names("mv=1"), ["Lightning Bolt", "Llanowar Elves"]
        )

    def test_set(self) -> None:
        self.assertEqual(self.result_names("s:mh2"), ["Fire // Ice", "Forest"])

    def test_rarity(self) -> None:
        self.assertEqual(self.result_names("r:rare"), ["Black Lotus", "Goblin King"])

    def test_artist(self) -> None:
        self.assertEqual(self.result_names("artist:rush"), ["Lightning Bolt"])

    def test_negated_artist(self) -> None:
        self.assertEqual(self.result_names("-artist:rush s:lea t:instant"), [])
        self.assertEqual(
            self.result_names("-artist:rush s:m10 t:instant"), ["Lightning Bolt"]
        )

    def test_reprint(self) -> None:
        self.assertEqual(self.result_names("is:reprint s:lea"), [])
        self.assertEqual(
            self.result_names("is:reprint s:m10"),
            ["Forest", "Goblin King", "Lightning Bolt", "Llanowar Elves"],
        )
        self.assertEqual(self.result_names("not:reprint s:mh2"), ["Fire // Ice"])

    def test_set_and_rarity_must_match_the_same_printing(self) -> None:
        """
        Goblin King is rare in LEA and uncommon in M10, so it's only rare in M10 if both
        conditions are checked against the same printing
        """
        self.assertEqual(
            self.result_names("s:lea r:rare"), ["Black Lotus", "Goblin King"]
        )
        self.assertEqual(self.result_names("s:m10 r:rare"), [])

    def test_negated_set_finds_cards_with_another_printing(self) -> None:
        """
        Black Lotus is only in LEA, but every other card has a printing somewhere else
        """
        self.assertEqual(
            self.result_names("-s:lea"),
            [
                "Fire // Ice",
                "Forest",
                "Goblin King",
                "Lightning Bolt",
                "Llanowar Elves",
            ],
        )

    def test_ownership(self) -> None:
        self.assertEqual(
            self.result_names("own>=1", logged_in=True), ["Lightning Bolt"]
        )

    def test_owned_count_in_results(self) -> None:
        card = self.search("bolt", logged_in=True)["results"][0]["card"]
        self.assertEqual(card["owned_count"], 2)

    def test_selected_printing_is_newest_non_promo(self) -> None:
        result = self.search("bolt")["results"][0]
        self.assertEqual(result["selected_printing"]["set"]["code"], "M10")

    def test_selected_printing_matches_set_search(self) -> None:
        result = self.search("bolt s:lea")["results"][0]
        self.assertEqual(result["selected_printing"]["set"]["code"], "LEA")

    def test_selected_printing_is_newest_matching_printing(self) -> None:
        result = self.search("bolt -s:m10")["results"][0]
        self.assertEqual(result["selected_printing"]["set"]["code"], "LEA")
        result = self.search("goblin r:uncommon")["results"][0]
        self.assertEqual(result["selected_printing"]["set"]["code"], "M10")

    def test_selected_printing_can_be_a_promo_if_nothing_else_matches(self) -> None:
        result = self.search("bolt s:prm")["results"][0]
        self.assertEqual(result["selected_printing"]["set"]["code"], "PRM")

    def test_searching_by_card_is_the_default(self) -> None:
        client = APIClient()
        response = client.get("/api/search/search/", {"q": "bolt"}).json()
        self.assertEqual(response["mode"], "cards")
        self.assertEqual(response["count"], 1)

    def test_printings(self) -> None:
        """
        Printings of the same card go from newest to oldest
        """
        self.assertEqual(
            self.result_printings("bolt"),
            ["Lightning Bolt PRM", "Lightning Bolt M10", "Lightning Bolt LEA"],
        )

    def test_printings_must_match_the_whole_query(self) -> None:
        self.assertEqual(
            self.result_printings("r:rare"), ["Black Lotus LEA", "Goblin King LEA"]
        )

    def test_sorting_printings(self) -> None:
        self.assertEqual(
            self.result_printings("t:creature sort:date"),
            [
                "Goblin King LEA",
                "Llanowar Elves LEA",
                "Goblin King M10",
                "Llanowar Elves M10",
            ],
        )

    def test_printing_ownership(self) -> None:
        self.assertEqual(
            self.result_printings("own>=1", logged_in=True), ["Lightning Bolt LEA"]
        )
        self.assertEqual(
            self.result_printings("bolt own=0", logged_in=True),
            ["Lightning Bolt PRM", "Lightning Bolt M10"],
        )

    def test_printing_owned_count(self) -> None:
        response = self.search("bolt", logged_in=True, mode="printings")
        self.assertEqual(
            [r["selected_printing"]["owned_count"] for r in response["results"]],
            [0, 0, 2],
        )

    def test_price(self) -> None:
        """
        In a card search, a card's price is its cheapest printing
        """
        for printing, value in zip(
            self.bolt.printings.order_by("set__release_date"), ("150", "0.50", "2")
        ):
            printing.latest_price = CardPrice.objects.create(
                card_printing=printing,
                date=datetime.date.today(),
                paper_value=Decimal(value),
                cheapest_card=self.bolt if value == "0.50" else None,
            )
            printing.save()
        self.assertEqual(self.result_names("price<1"), ["Lightning Bolt"])
        self.assertEqual(self.result_printings("price<1"), ["Lightning Bolt M10"])
        self.assertEqual(
            self.result_printings("bolt sort:price"),
            ["Lightning Bolt LEA", "Lightning Bolt PRM", "Lightning Bolt M10"],
        )
        self.assertEqual(
            self.result_printings("bolt -sort:price"),
            ["Lightning Bolt M10", "Lightning Bolt PRM", "Lightning Bolt LEA"],
        )
        self.assertEqual(
            self.result_printings("bolt sort<price"),
            ["Lightning Bolt M10", "Lightning Bolt PRM", "Lightning Bolt LEA"],
        )

    def test_unknown_set_is_an_error(self) -> None:
        response = self.search("s:nonsense")
        self.assertEqual(response["results"], [])
        self.assertEqual(response["error_message"], 'Unknown set "nonsense"')

    def test_layout_with_a_printing_parameter(self) -> None:
        self.assertEqual(self.result_names("layout:split s:mh2"), ["Fire // Ice"])

    def test_layout(self) -> None:
        self.assertEqual(self.result_names("layout:split"), ["Fire // Ice"])

    def test_deck_with_a_printing_parameter(self) -> None:
        deck = Deck.objects.create(
            name="Burn",
            owner=self.user,
            format="modern",
            date_created=datetime.date.today(),
        )
        DeckCard.objects.create(deck=deck, card=self.bolt, count=4)
        DeckCard.objects.create(deck=deck, card=self.goblin_king, count=2)
        self.assertEqual(
            self.result_names(f"deck:{deck.id}"), ["Goblin King", "Lightning Bolt"]
        )
        self.assertEqual(self.result_names(f"deck:{deck.id} s:prm"), ["Lightning Bolt"])

    def test_universes_beyond_with_a_printing_parameter(self) -> None:
        self.assertEqual(
            self.result_names("-is:ub r:rare"), ["Black Lotus", "Goblin King"]
        )

    def test_game(self) -> None:
        self.assertEqual(len(self.result_names("game:paper")), 6)
        self.assertEqual(self.result_names("game:online"), [])

    def test_sorting_by_a_printing_field_does_not_repeat_cards(self) -> None:
        response = self.search("t:creature sort:date")
        self.assertEqual(response["count"], 2)
        self.assertEqual(
            [r["card"]["name"] for r in response["results"]],
            ["Goblin King", "Llanowar Elves"],
        )

    def test_sort_by_power(self) -> None:
        self.elves.faces.update(power="1", num_power=1)
        self.goblin_king.faces.update(power="2", num_power=2)
        self.assertEqual(
            self.result_names("order:power"),
            [
                "Llanowar Elves",
                "Goblin King",
                "Black Lotus",
                "Fire // Ice",
                "Forest",
                "Lightning Bolt",
            ],
        )
        self.assertEqual(
            self.result_names("order<power")[:2], ["Goblin King", "Llanowar Elves"]
        )

    def test_sort_by_colour_weight(self) -> None:
        self.assertEqual(len(self.result_names("sort:cw")), 6)

    def test_sort_by_rarity(self) -> None:
        self.assertEqual(
            self.result_names("sort:rarity -s:lea"),
            [
                "Fire // Ice",
                "Goblin King",
                "Forest",
                "Lightning Bolt",
                "Llanowar Elves",
            ],
        )

    def test_sort_by_a_printing_field_only_uses_matching_printings(self) -> None:
        """
        Lightning Bolt's newest printing is the promo, which doesn't match
        """
        self.assertEqual(
            self.result_names("(s:m10 or s:mh2) sort<date"),
            [
                "Fire // Ice",
                "Forest",
                "Goblin King",
                "Lightning Bolt",
                "Llanowar Elves",
            ],
        )
