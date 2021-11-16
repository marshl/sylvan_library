"""
Module for the verify_database command
"""
# pylint: disable=too-many-lines
import math
import sys
import traceback
from typing import Optional, Any, List

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Count

from cards.models import Block, Card, CardPrinting, Rarity, Set, CardFace, Colour

WUBRG = Colour.WHITE | Colour.BLUE | Colour.BLACK | Colour.RED | Colour.GREEN

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

    def test_blocks(self) -> None:
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

        mirrodin_sets = Block.objects.get(name="Mirrodin").sets
        self.assert_true(
            mirrodin_sets.count() == 6,
            "Mirrodin should have 3 sets, but instead has: {}".format(
                mirrodin_sets.all()
            ),
        )
        time_spiral_sets = Block.objects.get(name="Time Spiral").sets
        self.assert_true(
            time_spiral_sets.count() == 7,
            "Time Spiral should have 4 sets, but instead has: {}".format(
                time_spiral_sets.all()
            ),
        )
        amonkhet_sets = Block.objects.get(name="Amonkhet").sets
        self.assert_true(
            amonkhet_sets.count() == 7,
            "Amonkhet blockshould have 5 sets, but instead has: {}".format(
                amonkhet_sets.all()
            ),
        )

    def test_sets(self) -> None:
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

    def test_rarities(self) -> None:
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

    def test_card_printings(self) -> None:
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

    def test_minimum_localisations(self) -> None:
        """
        Tests that every card has a printed language
        """
        zero_localisation_printings = CardPrinting.objects.annotate(
            localisation_count=Count("localisations")
        ).filter(localisation_count=0)
        self.assert_false(
            zero_localisation_printings.exists(),
            f"There should be at least one localisation for each printing: {zero_localisation_printings}",
        )

    def test_minimum_printings(self) -> None:
        zero_printing_cards = Card.objects.annotate(
            printing_count=Count("printings")
        ).filter(printing_count=0)
        self.assert_false(
            zero_printing_cards.exists(),
            f"Every card must have at least one printing: {zero_printing_cards}",
        )

    def test_minimum_face_printings(self) -> None:
        zero_face_printings = CardFace.objects.annotate(
            face_printing_count=Count("face_printings")
        ).filter(face_printing_count=0)
        self.assert_false(
            zero_face_printings.exists(),
            f"Every CardFace should have at least one printing: {zero_face_printings}",
        )

        zero_face_printings = CardPrinting.objects.annotate(
            face_printing_count=Count("face_printings")
        ).filter(face_printing_count=0)
        self.assert_false(
            zero_face_printings.exists(),
            f"Every CardPrinting should have at least one CardFacePrinting: {zero_face_printings}",
        )

    def test_minimum_faces(self) -> None:
        low_count_cards = (
            Card.objects.filter(
                layout__in=(
                    "split",
                    "flip",
                    "transform",
                    "adventure",
                    "modal_dfc",
                )
            )
            .annotate(face_count=Count("faces"))
            .exclude(face_count__gte=2)
        )

        self.assert_false(
            low_count_cards.exists(),
            f"Multi-faced cards should have multiple faces: {low_count_cards}",
        )

    def test_maximum_faces(self) -> None:
        high_count_single_face_cards = (
            Card.objects.exclude(
                layout__in=(
                    "split",
                    "flip",
                    "transform",
                    "meld",
                    "aftermath",
                    "adventure",
                    "modal_dfc",
                    # Not all tokens have multiple faces, but there are some dual faced tokens
                    "token",
                )
            )
            .annotate(face_count=Count("faces"))
            .exclude(face_count__lte=1)
        )
        self.assert_false(
            high_count_single_face_cards.exists(),
            f"Only two faced cards should have multiple faces: {high_count_single_face_cards}",
        )

    # def test_unique_images(self) -> None:
    #     """
    #     Tests that every printed language has a unique image path
    #     """
    #
    #     image_url_map = {}
    #     for printed_language in (
    #         CardFaceLocalisation.objects.all()#select_related(
    #             # "localisation__card_printing__card"
    #         # )
    #         # .select_related("card_printing_face__card_face")
    #         # .select_related("localisation__language")
    #         # .all()
    #     ):
    #         image_path = printed_language.get_image_path()
    #         if image_path is None:
    #             continue
    #         if image_path not in image_url_map:
    #             image_url_map[image_path] = [printed_language]
    #         else:
    #             image_url_map[image_path].append(printed_language)
    #
    #     for image_path, localisations in image_url_map.items():
    #         if len(localisations) == 1:
    #             continue
    #
    #         # Flip and split cards share the same image, so we can ignore them
    #         if not any(
    #             pl
    #             for pl in localisations
    #             if pl.card_printing.card.layout
    #             not in ["flip", "split", "aftermath", "adventure"]
    #         ):
    #             continue
    #
    #         self.assert_true(
    #             False,
    #             f"Too many printed languages for the same image path: "
    #             + f"{localisations}: {image_path}",
    #         )

    def test_card_name(self) -> None:
        """
        Test that cards of various names exist
        """
        # Normal card
        self.assert_card_exists("Animate Artifact")

        # Split card
        self.assert_card_exists("Wear // Tear")

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
        self.assert_card_exists("Homura, Human Ascendant // Homura's Essence")
        self.assert_card_exists("Aether Charge")

        # Negative tests
        self.assert_card_not_exists("Æther Charge")

    def test_card_cost(self) -> None:
        """
        Tests tje cost of various Card objects
        :return:
        """
        # Expensive card
        self.assert_card_face_cost_eq("Progenitus", "{W}{W}{U}{U}{B}{B}{R}{R}{G}{G}")

        # Lands
        self.assert_card_face_cost_eq("Temple of the False God", None)
        self.assert_card_face_cost_eq("Dryad Arbor", None)

        # Monocoloured hybrid card
        self.assert_card_face_cost_eq("Flame Javelin", "{2/R}{2/R}{2/R}")

        # Plane
        self.assert_card_face_cost_eq("Krosa", None)

        # Multi-numeral symbol cards
        self.assert_card_face_cost_eq("Gleemax", "{1000000}")
        self.assert_card_face_cost_eq("Draco", "{16}")

        # Hybrid multicoloured card
        self.assert_card_face_cost_eq("Naya Hushblade", "{R/W}{G}")

        # Half mana card
        self.assert_card_face_cost_eq("Little Girl", "{HW}")

        # Meld card
        self.assert_card_face_cost_eq("Brisela, Voice of Nightmares", None)

        # Flip card
        self.assert_card_face_cost_eq("Bushi Tenderfoot", "{W}")
        self.assert_card_face_cost_eq("Kenzo the Hardhearted", None)

        # Phyrexian mana card
        self.assert_card_face_cost_eq("Birthing Pod", "{3}{G/P}")

    def test_card_cmc(self) -> None:
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
        self.assert_card_cmc_eq("Garruk Relentless // Garruk, the Veil-Cursed", 4)

        # Meld card
        self.assert_card_cmc_eq("Brisela, Voice of Nightmares", 11)

        # Split card
        # Both Wear and Tear should have the same CMC under the new rules
        self.assert_card_cmc_eq("Wear // Tear", 3)

        # Flip card
        self.assert_card_cmc_eq("Homura, Human Ascendant // Homura's Essence", 6)

    def test_card_colour(self) -> None:
        """
        Tests the colour of various Card objects
        """

        # Mono-coloured card
        self.assert_card_face_colour_eq("Glory Seeker", Colour.WHITE)

        # Multicoloured card
        self.assert_card_face_colour_eq(
            "Dark Heart of the Wood", Colour.BLACK | Colour.GREEN
        )

        self.assert_card_face_colour_eq("Progenitus", WUBRG)
        self.assert_card_face_colour_eq("Reaper King", WUBRG)

        # Hybrid card
        self.assert_card_face_colour_eq("Azorius Guildmage", Colour.WHITE | Colour.BLUE)

        # Colour indicator cards
        self.assert_card_face_colour_eq("Transguild Courier", WUBRG)
        self.assert_card_face_colour_eq("Ghostfire", 0)
        self.assert_card_face_colour_eq("Dryad Arbor", Colour.GREEN)

        # Same colour transform card
        self.assert_card_face_colour_eq("Delver of Secrets", Colour.BLUE)
        self.assert_card_face_colour_eq("Insectile Aberration", Colour.BLUE)

        # Different colour transform card
        self.assert_card_face_colour_eq("Garruk Relentless", Colour.GREEN)
        self.assert_card_face_colour_eq(
            "Garruk, the Veil-Cursed", Colour.BLACK | Colour.GREEN
        )

        # Colour identity cards
        self.assert_card_face_colour_eq("Bosh, Iron Golem", 0)

        # Split card
        self.assert_card_face_colour_eq("Tear", Colour.WHITE)

        # Flip card
        self.assert_card_face_colour_eq("Rune-Tail, Kitsune Ascendant", Colour.WHITE)
        self.assert_card_face_colour_eq("Rune-Tail's Essence", Colour.WHITE)

        # Normal cards

    def test_card_colour_identity(self) -> None:
        """
        Tests the colour identity of various Cards
        :return:
        """

        self.assert_card_colour_identity_eq("Goblin Piker", Colour.RED)

        # Lands
        self.assert_card_colour_identity_eq("Mountain", Colour.RED)
        self.assert_card_colour_identity_eq("Polluted Delta", 0)
        self.assert_card_colour_identity_eq("Tolarian Academy", Colour.BLUE)

        # Colour indicator cards
        self.assert_card_colour_identity_eq("Ghostfire", Colour.RED)
        self.assert_card_colour_identity_eq("Dryad Arbor", Colour.GREEN)

        # Augment cards
        self.assert_card_colour_identity_eq("Half-Orc, Half-", Colour.RED)

        # Symbol in rules cards
        self.assert_card_colour_identity_eq("Bosh, Iron Golem", Colour.RED)
        self.assert_card_colour_identity_eq(
            "Dawnray Archer", Colour.WHITE | Colour.BLUE
        )
        self.assert_card_colour_identity_eq("Obelisk of Alara", WUBRG)

        # Hybrid cards
        self.assert_card_colour_identity_eq(
            "Azorius Guildmage", Colour.WHITE | Colour.BLUE
        )

        # Split cards
        self.assert_card_colour_identity_eq("Wear // Tear", Colour.WHITE | Colour.RED)

        # Flip cards
        self.assert_card_colour_identity_eq(
            "Garruk Relentless // Garruk, the Veil-Cursed", Colour.BLACK | Colour.GREEN
        )
        self.assert_card_colour_identity_eq(
            "Gisela, the Broken Blade // Brisela, Voice of Nightmares", Colour.WHITE
        )
        self.assert_card_colour_identity_eq(
            "Brisela, Voice of Nightmares", Colour.WHITE
        )

    def test_card_colour_count(self) -> None:
        """
        Tests the colour count of various cards
        """
        # Normal cards
        self.assert_card_face_colour_count_eq("Birds of Paradise", 1)
        self.assert_card_face_colour_count_eq("Edgewalker", 2)
        self.assert_card_face_colour_count_eq("Naya Hushblade", 3)
        self.assert_card_face_colour_count_eq("Temple of the False God", 0)
        self.assert_card_face_colour_count_eq("Ornithopter", 0)
        self.assert_card_face_colour_count_eq("Glint-Eye Nephilim", 4)
        self.assert_card_face_colour_count_eq("Cromat", 5)

        # Colour indicator cards
        self.assert_card_face_colour_count_eq("Evermind", 1)
        self.assert_card_face_colour_count_eq("Arlinn, Embraced by the Moon", 2)

        # Non-playable cards
        self.assert_card_face_colour_count_eq("Dance, Pathetic Marionette", 0)

    def test_card_type(self) -> None:
        """
        Test the type of various cards
        """
        self.assert_card_face_types_eq("Kird Ape", ["Creature"])
        self.assert_card_face_types_eq("Forest", ["Land"])
        self.assert_card_face_types_eq("Masticore", ["Artifact", "Creature"])
        self.assert_card_face_types_eq("Tarmogoyf", ["Creature"])
        self.assert_card_face_types_eq("Lignify", ["Tribal", "Enchantment"])
        self.assert_card_face_types_eq("Sen Triplets", ["Artifact", "Creature"])
        self.assert_card_face_types_eq("Walking Atlas", ["Artifact", "Creature"])
        self.assert_card_face_types_eq("Soul Net", ["Artifact"])
        self.assert_card_face_types_eq("Ajani Goldmane", ["Planeswalker"])
        self.assert_card_face_types_eq("Bant", ["Plane"])
        self.assert_card_face_types_eq("My Crushing Masterstroke", ["Scheme"])
        self.assert_card_face_types_eq("Nameless Race", ["Creature"])

    def test_card_subype(self) -> None:
        """
        Tests the subtype of various cards
        """
        # Single subtype
        self.assert_card_subtype_eq("Screaming Seahawk", ["Bird"])
        self.assert_card_subtype_eq("Mistform Ultimus", ["Illusion"])
        self.assert_card_subtype_eq("Forest", ["Forest"])
        # Multiple subtypes
        self.assert_card_subtype_eq("Glory Seeker", ["Human", "Soldier"])
        # Planeswalker
        self.assert_card_subtype_eq("Jace, the Mind Sculptor", ["Jace"])
        # Tribal
        self.assert_card_subtype_eq("Lignify", ["Treefolk", "Aura"])
        # None
        self.assert_card_subtype_eq("Nameless Race", [])
        self.assert_card_subtype_eq("Spellbook", [])

    def test_card_power(self) -> None:
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

    def test_card_num_power(self) -> None:
        """
        Tests the numerical power of various cards
        """
        # Normal creatures
        self.assert_card_face_num_power_eq("Stone Golem", 4)
        self.assert_card_face_num_power_eq("Progenitus", 10)
        self.assert_card_face_num_power_eq("Emrakul, the Aeons Torn", 15)

        # Infinite creatures
        self.assert_card_face_num_power_eq("Infinity Elemental", math.inf)

        # Vehicles
        self.assert_card_face_num_power_eq("Smuggler's Copter", 3)

        # Negative power creatures
        self.assert_card_face_num_power_eq("Spinal Parasite", -1)

        # Non-creatures
        self.assert_card_face_num_power_eq("Ancestral Recall", 0)

        # Misprints
        self.assert_card_face_num_power_eq("Elvish Archers", 2)

        # + Cards
        self.assert_card_face_num_power_eq("Tarmogoyf", 0)
        self.assert_card_face_num_power_eq("Haunting Apparition", 1)

    def test_card_toughness(self) -> None:
        """
        Test the stringy toughness of various cards
        """
        # Normal Cards
        self.assert_card_face_toughness_eq("Obsianus Golem", "6")
        self.assert_card_face_toughness_eq("Dryad Arbor", "1")
        self.assert_card_face_toughness_eq("Force of Savagery", "0")

        # Vehicles
        self.assert_card_face_toughness_eq("Heart of Kiran", "4")

        # Negative Cards
        self.assert_card_face_toughness_eq("Spinal Parasite", "-1")

        # + Cards
        self.assert_card_face_toughness_eq("Tarmogoyf", "1+*")
        self.assert_card_face_toughness_eq("Gaea's Avenger", "1+*")
        self.assert_card_face_toughness_eq("Half-Orc, Half-", "+1")
        self.assert_card_face_toughness_eq("S.N.O.T.", "*²")

        # Misprints
        self.assert_card_face_toughness_eq("Elvish Archers", "1")

        # Noncreature cards
        self.assert_card_face_toughness_eq("Gratuitous Violence", None)
        self.assert_card_face_toughness_eq("Ancestral Recall", None)
        self.assert_card_face_toughness_eq("Krosa", None)

    def test_card_num_toughness(self) -> None:
        """
        Test the numerical toughness of various cards
        """
        # Normal Cards
        self.assert_card_face_num_toughness_eq("Wall of Fire", 5)
        self.assert_card_face_num_toughness_eq("Daru Lancer", 4)
        self.assert_card_face_num_toughness_eq("Tree of Redemption", 13)

        # Vehicles
        self.assert_card_face_num_toughness_eq("Skysovereign, Consul Flagship", 5)

        # Negative cards
        self.assert_card_face_num_toughness_eq("Spinal Parasite", -1)

        # Misprints
        self.assert_card_face_num_toughness_eq("Elvish Archers", 1)

        # + Cards
        self.assert_card_face_num_toughness_eq("Tarmogoyf", 1)
        self.assert_card_face_num_toughness_eq("Angry Mob", 2)
        self.assert_card_face_num_toughness_eq("S.N.O.T.", 0)

    def test_loyalty(self) -> None:
        """
        Test the loyalty of various cards
        """
        # Planeswalkers
        self.assert_cardface_loyalty_eq("Ajani Goldmane", "4")

        # Flipwalkers
        self.assert_cardface_loyalty_eq("Chandra, Fire of Kaladesh", None)
        self.assert_cardface_loyalty_eq("Chandra, Roaring Flame", "4")

        # Non-planeswalkers
        self.assert_cardface_loyalty_eq("Glimmervoid Basin", None)
        self.assert_cardface_loyalty_eq("Megatog", None)
        self.assert_cardface_loyalty_eq("Urza", None)

    def test_card_num_loyalty(self) -> None:
        """
        Tests the numerical loyalty of various cards
        """
        # Planeswalkers
        self.assert_card_face_num_loyalty_eq("Ajani Goldmane", 4)

        # Flipwalkers
        self.assert_card_face_num_loyalty_eq("Chandra, Fire of Kaladesh", 0)
        self.assert_card_face_num_loyalty_eq("Chandra, Roaring Flame", 4)

        # Non-planeswalkers
        self.assert_card_face_num_loyalty_eq("Glimmervoid Basin", 0)
        self.assert_card_face_num_loyalty_eq("Megatog", 0)
        self.assert_card_face_num_loyalty_eq("Urza", 0)

    def test_card_rules_text(self) -> None:
        """
        Tests the rules texts
        """
        self.assert_card_face_rules_eq("Grizzly Bears", None)
        self.assert_card_face_rules_eq("Elite Vanguard", None)
        # self.assert_card_face_rules_eq("Forest", "({T}: Add {G}.)")
        self.assert_card_face_rules_eq("Snow-Covered Swamp", "({T}: Add {B}.)")

        self.assert_card_face_rules_eq("Air Elemental", "Flying")
        self.assert_card_face_rules_eq("Thunder Spirit", "Flying, first strike")
        self.assert_card_face_rules_eq("Dark Ritual", "Add {B}{B}{B}.")
        self.assert_card_face_rules_eq("Palladium Myr", "{T}: Add {C}{C}.")

    def test_card_layouts(self) -> None:
        """
        Tests the layouts of various Card objects
        """
        self.assert_card_layout_eq("Glory Seeker", "normal")
        self.assert_card_layout_eq("Hit // Run", "split")
        self.assert_card_layout_eq("Hired Muscle // Scarmaker", "flip")
        self.assert_card_layout_eq(
            "Delver of Secrets // Insectile Aberration", "transform"
        )
        self.assert_card_layout_eq("Mount Keralia", "planar")
        self.assert_card_layout_eq("Glimmervoid Basin", "planar")
        self.assert_card_layout_eq("I Bask in Your Silent Awe", "scheme")
        self.assert_card_layout_eq("Every Hope Shall Vanish", "scheme")
        self.assert_card_layout_eq("Time Distortion", "planar")
        self.assert_card_layout_eq("Echo Mage", "leveler")
        self.assert_card_layout_eq("Caravan Escort", "leveler")
        self.assert_card_layout_eq("Birds of Paradise Avatar", "vanguard")
        self.assert_card_layout_eq("Gix", "vanguard")
        self.assert_card_layout_eq(
            "Gisela, the Broken Blade // Brisela, Voice of Nightmares", "meld"
        )
        self.assert_card_layout_eq(
            "Bruna, the Fading Light // Brisela, Voice of Nightmares", "meld"
        )
        self.assert_card_layout_eq("Brisela, Voice of Nightmares", "meld")

    def test_cardprinting_flavour(self) -> None:
        """
        Tests the flavour texts of various CardPrintings
        """
        self.assert_cardfaceprinting_flavour_eq(
            "Goblin Chieftain",
            "M10",
            '"We are goblinkind, heirs to the mountain empires of chieftains past. '
            + 'Rest is death to us, and arson is our call to war."',
        )

        self.assert_cardfaceprinting_flavour_eq(
            "Goblin Chieftain", "M12", '''"It's time for the 'Smash, Smash' song!"'''
        )

        self.assert_cardfaceprinting_flavour_eq("Land Aid '04", "UNH", None)
        self.assert_cardfaceprinting_flavour_eq(
            "Goblin Balloon Brigade",
            "M11",
            '"The enemy is getting too close! Quick! Inflate the toad!"',
        )
        self.assert_cardfaceprinting_flavour_eq(
            "Lhurgoyf",
            "ICE",
            """"Ach! Hans, run! It's the Lhurgoyf!"
—Saffi Eriksdotter, last words""",
        )

        self.assert_cardfaceprinting_flavour_eq("Magma Mine", "VIS", "BOOM!")

    def test_cardprinting_artist(self) -> None:
        """
        Tests the properties of CardPrinting artists
        """
        # Misprint
        self.assert_card_printing_artist_eq("Animate Artifact", "LEA", "Douglas Shuler")
        self.assert_card_printing_artist_eq("Benalish Hero", "LEB", "Douglas Shuler")

        # Combination
        self.assert_card_printing_artist_eq(
            "Wound Reflection", "SHM", "Terese Nielsen & Ron Spencer"
        )

        # Unhinged
        self.assert_card_printing_artist_eq(
            "Persecute Artist", "UNH", "Rebecca “Don't Mess with Me” Guay"
        )
        self.assert_card_printing_artist_eq(
            "Fascist Art Director", "UNH", "Edward P. “Feed Me” Beard, Jr."
        )
        self.assert_card_printing_artist_eq("Atinlay Igpay", "UNH", "Evkay Alkerway")

    def test_cardprinting_collectornum(self) -> None:
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

    def assert_card_face_cost_eq(self, card_name: str, cost: Optional[str]):
        """
        Asserts that the given card has the given cost
        :param card_name: The name of the card to test
        :param cost: The expected cost of the card
        """
        self.assert_card_face_attr_eq(card_name, "mana_cost", cost)

    def assert_card_cmc_eq(self, card_name: str, cmc: float):
        """
        Asserts that the given card has the given converted man cost
        :param card_name: The name of the card to test
        :param cmc: The expected converted mana cost of the card
        """
        self.assert_card_attr_eq(card_name, "converted_mana_cost", cmc)

    def assert_card_face_colour_eq(self, card_face_name: str, colours: int):
        """
        Asserts that the card with the given name has the given colours
        :param card_face_name: The name of the card to test
        :param colours: the expected colours
        """
        face = CardFace.objects.get(name=card_face_name)
        actual = int(face.colour)
        self.assert_true(
            colours == actual,
            f'{card_face_name}.colours was expected to be "{colours}", actually "{actual}"',
        )

    def assert_card_colour_identity_eq(
        self, card_name: str, colour_identity: int
    ) -> None:
        """
        Asserts that the card with the given name has the given colour identity
        :param card_name: The name of the card to test
        :param colour_identity: the expected colour_identity
        """
        actual = int(Card.objects.get(name=card_name).colour_identity)
        self.assert_true(
            colour_identity == actual,
            f"{card_name}.colour_identity was expected "
            f'to be "{colour_identity}", actually "{actual}"',
        )

    def assert_card_face_colour_count_eq(self, card_face_name: str, colour_count: int):
        """
        Asserts that the given card has the given number of colours
        :param card_face_name: The name of the card to test
        :param colour_count: The number of colours the card is expected to have
        """
        self.assert_card_face_attr_eq(card_face_name, "colour_count", colour_count)

    def assert_card_face_types_eq(self, card_face_name: str, card_types: List[str]):
        """
        Asserts that the given card has the given type
        :param card_face_name: The name of the card to test
        :param card_types: The type that the card is expected to have
        """
        card_face = CardFace.objects.get(name=card_face_name)
        actual = card_face.types.values_list("name", flat=True)
        self.assert_true(
            set(card_types) == set(actual),
            f"Expected {card_face_name} to have the types {card_types} but instead got {actual}",
        )

    def assert_card_subtype_eq(self, card_face_name: str, subtypes: List[str]):
        """
        Asserts the given card has the given subtype
        :param card_face_name: The name of the card to test
        :param subtypes: The subtype the card is expected to have
        """
        card_face = CardFace.objects.get(name=card_face_name)
        actual = set(card_face.subtypes.values_list("name", flat=True))
        self.assert_true(
            set(subtypes) == actual,
            f"Expected {card_face_name} to have the subtypes {subtypes} but instead got {actual}",
        )

    def assert_card_power_eq(self, card_name: str, power: Optional[str]):
        """
        Asserts that the given card has the given power
        :param card_name: The name of the card to test
        :param power: The power that the card should have
        """
        self.assert_card_face_attr_eq(card_name, "power", power)

    def assert_card_face_num_power_eq(self, card_name: str, num_power: float):
        """
        Asserts that the given card has the given numerical power
        :param card_name: The card's name to test
        :param num_power: The numerical power that the card should have
        """
        self.assert_card_face_attr_eq(card_name, "num_power", num_power)

    def assert_card_face_toughness_eq(self, card_name: str, toughness: Optional[str]):
        """
        Asserts that the card with the given name has the given toughness
        :param card_name: The name of the card to test
        :param toughness: the expected toughness
        """
        self.assert_card_face_attr_eq(card_name, "toughness", toughness)

    def assert_card_face_num_toughness_eq(self, card_name: str, num_toughness: float):
        """
        Asserts that the card with the given name has the given numerical toughness
        :param card_name: The name of the card to test
        :param num_toughness: the expected numerical toughness
        """
        self.assert_card_face_attr_eq(card_name, "num_toughness", num_toughness)

    def assert_cardface_loyalty_eq(self, card_face_name: str, loyalty: Optional[str]):
        """
        Asserts that the card with the given name has the given loyalty
        :param card_face_name: The name of the card face to test
        :param loyalty: the expected loyalty
        """
        self.assert_card_face_attr_eq(card_face_name, "loyalty", loyalty)

    def assert_card_face_num_loyalty_eq(self, card_name: str, num_loyalty: int):
        """
        Asserts that the card with the given name has the given numerical loyalty
        :param card_name: The name of the card to test
        :param num_loyalty: the expected numerical loyalty
        """
        self.assert_card_face_attr_eq(card_name, "num_loyalty", num_loyalty)

    def assert_card_face_rules_eq(self, card_name: str, rules_text: Optional[str]):
        """
        Asserts that the card with the given name has the given rules
        :param card_name: The name of the card to test
        :param rules_text: the expected rules text
        """
        self.assert_card_face_attr_eq(card_name, "rules_text", rules_text)

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

    def assert_card_face_attr_eq(
        self, card_face_name: str, attr_name: str, attr_value: Any
    ):
        """
        Asserts that the card with the given name and the given attribute has the expected value
        :param card_face_name: The name of the card to test
        :param attr_name: The attribute to test
        :param attr_value: The expected value of the attribute
        """
        try:
            card_face = CardFace.objects.get(name=card_face_name)
            self.assert_obj_attr_eq(card_face, attr_name, attr_value)
        except CardFace.DoesNotExist:
            self.assert_true(False, f'Card "{card_face_name}" could not be found')

    def assert_cardfaceprinting_flavour_eq(
        self, card_face_name: str, setcode: str, flavour: Optional[str]
    ):
        """
        Asserts that the card printing of the given name and set has the given flavour text
        :param card_face_name: The name of the card face
        :param setcode: The set the printing it in
        :param flavour: The expected flavour text of the printing
        """
        self.assert_cardfaceprinting_attr_eq(
            card_face_name, setcode, "flavour_text", flavour
        )

    def assert_card_printing_artist_eq(
        self, card_face_name: str, setcode: str, artist: str
    ):
        """
        Asserts that the card printing of the given name and set has the given artist
        :param card_face_name: The name of the card to test
        :param setcode: The set the card is in te to test
        :param artist: The expected artist
        """
        self.assert_cardfaceprinting_attr_eq(card_face_name, setcode, "artist", artist)

    def assert_card_printing_attr_eq(
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

    def assert_cardfaceprinting_attr_eq(
        self, card_face_name: str, setcode: str, attr_name: str, attr_value: Any
    ):
        """
        Asserts that the card printing of the given name and set has the expected attribute value
        :param card_face_name: The name of the card face
        :param setcode: The set of the card
        :param attr_name: The attribute name
        :param attr_value: The expected attribute value
        """
        try:
            card_face = CardFace.objects.get(name=card_face_name)
            card_set = Set.objects.get(code=setcode)
            card_face_printing = card_face.face_printings.get(
                card_printing__set=card_set
            )
        except (CardFace.DoesNotExist, Set.DoesNotExist):
            self.assert_true(
                False,
                f'CardFacePrinting "{card_face_name}" in "{setcode}" could not be found',
            )
            return
        self.assert_obj_attr_eq(card_face_printing, attr_name, attr_value)

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
