import json
import logging
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from spellbook.models import Card, CardPrinting, CardPrintingLanguage
from spellbook.models import PhysicalCard
from spellbook.models import CardRuling, Rarity, Block
from spellbook.models import Set, Language
from spellbook.management.commands import _parse, _paths, _colour


class Command(BaseCommand):
    help = 'Verifies that database update was successful'

    def handle(self, *args, **options):
        methods = [method_name for method_name in dir(self)
                   if callable(getattr(self, method_name)) and method_name.startswith('test')]
        for method in methods:
            (getattr(self, method))()

    def test_tarmogoyf_exists(self):
        assert Card.objects.filter(name='Tarmogoyf').exists()

    def test_blocks(self):
        assert Block.objects.filter(name='Ice Age').exists(), 'Ice Age block should exist'
        assert Block.objects.filter(name='Ravnica').exists(), 'Ravnica block should exist'
        assert Block.objects.filter(name='Ixalan').exists(), 'Ixalan block should exist'
        assert not Block.objects.filter(name='Weatherlight').exists(), 'Weatherlight block should not exist'

        assert Block.objects.get(name='Ice Age').release_date < Block.objects.get(
            name='Onslaught').release_date, 'Ice Age should be released before Onslaught'

        assert Block.objects.get(name='Mirrodin').set_set.count() == 3, 'Mirrodin should have 3 sets'
        assert Block.objects.get(name='Time Spiral').set_set.count() == 4, 'Time Spiral should have 4 sets'
        assert Block.objects.get(name='Amonkhet').set_set.count() == 3, \
            'Amonkhet should have 3 sets (including Welcome Deck 2017)'

    def test_sets(self):
        assert not Set.objects.filter(name='Worlds').exists(), 'The Worlds set should have been filtered out'
        assert not Set.objects.filter(code__startswith='p').exists(), \
            'Sets that start with "p" should have been filtered out'

        assert Set.objects.get(code='ONS').block.name == 'Onslaught', 'Onslaught should be in the Onslaught block'
        assert Set.objects.get(code='WTH').block.name == 'Mirage', 'Weatherlight should be in the Mirage block'
        assert Set.objects.get(code='CSP').block.name == 'Ice Age', 'Coldsnap should be in the Ice Age block'

    def test_rarities(self):
        assert Rarity.objects.filter(symbol='R').exists(), 'The rare rarity should exist'
        assert Rarity.objects.get(symbol='C').display_order < Rarity.objects.get(symbol='U').display_order, \
            'Common rarity should be displayed before uncommon rarity'

    def test_card_name(self):
        assert Card.objects.get(name='Animate Artifact'), 'Animate Artifact should exist'
        assert Card.objects.get(name='Aether Charge'), 'Aether Charge should exist'
        assert Card.objects.filter(name='The Ultimate Nightmare of Wizards of the Coast® Customer Service').exists(), \
            'The Ultimate Nightmare of Wizards of the Coast® Customer Service should exist'

        assert Card.objects.filter(name='Wear').exists(), 'Wear should exist'
        assert Card.objects.filter(name='Jötun Grunt').exists(), 'Jötun Grunt should exist'
        assert Card.objects.filter(name='"Ach! Hans, Run!"').exists(), '"Ach! Hans, Run!" should exist'
        assert Card.objects.filter(name='_____').exists(), '_____ should exist'
        assert Card.objects.filter(name='Homura, Human Ascendant').exists(), 'Homura, Human Ascendant should exist'

        # Negative tests
        assert not Card.objects.filter(name='Splendid Genesis').exists(), 'Splendid Genesis should not exist'
        assert not Card.objects.filter(name='Æther Charge').exists(), 'Æther Charge should not exist'

    def test_card_cost(self):
        assert Card.objects.get(name='Progenitus').cost == '{W}{W}{U}{U}{B}{B}{R}{R}{G}{G}', \
            'Progenitus cost is incorrect'

        assert Card.objects.get(name='Dryad Arbor').cost is None, 'Dryad Arbor should have no mana cost'
        assert Card.objects.get(name='Flame Javelin').cost == '{2/R}{2/R}{2/R}', 'Flame Javelins cost is incorrect'
        assert Card.objects.get(name='Krosa').cost is None, 'Krosa should have no mana cost'
        assert Card.objects.get(name='Gleemax').cost == '{1000000}', 'Gleemax has the wrong mana cost'
        assert Card.objects.get(name='Naya Hushblade').cost == '{R/W}{G}', 'Naya Hushblade has the wrong mana cost'
        assert Card.objects.get(name='Little Girl').cost == '{hw}', 'Little Girl has the wrong mana cost'
        assert Card.objects.get(name='Brisela, Voice of Nightmares').cost is None, 'Brisela should have no mana cost'
        assert Card.objects.get(name='Bushi Tenderfoot').cost == '{W}', 'Bushi Tenerfoot has the wrong cost'
        assert Card.objects.get(name='Kenzo the Hardhearted').cost == '{W}', 'Kezno has the wrong mana cost'
        assert Card.objects.get(name='Birthing Pod').cost == '{3}{G/P}', 'Birthing Pod has the wrong mana cost'

    def test_card_cmc(self):
        assert Card.objects.get(name='Tarmogoyf').cmc == 2, 'Tarmogoyf should have a cmc of 2'
        assert Card.objects.get(name='Black Lotus').cmc == 0, 'Black Lotus should have a cmc of 0'
        assert Card.objects.get(name='Living End').cmc == 0, 'Living End should have a cmc of 0'
        assert Card.objects.get(name='Reaper King').cmc == 10, 'Reaper King should have a cmc of 10'
        assert Card.objects.get(name='Little Girl').cmc == 0.5, 'Little Girl should have a cmc of 0.5'
        assert Card.objects.get(name='Flame Javelin').cmc == 6, 'Flame Javelin should have a cmc of 6'
        assert Card.objects.get(name='Gleemax').cmc == 1000000, 'Gleemax should have a cmc of 1000000'
        assert Card.objects.get(name='Birthing Pod').cmc == 4, 'Birthing Pod should have a cmc of 4'
        assert Card.objects.get(name='Blinkmoth Infusion').cmc == 14, 'Blinkmoth Infusion should have a cmc of 14'
        assert Card.objects.get(name='Dryad Arbor').cmc == 0, 'Dryad Arbor should have a cmc of 0'
        assert Card.objects.get(name='Kozilek, the Great Distortion').cmc == 10, \
            'Kozilek the Great Distortion should have a cmc of 10'
        assert Card.objects.get(name='Krosa').cmc == 0, 'Krosa should have a cmc of 0'
        assert Card.objects.get(name='Comet Storm').cmc == 2, 'Comet STorm should have a cmc of 2'
        assert Card.objects.get(name='Garruk Relentless').cmc == 4, 'Garruk Relentless should have a cmc of 4'
        assert Card.objects.get(name='Garruk, the Veil-Cursed').cmc == 4, \
            'Garruk, the Veil-Cursed should have a cmc of 4'
        assert Card.objects.get(name='Brisela, Voice of Nightmares').cmc == 11, 'Brisela should have a cmc of 11'
        assert Card.objects.get(name='Wear').cmc == 2, 'Wear should have a cmc of 2'
        assert Card.objects.get(name='Homura\'s Essence').cmc == 6, 'Homras Essence should have a cmc of 6'

    def test_card_color(self):
        white = colour.colour_codes_to_flags(['W'])
        blue = colour.colour_codes_to_flags(['U'])
        green = colour.colour_codes_to_flags(['G'])
        white_blue = colour.colour_codes_to_flags(['W', 'U'])
        black_green = colour.colour_codes_to_flags(['B', 'G'])
        wubrg = colour.colour_codes_to_flags(['W', 'U', 'B', 'R', 'G'])

        # Monocoloured card
        assert Card.objects.get(name='Glory Seeker').colour == white, 'Glory Seeker should be white'

        # Multicoloured card
        assert Card.objects.get(name='Dark Heart of the Wood').colour == black_green, \
            'Dark Heart of the Wood should be black-green'
        assert Card.objects.get(name='Progenitus').colour == wubrg, 'Progenitus should be all colours'
        assert Card.objects.get(name='Reaper King').colour == wubrg, 'Reaper King should be all colours'

        # Hybrid card
        assert Card.objects.get(name='Azorius Guildmage').colour == white_blue, 'Azorius Guildmage should be white-blue'

        # Colour indicator cards
        assert Card.objects.get(name='Transguild Courier').colour == wubrg, 'Transguild Courier should be all colours'
        assert Card.objects.get(name='Ghostfire').colour == 0, 'Ghostfire should be colourless'
        assert Card.objects.get(name='Dryad Arbor').colour == green, 'Dryad Arbor should be green'

        # Same colour transform card
        assert Card.objects.get(name='Delver of Secrets').colour == blue, 'Delver of Secrets should be blue'
        assert Card.objects.get(name='Insectile Aberration').colour == blue, 'Insectile Aberration should be blue'

        # Different colour transform card
        assert Card.objects.get(name='Garruk Relentless').colour == green, 'Garruk Relentless should be green'
        assert Card.objects.get(name='Garruk, the Veil-Cursed').colour == black_green, \
            'Garruk, the Veil-Cursed should be black green'

        # Colour identity cards
        assert Card.objects.get(name='Bosh, Iron Golem').colour == 0, 'Bosh should be colourless'

        # Split card
        assert Card.objects.get(name='Tear').colour == white, 'Tear should be white'

        # Flip card
        assert Card.objects.get(name='Rune-Tail, Kitsune Ascendant').colour == white, \
            'Rune-Tail, Kitsune Ascendant should be white'
        assert Card.objects.get(name='Rune-Tail\'s Essence').colour == white, 'Rune-Tail\'s Essence should be white'
