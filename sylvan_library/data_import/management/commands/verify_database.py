from django.core.management.base import BaseCommand

from cards.models import *
from cards import colour


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

        assert Block.objects.get(name='Mirrodin').sets.count() == 3, 'Mirrodin should have 3 sets'
        assert Block.objects.get(name='Time Spiral').sets.count() == 4, 'Time Spiral should have 4 sets'
        assert Block.objects.get(name='Amonkhet').sets.count() == 3, \
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
        # Normal card
        assert Card.objects.get(name='Animate Artifact'), 'Animate Artifact should exist'

        # Split card
        assert Card.objects.filter(name='Wear').exists(), 'Wear should exist'

        # UTF-8
        assert Card.objects.filter(name='Jötun Grunt').exists(), 'Jötun Grunt should exist'
        assert Card.objects.get(name='Aether Charge'), 'Aether Charge should exist'

        # Un-names
        assert Card.objects.filter(name='_____').exists(), '_____ should exist'
        assert Card.objects.filter(name='"Ach! Hans, Run!"').exists(), '"Ach! Hans, Run!" should exist'
        assert Card.objects.filter(name='The Ultimate Nightmare of Wizards of the Coast® Customer Service').exists(), \
            'The Ultimate Nightmare of Wizards of the Coast® Customer Service should exist'

        # Fip card
        assert Card.objects.filter(name='Homura, Human Ascendant').exists(), 'Homura, Human Ascendant should exist'

        # Negative tests
        assert not Card.objects.filter(name='Splendid Genesis').exists(), 'Splendid Genesis should not exist'
        assert not Card.objects.filter(name='Æther Charge').exists(), 'Æther Charge should not exist'

    def test_card_cost(self):
        # Expensive card
        assert Card.objects.get(name='Progenitus').cost == '{W}{W}{U}{U}{B}{B}{R}{R}{G}{G}', \
            'Progenitus cost is incorrect'

        # Lands
        assert Card.objects.get(name='Forest').cost is None, 'Dryad Arbor should have no mana cost'
        assert Card.objects.get(name='Dryad Arbor').cost is None, 'Dryad Arbor should have no mana cost'

        # Monocoloured hybrid card
        assert Card.objects.get(name='Flame Javelin').cost == '{2/R}{2/R}{2/R}', 'Flame Javelins cost is incorrect'

        # Plane
        assert Card.objects.get(name='Krosa').cost is None, 'Krosa should have no mana cost'

        # Multi-numeral symbol cards
        assert Card.objects.get(name='Gleemax').cost == '{1000000}', 'Gleemax has the wrong mana cost'
        assert Card.objects.get(name='Draco').cost == '{16}', 'Draco has the wrong mana cost'

        # Hybrid multicoloured card
        assert Card.objects.get(name='Naya Hushblade').cost == '{R/W}{G}', 'Naya Hushblade has the wrong mana cost'

        # Half mana card
        assert Card.objects.get(name='Little Girl').cost == '{hw}', 'Little Girl has the wrong mana cost'

        # Meld card
        assert Card.objects.get(name='Brisela, Voice of Nightmares').cost is None, 'Brisela should have no mana cost'

        # Flip card
        assert Card.objects.get(name='Bushi Tenderfoot').cost == '{W}', 'Bushi Tenerfoot has the wrong cost'
        assert Card.objects.get(name='Kenzo the Hardhearted').cost == '{W}', 'Kezno has the wrong mana cost'

        # Phyrexian mana card
        assert Card.objects.get(name='Birthing Pod').cost == '{3}{G/P}', 'Birthing Pod has the wrong mana cost'

    def test_card_cmc(self):
        # Normal cards
        assert Card.objects.get(name='Tarmogoyf').cmc == 2, 'Tarmogoyf should have a cmc of 2'
        assert Card.objects.get(name='Black Lotus').cmc == 0, 'Black Lotus should have a cmc of 0'

        # Costless card
        assert Card.objects.get(name='Living End').cmc == 0, 'Living End should have a cmc of 0'

        # Half mana card
        assert Card.objects.get(name='Little Girl').cmc == 0.5, 'Little Girl should have a cmc of 0.5'

        # Monocoloured hybrid cards
        assert Card.objects.get(name='Reaper King').cmc == 10, 'Reaper King should have a cmc of 10'
        assert Card.objects.get(name='Flame Javelin').cmc == 6, 'Flame Javelin should have a cmc of 6'

        # High cost cards
        assert Card.objects.get(name='Blinkmoth Infusion').cmc == 14, 'Blinkmoth Infusion should have a cmc of 14'
        assert Card.objects.get(name='Gleemax').cmc == 1000000, 'Gleemax should have a cmc of 1000000'

        # Phyrexian mana card
        assert Card.objects.get(name='Birthing Pod').cmc == 4, 'Birthing Pod should have a cmc of 4'

        # Land
        assert Card.objects.get(name='Dryad Arbor').cmc == 0, 'Dryad Arbor should have a cmc of 0'

        # Colourless mana card
        assert Card.objects.get(name='Kozilek, the Great Distortion').cmc == 10, \
            'Kozilek the Great Distortion should have a cmc of 10'

        # Plane
        assert Card.objects.get(name='Krosa').cmc == 0, 'Krosa should have a cmc of 0'

        # X cost card
        assert Card.objects.get(name='Comet Storm').cmc == 2, 'Comet STorm should have a cmc of 2'

        # Transform card
        assert Card.objects.get(name='Garruk Relentless').cmc == 4, 'Garruk Relentless should have a cmc of 4'
        assert Card.objects.get(name='Garruk, the Veil-Cursed').cmc == 4, \
            'Garruk, the Veil-Cursed should have a cmc of 4'

        # Meld card
        assert Card.objects.get(name='Brisela, Voice of Nightmares').cmc == 11, 'Brisela should have a cmc of 11'

        # Split card
        assert Card.objects.get(name='Wear').cmc == 2, 'Wear should have a cmc of 2'

        # Flip card
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

    def test_card_colour_identity(self):
        white = colour.colour_codes_to_flags(['W'])
        blue = colour.colour_codes_to_flags(['U'])
        red = colour.colour_codes_to_flags(['R'])
        green = colour.colour_codes_to_flags(['G'])
        white_blue = colour.colour_codes_to_flags(['W', 'U'])
        black_green = colour.colour_codes_to_flags(['B', 'G'])
        wubrg = colour.colour_codes_to_flags(['W', 'U', 'B', 'R', 'G'])

        # Normal cards
        assert Card.objects.get(name='Goblin Piker').colour_identity == red, 'Goblin Piker should be red'

        # Lands
        assert Card.objects.get(name='Mountain').colour_identity == red, 'Mountain should be red'
        assert Card.objects.get(name='Polluted Delta').colour_identity == 0, \
            'Polluted Delta should have no colour identity'
        assert Card.objects.get(name='Tolarian Academy').colour_identity == blue, 'Tolarian Academy should be blue'

        # Colour indicator cards
        assert Card.objects.get(name='Ghostfire').colour_identity == red, 'Ghostfire should be red'
        assert Card.objects.get(name='Dryad Arbor').colour_identity == green, 'Dryad Arbor should be green'

        # Augment cards
        assert Card.objects.get(name='Half-Orc, Half-').colour_identity == red, 'Half-OrdHal- should be red'

        # Symbol in rules cards
        assert Card.objects.get(name='Bosh, Iron Golem').colour_identity == red, 'Bosh, Iron Golem should be red'
        assert Card.objects.get(name='Dawnray Archer').colour_identity == white_blue, \
            'Dawnray Archer should be white-blue'
        assert Card.objects.get(name='Obelisk of Alara').colour_identity == wubrg, \
            'Obelisk of Alara should be all colours'

        # Hybrid cards
        assert Card.objects.get(name='Azorius Guildmage').colour_identity == white_blue, \
            'Azorius guildmage should be white-blue'

        # Flip cards
        assert Card.objects.get(name='Garruk Relentless').colour_identity == black_green, \
            'Garruk Relentless should be black-green'
        assert Card.objects.get(name='Garruk, the Veil-Cursed').colour_identity == black_green, \
            'Garruk, the Veil-Cursed should be black-green'

        assert Card.objects.get(name='Gisela, the Broken Blade').colour_identity == white, \
            'Gisela, Blade of Goldnight should be white'
        assert Card.objects.get(name='Brisela, Voice of Nightmares').colour_identity == white, \
            'Brisela, Voice of Nightmares should be white'

    def test_card_colour_count(self):
        # Normal cards
        assert Card.objects.get(name='Birds of Paradise').colour_count == 1, 'Birds of Paradise should have one colour'
        assert Card.objects.get(name='Edgewalker').colour_count == 2, 'Edgewalker should two colours'
        assert Card.objects.get(name='Naya Hushblade').colour_count == 3, 'Naya Hushblade should have 3 colours'
        assert Card.objects.get(name='Swamp').colour_count == 0, 'Swamp should have no colours'
        assert Card.objects.get(name='Ornithopter').colour_count == 0, 'Ornithopter should have no colours'
        assert Card.objects.get(name='Glint-Eye Nephilim').colour_count == 4, 'Glint-Eye Nephilim should have 4 colours'
        assert Card.objects.get(name='Cromat').colour_count == 5, 'Cromat should have 5 colours'

        # Colour indicator cards
        assert Card.objects.get(name='Evermind').colour_count == 1, 'Evermind should have 1 colour'
        assert Card.objects.get(name='Arlinn, Embraced by the Moon').colour_count == 2, 'Arlinn should have 2 colours'

        # Non-playable cards
        assert Card.objects.get(name='Dance, Pathetic Marionette').colour_count == 0, 'Schemes should have no colour'

    def test_card_type(self):
        assert Card.objects.get(name='Kird Ape').type == 'Creature', 'Kird Ape should be a creature'
        assert Card.objects.get(name='Forest').type == 'Basic Land', 'Forest should be a Basic Land'
        assert Card.objects.get(name='Masticore').type == 'Artifact Creature', \
            'Masticore should be an artifact creature'
        assert Card.objects.get(name='Tarmogoyf').type == 'Creature', 'Tarmogoyf should be a creature'
        assert Card.objects.get(name='Lignify').type == 'Tribal Enchantment', 'Lifnify should be a Tribal Enchantment'
        assert Card.objects.get(name='Sen Triplets').type == 'Legendary Artifact Creature', \
            'Sen Triplets should be a Legendary Artifact Creature'
        assert Card.objects.get(name='Walking Atlas').type == 'Artifact Creature', \
            'Walking Atlas should be an artifact creature'

        assert Card.objects.get(name='Soul Net').type == 'Artifact', 'Soul Net should be an artifact'
        assert Card.objects.get(name='Ajani Goldmane').type == 'Legendary Planeswalker', \
            'Ajani should be a Legendary Planeswalker'
        assert Card.objects.get(name='Bant').type == 'Plane', 'Bant should be a Plane'
        assert Card.objects.get(name='My Crushing Masterstroke').type == 'Scheme', \
            'My Crushing Masterstroke should be a scheme'

        assert Card.objects.get(name='Nameless Race').type == 'Creature', 'Nameless race should be a creature'

    def test_card_subype(self):
        assert Card.objects.get(name='Screaming Seahawk').subtype == 'Bird', 'Screaming Sehawk should be a bird'
        assert Card.objects.get(name='Jace, the Mind Sculptor').subtype == 'Jace', \
            'Jace, the Mind Sculptor should be a Jace'
        assert Card.objects.get(name='Mistform Ultimus').subtype == 'Illusion', 'Mistform Ultimus should be an illusion'
        assert Card.objects.get(name='Lignify').subtype == 'Treefolk Aura', 'Lignify should be a treefolk aura'
        assert Card.objects.get(name='Nameless Race').subtype is None, 'Nameless Race should have no subtype'
        assert Card.objects.get(name='Forest').subtype == 'Forest', 'Forest should be a Forest'
        assert Card.objects.get(name='Spellbook').subtype is None, 'Spellbook should have no subtype'

    def test_card_power(self):
        # Normal Cards
        assert Card.objects.get(name='Birds of Paradise').power == '0', 'Birds of Paradise should have a power of 0'
        assert Card.objects.get(name='Dryad Arbor').power == '1', 'Dryad Arbor should have 1 power'
        assert Card.objects.get(name='Juggernaut').power == '5', 'Juggernaut should have 5 power'

        # Vehicles
        assert Card.objects.get(name='Irontread Crusher').power == '6', 'Irontread Crusher should have 6 power'

        # Negative Cards
        assert Card.objects.get(name='Char-Rumbler').power == '-1', 'Char-Rumbler should have a power of -1'
        assert Card.objects.get(name='Spinal Parasite').power == '-1', 'Spinal Parasite should have a power of -1'

        # + Cards
        assert Card.objects.get(name='Tarmogoyf').power == '*', "Tarmogoyf should have a power of *"
        assert Card.objects.get(name='Gaea\'s Avenger').power == '1+*', 'Gaea\'s Avenger should have a power of 1+*'
        assert Card.objects.get(name='Zombified').power == '+2', 'Zombified should have a power of +2'

        # Noncreature cards
        assert Card.objects.get(name='Ancestral Recall').power is None, 'Ancestral recall should have no power'
        assert Card.objects.get(name='Krosa').power is None, 'Krosa should have no power'
        assert Card.objects.get(name='Gratuitous Violence').power is None, 'Gratuitous Violence should have no power'

    def test_card_toughness(self):

        # Normal Cards
        assert Card.objects.get(name='Obsianus Golem').toughness == '6', 'Obsianus Golem should have 6 toughness'
        assert Card.objects.get(name='Dryad Arbor').toughness == '1', 'Dryad Arbor should have 1 toughness'
        assert Card.objects.get(name='Force of Savagery').toughness == '0', 'Force of Savagery should have 0 toughness'

        # Vehicles
        assert Card.objects.get(name='Heart of Kiran').toughness == '4', 'Heart of Kiran should have 4 toughness'

        # Negative Cards
        assert Card.objects.get(name='Char-Rumbler').power == '-1', 'Char-Rumbler should have a power of -1'
        assert Card.objects.get(name='Spinal Parasite').toughness == '-1', 'Spinal Parasite should have a toughness of -1'

        # + Cards
        assert Card.objects.get(name='Tarmogoyf').power == '*', "Tarmogoyf should have a power of *"
        assert Card.objects.get(name='Gaea\'s Avenger').power == '1+*', 'Gaea\'s Avenger should have a power of 1+*'
        assert Card.objects.get(name='Zombified').power == '+2', 'Zombified should have a power of +2'

        # Noncreature cards
        assert Card.objects.get(name='Ancestral Recall').power is None, 'Ancestral recall should have no power'
        assert Card.objects.get(name='Krosa').power is None, 'Krosa should have no power'
        assert Card.objects.get(name='Gratuitous Violence').power is None, 'Gratuitous Violence should have no power'
