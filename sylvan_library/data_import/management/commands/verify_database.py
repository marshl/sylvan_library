"""
Module for the verify_database command
"""
import math
import sys
import traceback
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Count

from cards.models import (
    Block,
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)

WUBRG = (
    Card.colour_flags.white
    | Card.colour_flags.blue
    | Card.colour_flags.black
    | Card.colour_flags.red
    | Card.colour_flags.green
)

# pylint: disable=too-many-public-methods
class Command(BaseCommand):
    """
    The command to verify that the database update was successful
    In a way this could be considered a kind of unit test, but it is meant to be
    applied on actual production data, and just verifies that the data is in the correct state.

    Note that some of these tests may fail occasionally, probably due to changes in the API.
    """

    help = "Verifies that database update was successful"

    def __init__(self):
        super().__init__()

        self.successful_tests = 0
        self.failed_tests = 0
        self.error_messages = list()
        self.test_count = 0

    def handle(self, *args, **options):
        methods = [
            method_name
            for method_name in dir(self)
            if callable(getattr(self, method_name)) and method_name.startswith("test")
        ]
        for method in methods:
            (getattr(self, method))()

        total_tests = self.successful_tests + self.failed_tests
        print("\n\n")
        print(f"{total_tests} Tests Run")
        print(f"{self.successful_tests} Successful")
        print(f"{self.failed_tests} Failed)")
        for error in self.error_messages:
            print(error["message"])

    def test_blocks(self):
        """
        Tests the properties of various blocks
        """
        self.assert_true(
            Block.objects.filter(name="Ice Age").exists(), "Ice Age block should exist"
        )
        self.assert_true(
            Block.objects.filter(name="Ravnica").exists(), "Ravnica block should exist"
        )
        self.assert_true(
            Block.objects.filter(name="Ixalan").exists(), "Ixalan block should exist"
        )
        self.assert_false(
            Block.objects.filter(name="Weatherlight").exists(),
            "Weatherlight block should not exist",
        )

        self.assert_true(
            Block.objects.get(name="Ice Age").release_date
            < Block.objects.get(name="Onslaught").release_date,
            "Ice Age should be released before Onslaught",
        )

        self.assert_true(
            Block.objects.get(name="Mirrodin").sets.count() == 3,
            "Mirrodin should have 3 sets",
        )
        self.assert_true(
            Block.objects.get(name="Time Spiral").sets.count() == 4,
            "Time Spiral should have 4 sets",
        )
        self.assert_true(
            Block.objects.get(name="Amonkhet").sets.count() == 5,
            "Amonkhet blockshould have 5 sets",
        )

    def test_sets(self):
        """
        Tests the properties of various sets
        """
        self.assert_true(
            Set.objects.get(code="ONS").block.name == "Onslaught",
            "Onslaught should be in the Onslaught block",
        )
        self.assert_true(
            Set.objects.get(code="WTH").block.name == "Mirage",
            "Weatherlight should be in the Mirage block",
        )
        self.assert_true(
            Set.objects.get(code="CSP").block.name == "Ice Age",
            "Coldsnap should be in the Ice Age block",
        )

    def test_rarities(self):
        """
        Tests the properties of various rarities
        """
        self.assert_true(
            Rarity.objects.filter(symbol="R").exists(), "The rare rarity should exist"
        )

        self.assert_true(
            Rarity.objects.get(symbol="C").display_order
            < Rarity.objects.get(symbol="U").display_order,
            "Common rarity should be displayed before uncommon rarity",
        )

    def test_card_printings(self):
        """
        Tests that every card should have a printing
        """
        query = Card.objects.annotate(printing_count=Count("printings")).filter(
            printing_count=0
        )
        self.assert_true(
            query.count() == 0,
            f"There should be at least one printing for every card: {query.all()}",
        )

    def test_minimum_printed_languages(self):
        """
        Tests that every card has a printed language
        """
        self.assert_true(
            CardPrinting.objects.annotate(printlang_count=Count("printed_languages"))
            .filter(printlang_count=0)
            .count()
            == 0,
            "There should be at least one printed language for each printing",
        )

    def test_minimum_physical_cards(self):
        """
        Tests that every physical card has at least one printed language
        """
        zero_count_printlangs = CardPrintingLanguage.objects.annotate(
            physcard_count=Count("physical_cards")
        ).filter(physcard_count=0)

        self.assert_true(
            zero_count_printlangs.count() == 0,
            "Every CardPrintingLanguage should have at least one PhysicalCard",
        )

        zero_count_physcard = PhysicalCard.objects.annotate(
            printlang_count=Count("printed_languages")
        ).filter(printlang_count=0)

        self.assert_true(
            zero_count_physcard.count() == 0,
            f"There should be at least one printed language for each physical card: "
            f"{zero_count_physcard.all()}",
        )

        low_count_two_faced_cards = (
            PhysicalCard.objects.filter(
                layout__in=("split", "flip", "transform", "meld")
            )
            .annotate(printlang_count=Count("printed_languages"))
            .exclude(printlang_count__gte=2)
        )

        self.assert_true(
            low_count_two_faced_cards.count() == 0,
            "Multi-sided physical cards should have multiple printlangs",
        )

        high_count_single_face_cards = (
            PhysicalCard.objects.exclude(
                layout__in=("split", "flip", "transform", "meld")
            )
            .annotate(printlang_count=Count("printed_languages"))
            .exclude(printlang_count=1)
        )

        self.assert_true(
            high_count_single_face_cards.count() == 0,
            "Only two-face cards should have multiple printlangs",
        )

    def test_unique_images(self):
        """
        Tests that every printed language has a unique image path
        """

        image_url_map = {}
        for printed_language in (
            CardPrintingLanguage.objects.prefetch_related("card_printing__card")
            .prefetch_related("card_printing__set")
            .prefetch_related("language")
            .all()
        ):
            image_path = printed_language.get_image_path()
            if image_path is None:
                continue
            if image_path not in image_url_map:
                image_url_map[image_path] = [printed_language]
            else:
                image_url_map[image_path].append(printed_language)

        for image_path, printed_languages in image_url_map.items():
            if len(printed_languages) == 1:
                continue

            # Flip and split cards share the same image, so we can ignore them
            if not any(
                pl
                for pl in printed_languages
                if pl.card_printing.card.layout not in ["flip", "split"]
            ):
                continue

            self.assert_true(
                False,
                f"Too many printed languages for the same image path: "
                + f"{printed_languages}: {image_path}",
            )

    def test_card_name(self):
        """
        Test that cards of various names exist
        """
        # Normal card
        self.assert_card_exists("Animate Artifact")

        # Split card
        self.assert_card_exists("Wear")

        # UTF-8
        self.assert_card_exists("Jötun Grunt")
        self.assert_card_exists("Aether Charge")

        # Un-names
        self.assert_card_exists("_____")
        self.assert_card_exists('"Ach! Hans, Run!"')
        self.assert_card_exists(
            "The Ultimate Nightmare of Wizards of the Coast® Customer Service"
        )

        # Fip card
        self.assert_card_exists("Homura, Human Ascendant")
        self.assert_card_exists("Homura's Essence")

        # Negative tests
        self.assert_card_not_exists("Æther Charge")

    def test_card_cost(self):
        """
        Tests tje cost of various Card objects
        :return:
        """
        # Expensive card
        self.assert_card_cost_eq("Progenitus", "{W}{W}{U}{U}{B}{B}{R}{R}{G}{G}")

        # Lands
        self.assert_card_cost_eq("Forest", None)
        self.assert_card_cost_eq("Dryad Arbor", None)

        # Monocoloured hybrid card
        self.assert_card_cost_eq("Flame Javelin", "{2/R}{2/R}{2/R}")

        # Plane
        self.assert_card_cost_eq("Krosa", None)

        # Multi-numeral symbol cards
        self.assert_card_cost_eq("Gleemax", "{1000000}")
        self.assert_card_cost_eq("Draco", "{16}")

        # Hybrid multicoloured card
        self.assert_card_cost_eq("Naya Hushblade", "{R/W}{G}")

        # Half mana card
        self.assert_card_cost_eq("Little Girl", "{HW}")

        # Meld card
        self.assert_card_cost_eq("Brisela, Voice of Nightmares", None)

        # Flip card
        self.assert_card_cost_eq("Bushi Tenderfoot", "{W}")
        self.assert_card_cost_eq("Kenzo the Hardhearted", None)

        # Phyrexian mana card
        self.assert_card_cost_eq("Birthing Pod", "{3}{G/P}")

    def test_card_cmc(self):
        """
        Tests the converted mana costs of various cards
        :return:
        """
        # Normal cards
        self.assert_card_cmc_eq("Tarmogoyf", 2)
        self.assert_card_cmc_eq("Black Lotus", 0)

        # Costless card
        self.assert_card_cmc_eq("Living End", 0)

        # Half mana card
        self.assert_card_cmc_eq("Little Girl", 0.5)

        # Monocoloured hybrid cards
        self.assert_card_cmc_eq("Reaper King", 10)
        self.assert_card_cmc_eq("Flame Javelin", 6)

        # High cost cards
        self.assert_card_cmc_eq("Blinkmoth Infusion", 14)
        self.assert_card_cmc_eq("Gleemax", 1000000)

        # Phyrexian mana card
        self.assert_card_cmc_eq("Birthing Pod", 4)

        # Land
        self.assert_card_cmc_eq("Dryad Arbor", 0)

        # Colourless mana card
        self.assert_card_cmc_eq("Kozilek, the Great Distortion", 10)

        # Plane
        self.assert_card_cmc_eq("Krosa", 0)

        # X cost card
        self.assert_card_cmc_eq("Comet Storm", 2)

        # Transform card
        self.assert_card_cmc_eq("Garruk Relentless", 4)
        self.assert_card_cmc_eq("Garruk, the Veil-Cursed", 4)

        # Meld card
        self.assert_card_cmc_eq("Brisela, Voice of Nightmares", 11)

        # Split card
        # Both Wear and Tear should have the same CMC under the new rules
        self.assert_card_cmc_eq("Wear", 3)
        self.assert_card_cmc_eq("Tear", 3)

        # Flip card
        self.assert_card_cmc_eq("Homura's Essence", 6)

    def test_card_colour(self):
        """
        Tests the colour of various Card objects
        """

        # Mono-coloured card
        self.assert_card_colour_eq("Glory Seeker", Card.colour_flags.white)

        # Multicoloured card
        self.assert_card_colour_eq(
            "Dark Heart of the Wood", Card.colour_flags.black | Card.colour_flags.green
        )

        self.assert_card_colour_eq("Progenitus", WUBRG)
        self.assert_card_colour_eq("Reaper King", WUBRG)

        # Hybrid card
        self.assert_card_colour_eq(
            "Azorius Guildmage", Card.colour_flags.white | Card.colour_flags.blue
        )

        # Colour indicator cards
        self.assert_card_colour_eq("Transguild Courier", WUBRG)
        self.assert_card_colour_eq("Ghostfire", 0)
        self.assert_card_colour_eq("Dryad Arbor", Card.colour_flags.green)

        # Same colour transform card
        self.assert_card_colour_eq("Delver of Secrets", Card.colour_flags.blue)
        self.assert_card_colour_eq("Insectile Aberration", Card.colour_flags.blue)

        # Different colour transform card
        self.assert_card_colour_eq("Garruk Relentless", Card.colour_flags.green)
        self.assert_card_colour_eq(
            "Garruk, the Veil-Cursed", Card.colour_flags.black | Card.colour_flags.green
        )

        # Colour identity cards
        self.assert_card_colour_eq("Bosh, Iron Golem", 0)

        # Split card
        self.assert_card_colour_eq("Tear", Card.colour_flags.white)

        # Flip card
        self.assert_card_colour_eq(
            "Rune-Tail, Kitsune Ascendant", Card.colour_flags.white
        )
        self.assert_card_colour_eq("Rune-Tail's Essence", Card.colour_flags.white)

        # Normal cards

    def test_card_colour_identity(self):
        """
        Tests the colour identity of various Cards
        :return:
        """

        self.assert_card_colour_identity_eq("Goblin Piker", Card.colour_flags.red)

        # Lands
        self.assert_card_colour_identity_eq("Mountain", Card.colour_flags.red)
        self.assert_card_colour_identity_eq("Polluted Delta", 0)
        self.assert_card_colour_identity_eq("Tolarian Academy", Card.colour_flags.blue)

        # Colour indicator cards
        self.assert_card_colour_identity_eq("Ghostfire", Card.colour_flags.red)
        self.assert_card_colour_identity_eq("Dryad Arbor", Card.colour_flags.green)

        # Augment cards
        self.assert_card_colour_identity_eq("Half-Orc, Half-", Card.colour_flags.red)

        # Symbol in rules cards
        self.assert_card_colour_identity_eq("Bosh, Iron Golem", Card.colour_flags.red)
        self.assert_card_colour_identity_eq(
            "Dawnray Archer", Card.colour_flags.white | Card.colour_flags.blue
        )
        self.assert_card_colour_identity_eq("Obelisk of Alara", WUBRG)

        # Hybrid cards
        self.assert_card_colour_identity_eq(
            "Azorius Guildmage", Card.colour_flags.white | Card.colour_flags.blue
        )

        # Split cards
        self.assert_card_colour_identity_eq(
            "Wear", Card.colour_flags.white | Card.colour_flags.red
        )
        self.assert_card_colour_identity_eq(
            "Tear", Card.colour_flags.white | Card.colour_flags.red
        )

        # Flip cards
        self.assert_card_colour_identity_eq(
            "Garruk Relentless", Card.colour_flags.black | Card.colour_flags.green
        )
        self.assert_card_colour_identity_eq(
            "Garruk, the Veil-Cursed", Card.colour_flags.black | Card.colour_flags.green
        )
        self.assert_card_colour_identity_eq(
            "Gisela, the Broken Blade", Card.colour_flags.white
        )
        self.assert_card_colour_identity_eq(
            "Brisela, Voice of Nightmares", Card.colour_flags.white
        )

    def test_card_colour_count(self):
        """
        Tests the colour count of various cards
        """
        # Normal cards
        self.assert_card_colour_count_eq("Birds of Paradise", 1)
        self.assert_card_colour_count_eq("Edgewalker", 2)
        self.assert_card_colour_count_eq("Naya Hushblade", 3)
        self.assert_card_colour_count_eq("Swamp", 0)
        self.assert_card_colour_count_eq("Ornithopter", 0)
        self.assert_card_colour_count_eq("Glint-Eye Nephilim", 4)
        self.assert_card_colour_count_eq("Cromat", 5)

        # Colour indicator cards
        self.assert_card_colour_count_eq("Evermind", 1)
        self.assert_card_colour_count_eq("Arlinn, Embraced by the Moon", 2)

        # Non-playable cards
        self.assert_card_colour_count_eq("Dance, Pathetic Marionette", 0)

    def test_card_type(self):
        """
        Test the type of various cards
        """
        self.assert_card_type_eq("Kird Ape", "Creature")
        self.assert_card_type_eq("Forest", "Basic Land")
        self.assert_card_type_eq("Masticore", "Artifact Creature")
        self.assert_card_type_eq("Tarmogoyf", "Creature")
        self.assert_card_type_eq("Lignify", "Tribal Enchantment")
        self.assert_card_type_eq("Sen Triplets", "Legendary Artifact Creature")
        self.assert_card_type_eq("Walking Atlas", "Artifact Creature")
        self.assert_card_type_eq("Soul Net", "Artifact")
        self.assert_card_type_eq("Ajani Goldmane", "Legendary Planeswalker")
        self.assert_card_type_eq("Bant", "Plane")
        self.assert_card_type_eq("My Crushing Masterstroke", "Scheme")
        self.assert_card_type_eq("Nameless Race", "Creature")

    def test_card_subype(self):
        """
        Tests the subtype of various cards
        """
        # Single subtype
        self.assert_card_subtype_eq("Screaming Seahawk", "Bird")
        self.assert_card_subtype_eq("Mistform Ultimus", "Illusion")
        self.assert_card_subtype_eq("Forest", "Forest")
        # Multiple subtypes
        self.assert_card_subtype_eq("Glory Seeker", "Human Soldier")
        # Planeswalker
        self.assert_card_subtype_eq("Jace, the Mind Sculptor", "Jace")
        # Tribal
        self.assert_card_subtype_eq("Lignify", "Treefolk Aura")
        # None
        self.assert_card_subtype_eq("Nameless Race", "")
        self.assert_card_subtype_eq("Spellbook", "")

    def test_card_power(self):
        """
        Test the stringy power of various cards
        """
        # Normal Cards
        self.assert_card_power_eq("Birds of Paradise", "0")
        self.assert_card_power_eq("Dryad Arbor", "1")
        self.assert_card_power_eq("Juggernaut", "5")

        # Vehicles
        self.assert_card_power_eq("Irontread Crusher", "6")

        # Negative Cards
        self.assert_card_power_eq("Char-Rumbler", "-1")
        self.assert_card_power_eq("Spinal Parasite", "-1")

        # + Cards
        self.assert_card_power_eq("Tarmogoyf", "*")
        self.assert_card_power_eq("Gaea's Avenger", "1+*")
        self.assert_card_power_eq("Zombified", "+2")
        self.assert_card_power_eq("S.N.O.T.", "*²")

        # Misprints
        self.assert_card_power_eq("Elvish Archers", "2")

        # Non-creature cards
        self.assert_card_power_eq("Ancestral Recall", None)
        self.assert_card_power_eq("Krosa", None)
        self.assert_card_power_eq("Gratuitous Violence", None)

    def test_card_num_power(self):
        """
        Tests the numerical power of various cards
        """
        # Normal creatures
        self.assert_card_num_power_eq("Stone Golem", 4)
        self.assert_card_num_power_eq("Progenitus", 10)
        self.assert_card_num_power_eq("Emrakul, the Aeons Torn", 15)

        # Infinite creatures
        self.assert_card_num_power_eq("Infinity Elemental", math.inf)

        # Vehicles
        self.assert_card_num_power_eq("Smuggler's Copter", 3)

        # Negative power creatures
        self.assert_card_num_power_eq("Spinal Parasite", -1)

        # Non-creatures
        self.assert_card_num_power_eq("Ancestral Recall", 0)

        # Misprints
        self.assert_card_num_power_eq("Elvish Archers", 2)

        # + Cards
        self.assert_card_num_power_eq("Tarmogoyf", 0)
        self.assert_card_num_power_eq("Haunting Apparition", 1)

    def test_card_toughness(self):
        """
        Test the stringy toughness of various cards
        """
        # Normal Cards
        self.assert_card_toughness_eq("Obsianus Golem", "6")
        self.assert_card_toughness_eq("Dryad Arbor", "1")
        self.assert_card_toughness_eq("Force of Savagery", "0")

        # Vehicles
        self.assert_card_toughness_eq("Heart of Kiran", "4")

        # Negative Cards
        self.assert_card_toughness_eq("Spinal Parasite", "-1")

        # + Cards
        self.assert_card_toughness_eq("Tarmogoyf", "1+*")
        self.assert_card_toughness_eq("Gaea's Avenger", "1+*")
        self.assert_card_toughness_eq("Half-Orc, Half-", "+1")
        self.assert_card_toughness_eq("S.N.O.T.", "*²")

        # Misprints
        self.assert_card_toughness_eq("Elvish Archers", "1")

        # Noncreature cards
        self.assert_card_toughness_eq("Gratuitous Violence", None)
        self.assert_card_toughness_eq("Ancestral Recall", None)
        self.assert_card_toughness_eq("Krosa", None)

    def test_card_num_toughness(self):
        """
        Test the numerical toughness of various cards
        """
        # Normal Cards
        self.assert_card_num_toughness_eq("Wall of Fire", 5)
        self.assert_card_num_toughness_eq("Daru Lancer", 4)
        self.assert_card_num_toughness_eq("Tree of Redemption", 13)

        # Vehicles
        self.assert_card_num_toughness_eq("Skysovereign, Consul Flagship", 5)

        # Negative cards
        self.assert_card_num_toughness_eq("Spinal Parasite", -1)

        # Misprints
        self.assert_card_num_toughness_eq("Elvish Archers", 1)

        # + Cards
        self.assert_card_num_toughness_eq("Tarmogoyf", 1)
        self.assert_card_num_toughness_eq("Angry Mob", 2)
        self.assert_card_num_toughness_eq("S.N.O.T.", 0)

    def test_loyalty(self):
        """
        Test the loyalty of various cards
        """
        # Planeswalkers
        self.assert_card_loyalty_eq("Ajani Goldmane", "4")

        # Flipwalkers
        self.assert_card_loyalty_eq("Chandra, Fire of Kaladesh", None)
        self.assert_card_loyalty_eq("Chandra, Roaring Flame", "4")

        # Non-planeswalkers
        self.assert_card_loyalty_eq("Glimmervoid Basin", None)
        self.assert_card_loyalty_eq("Megatog", None)
        self.assert_card_loyalty_eq("Urza", None)

    def test_card_num_loyalty(self):
        """
        Tests the numerical loyalty of various cards
        """
        # Planeswalkers
        self.assert_card_num_loyalty_eq("Ajani Goldmane", 4)

        # Flipwalkers
        self.assert_card_num_loyalty_eq("Chandra, Fire of Kaladesh", 0)
        self.assert_card_num_loyalty_eq("Chandra, Roaring Flame", 4)

        # Non-planeswalkers
        self.assert_card_num_loyalty_eq("Glimmervoid Basin", 0)
        self.assert_card_num_loyalty_eq("Megatog", 0)
        self.assert_card_num_loyalty_eq("Urza", 0)

    def test_card_rules_text(self):
        """
        Tests the rules texts
        """
        self.assert_card_rules_eq("Grizzly Bears", None)
        self.assert_card_rules_eq("Elite Vanguard", None)
        self.assert_card_rules_eq("Forest", "({T}: Add {G}.)")
        self.assert_card_rules_eq("Snow-Covered Swamp", "({T}: Add {B}.)")

        self.assert_card_rules_eq(
            "Air Elemental",
            "Flying (This creature can't be blocked except by creatures with flying or reach.)",
        )
        self.assert_card_rules_eq("Thunder Spirit", "Flying, first strike")
        self.assert_card_rules_eq("Dark Ritual", "Add {B}{B}{B}.")
        self.assert_card_rules_eq("Palladium Myr", "{T}: Add {C}{C}.")
        self.assert_card_rules_eq(
            "Ice Cauldron",
            "{X}, {T}: Put a charge counter on Ice Cauldron and exile a nonland card from your "
            "hand. You may cast that card for as long as it remains exiled. Note the type and "
            "amount of mana spent to pay this activation cost. Activate this ability only if "
            "there are no charge counters on Ice Cauldron.\n{T}, Remove a charge counter from "
            "Ice Cauldron: Add Ice Cauldron's last noted type and amount of mana. "
            "Spend this mana only to cast the last card exiled with Ice Cauldron.",
        )

    def test_card_layouts(self):
        """
        Tests the layouts of various Card objects
        """
        self.assert_card_layout_eq("Glory Seeker", "normal")
        self.assert_card_layout_eq("Hit", "split")
        self.assert_card_layout_eq("Run", "split")
        self.assert_card_layout_eq("Hired Muscle", "flip")
        self.assert_card_layout_eq("Scarmaker", "flip")
        self.assert_card_layout_eq("Delver of Secrets", "transform")
        self.assert_card_layout_eq("Insectile Aberration", "transform")
        self.assert_card_layout_eq("Mount Keralia", "planar")
        self.assert_card_layout_eq("Glimmervoid Basin", "planar")
        self.assert_card_layout_eq("I Bask in Your Silent Awe", "scheme")
        self.assert_card_layout_eq("Every Hope Shall Vanish", "scheme")
        self.assert_card_layout_eq("Time Distortion", "planar")
        self.assert_card_layout_eq("Echo Mage", "leveler")
        self.assert_card_layout_eq("Caravan Escort", "leveler")
        self.assert_card_layout_eq("Birds of Paradise Avatar", "vanguard")
        self.assert_card_layout_eq("Gix", "vanguard")
        self.assert_card_layout_eq("Gisela, the Broken Blade", "meld")
        self.assert_card_layout_eq("Bruna, the Fading Light", "meld")
        self.assert_card_layout_eq("Brisela, Voice of Nightmares", "meld")

    def test_cardprinting_flavour(self):
        """
        Tests the flavour texts of various CardPrintings
        """
        self.assert_cardprinting_flavour_eq(
            "Goblin Chieftain",
            "M10",
            '"We are goblinkind, heirs to the mountain empires of chieftains past. '
            + 'Rest is death to us, and arson is our call to war."',
        )

        self.assert_cardprinting_flavour_eq(
            "Goblin Chieftain", "M12", '''"It's time for the 'Smash, Smash' song!"'''
        )

        self.assert_cardprinting_flavour_eq("Land Aid '04", "UNH", None)
        self.assert_cardprinting_flavour_eq(
            "Goblin Balloon Brigade",
            "M11",
            '"The enemy is getting too close! Quick! Inflate the toad!"',
        )
        self.assert_cardprinting_flavour_eq(
            "Lhurgoyf",
            "ICE",
            """"Ach! Hans, run! It's the Lhurgoyf!" —Saffi Eriksdotter, last words""",
        )

        self.assert_cardprinting_flavour_eq("Magma Mine", "VIS", "BOOM!")

    def test_cardprinting_artist(self):
        """
        Tests the properties of CardPrinting artists
        """
        # Misprint
        self.assert_cardprinting_artist_eq("Animate Artifact", "LEA", "Douglas Shuler")
        self.assert_cardprinting_artist_eq("Benalish Hero", "LEB", "Douglas Shuler")

        # Combination
        self.assert_cardprinting_artist_eq(
            "Wound Reflection", "SHM", "Terese Nielsen & Ron Spencer"
        )

        # Unhinged
        self.assert_cardprinting_artist_eq(
            "Persecute Artist", "UNH", "Rebecca “Don't Mess with Me” Guay"
        )
        self.assert_cardprinting_artist_eq(
            "Fascist Art Director", "UNH", "Edward P. “Feed Me” Beard, Jr."
        )
        self.assert_cardprinting_artist_eq("Atinlay Igpay", "UNH", "Evkay Alkerway")

    def test_cardprinting_collectornum(self):
        """
        Tests the properties of CardPrinting collector numbers
        """
        brothers_yamazaki = Card.objects.get(name="Brothers Yamazaki")
        kamigawa = Set.objects.get(name="Champions of Kamigawa")
        brother_a = CardPrinting.objects.get(
            card=brothers_yamazaki, set=kamigawa, number__endswith="a"
        )
        brother_b = CardPrinting.objects.get(
            card=brothers_yamazaki, set=kamigawa, number__endswith="b"
        )

        self.assert_true(
            brother_a.number[:-1] == brother_b.number[:-1],
            "Brothers Yamazaki should have the same collector number",
        )

        fallen_empires = Set.objects.get(name="Fallen Empires")
        initiates = Card.objects.get(name="Initiates of the Ebon Hand")
        numbers = [
            c.number
            for c in CardPrinting.objects.filter(card=initiates, set=fallen_empires)
        ]
        self.assert_true(
            sorted(numbers) == sorted(["39a", "39b", "39c"]),
            "The collector numbers for Initiates of the Ebon Hand are incorrect",
        )

    def test_physical_cards(self):
        """
        Tests the properties of PhysicalCard objects
        """
        gisela = Card.objects.get(name="Gisela, the Broken Blade")
        bruna = Card.objects.get(name="Bruna, the Fading Light")
        brisela = Card.objects.get(name="Brisela, Voice of Nightmares")
        emn = Set.objects.get(code="EMN")
        english = Language.objects.get(name="English")

        gisela_printlang = gisela.printings.get(set=emn).printed_languages.get(
            language=english
        )
        bruna_printlang = bruna.printings.get(set=emn).printed_languages.get(
            language=english
        )
        brisela_printlang = brisela.printings.get(set=emn).printed_languages.get(
            language=english
        )

        self.assert_true(
            gisela_printlang.physical_cards.count() == 1,
            "Gisela should only have one physical card",
        )
        self.assert_true(
            bruna_printlang.physical_cards.count() == 1,
            "Bruna should only have one physical card",
        )
        self.assert_true(
            brisela_printlang.physical_cards.count() == 2,
            "Brisela should have two physical cards",
        )

    def assert_card_exists(self, card_name: str):
        """
        Asserts that a card with the given name does exist
        :param card_name: The name of the card to test
        """
        self.assert_true(
            Card.objects.filter(name=card_name).exists(), f"{card_name} should exist"
        )

    def assert_card_not_exists(self, card_name: str):
        """
        Assert that a card with the given name does not exist
        :param card_name: The name of the card to test
        """
        self.assert_false(
            Card.objects.filter(name=card_name).exists(),
            f"{card_name} should not exist",
        )

    def assert_card_cost_eq(self, card_name: str, cost: Optional[str]):
        """
        Asserts that the given card has the given cost
        :param card_name: The name of the card to test
        :param cost: The expected cost of the card
        """
        self.assert_card_attr_eq(card_name, "cost", cost)

    def assert_card_cmc_eq(self, card_name: str, cmc: float):
        """
        Asserts that the given card has the given converted man cost
        :param card_name: The name of the card to test
        :param cmc: The expected converted mana cost of the card
        """
        self.assert_card_attr_eq(card_name, "cmc", cmc)

    def assert_card_colour_eq(self, card_name: str, colours: int):
        """
        Asserts that the card with the given name has the given colours
        :param card_name: The name of the card to test
        :param colours: the expected colours
        """
        actual = int(Card.objects.get(name=card_name).colour_flags)
        self.assert_true(
            colours == actual,
            f'{card_name}.colours was expected to be "{colours}", actually "{actual}"',
        )

    def assert_card_colour_identity_eq(self, card_name: str, colour_identity: int):
        """
        Asserts that the card with the given name has the given colour identity
        :param card_name: The name of the card to test
        :param colour_identity: the expected colour_identity
        """
        actual = int(Card.objects.get(name=card_name).colour_identity_flags)
        self.assert_true(
            colour_identity == actual,
            f"{card_name}.colour_identity_flags was expected "
            f'to be "{colour_identity}", actually "{actual}"',
        )

    def assert_card_colour_count_eq(self, card_name: str, colour_count: int):
        """
        Asserts that the given card has the given number of colours
        :param card_name: The name of the card to test
        :param colour_count: The number of colours the card is expected to have
        """
        self.assert_card_attr_eq(card_name, "colour_count", colour_count)

    def assert_card_type_eq(self, card_name: str, card_type: str):
        """
        Asserts that the given card has the given type
        :param card_name: The name of the card to test
        :param card_type: The type that the card is expected to have
        """
        self.assert_card_attr_eq(card_name, "type", card_type)

    def assert_card_subtype_eq(self, card_name: str, subtype: str):
        """
        Asserts the given card has the given subtype
        :param card_name: The name of the card to test
        :param subtype: The subtype the card is expected to have
        """
        self.assert_card_attr_eq(card_name, "subtype", subtype)

    def assert_card_power_eq(self, card_name: str, power: Optional[str]):
        """
        Asserts that the given card has the given power
        :param card_name: The name of the card to test
        :param power: The power that the card should have
        """
        self.assert_card_attr_eq(card_name, "power", power)

    def assert_card_num_power_eq(self, card_name: str, num_power: float):
        """
        Asserts that the given card has the given numerical power
        :param card_name: The card's name to test
        :param num_power: The numerical power that the card should have
        """
        self.assert_card_attr_eq(card_name, "num_power", num_power)

    def assert_card_toughness_eq(self, card_name: str, toughness: Optional[str]):
        """
        Asserts that the card with the given name has the given toughness
        :param card_name: The name of the card to test
        :param toughness: the expected toughness
        """
        self.assert_card_attr_eq(card_name, "toughness", toughness)

    def assert_card_num_toughness_eq(self, card_name: str, num_toughness: float):
        """
        Asserts that the card with the given name has the given numerical toughness
        :param card_name: The name of the card to test
        :param num_toughness: the expected numerical toughness
        """
        self.assert_card_attr_eq(card_name, "num_toughness", num_toughness)

    def assert_card_loyalty_eq(self, card_name: str, loyalty: Optional[str]):
        """
        Asserts that the card with the given name has the given loyalty
        :param card_name: The name of the card to test
        :param loyalty: the expected loyalty
        """
        self.assert_card_attr_eq(card_name, "loyalty", loyalty)

    def assert_card_num_loyalty_eq(self, card_name: str, num_loyalty: int):
        """
        Asserts that the card with the given name has the given numerical loyalty
        :param card_name: The name of the card to test
        :param num_loyalty: the expected numerical loyalty
        """
        self.assert_card_attr_eq(card_name, "num_loyalty", num_loyalty)

    def assert_card_rules_eq(self, card_name: str, rules_text: Optional[str]):
        """
        Asserts that the card with the given name has the given rules
        :param card_name: The name of the card to test
        :param rules_text: the expected rules text
        """
        self.assert_card_attr_eq(card_name, "rules_text", rules_text)

    def assert_card_layout_eq(self, card_name: str, layout: str):
        """
        Asserts that the card with the given name has the given layout
        :param card_name: The name of the card to test
        :param layout: the expected layout
        """
        self.assert_card_attr_eq(card_name, "layout", layout)

    def assert_card_attr_eq(self, card_name: str, attr_name: str, attr_value):
        """
        Asserts that the card with the given name and the given attribute has the expected value
        :param card_name: The name of the card to test
        :param attr_name: The attribute to test
        :param attr_value: The expected value of the attribute
        """
        if not Card.objects.filter(name=card_name).exists():
            self.assert_true(False, f'Card "{card_name}" could not be found')
            return

        card = Card.objects.get(name=card_name)
        self.assert_obj_attr_eq(card, attr_name, attr_value)

    def assert_cardprinting_flavour_eq(
        self, card_name: str, setcode: str, flavour: Optional[str]
    ):
        """
        Asserts that the card printing of the given name and set has the given flavour text
        :param card_name: The name of the card
        :param setcode: The set the printing it in
        :param flavour: The expected flavour text of the printing
        """
        self.assert_cardprinting_attr_eq(card_name, setcode, "flavour_text", flavour)

    def assert_cardprinting_artist_eq(self, card_name: str, setcode: str, artist: str):
        """
        Asserts that the card printing of the given name and set has the given artist
        :param card_name: The name of the card to test
        :param setcode: The set the card is in te to test
        :param artist: The expected artist
        """
        self.assert_cardprinting_attr_eq(card_name, setcode, "artist", artist)

    def assert_cardprinting_attr_eq(
        self, card_name: str, setcode: str, attr_name: str, attr_value
    ):
        """
        Asserts that the card printing of the given name and set has the expected attribute value
        :param card_name: The name of the card
        :param setcode: The set of the card
        :param attr_name: The attribute name
        :param attr_value: The expected attribute value
        """
        if (
            not Card.objects.filter(name=card_name).exists()
            or not Set.objects.filter(code=setcode).exists()
            or not CardPrinting.objects.filter(
                card=Card.objects.get(name=card_name), set=Set.objects.get(code=setcode)
            )
        ):
            self.assert_true(
                False, f'Card Printing "{card_name}" in "{setcode}" could not be found'
            )
            return

        card = Card.objects.get(name=card_name)
        card_set = Set.objects.get(code=setcode)
        cardprinting = CardPrinting.objects.filter(card=card, set=card_set).first()
        self.assert_obj_attr_eq(cardprinting, attr_name, attr_value)

    def assert_obj_attr_eq(self, obj: models.Model, attr_name: str, expected):
        """
        Asserts that the attribute of the given object is equal to the given value
        :param obj: The object to test
        :param attr_name: The attribute name of the object
        :param expected: The expected value of the attribute
        """
        actual = getattr(obj, attr_name)
        self.assert_true(
            expected == actual,
            f'{obj}.{attr_name} was expected to be "{expected}", actually "{actual}"',
        )

    def assert_false(self, result: bool, message: str):
        """
        Asserts that the given condition is false
        :param result: The value to test
        :param message: The message of the test
        :return:
        """
        self.assert_true(not result, message)

    def assert_true(self, result: bool, message: str):
        """
        Given a test result, logs the message for that test if it failed
        :param result: The result of the test
        :param message: The message of the test
        """
        if result:
            self.successful_tests += 1
            print(".", end="")
        else:
            self.failed_tests += 1
            print("F", end="")
            error = {"message": message, "trace": "".join(traceback.format_stack())}
            self.error_messages.append(error)

        self.test_count += 1
        if self.test_count % 25 == 0:
            print()

        sys.stdout.flush()
