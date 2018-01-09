from django.core.management.base import BaseCommand

import sys, traceback

from cards.models import *
from cards import colour
from cards.colour import Colour


class Command(BaseCommand):
    help = 'Verifies that database update was successful'

    class VerificationFailure:
        def __init__(self, message, stack_trace):
            self.message = message
            self.stack_trace = stack_trace

    def __init__(self):
        super().__init__()

        self.successful_tests = 0
        self.failed_tests = 0
        self.error_messages = list()

    def handle(self, *args, **options):
        methods = [method_name for method_name in dir(self)
                   if callable(getattr(self, method_name)) and method_name.startswith('test')]
        for method in methods:
            (getattr(self, method))()

        total_tests = self.successful_tests + self.failed_tests

        print(f'\n\n{total_tests} Tests Run ({self.successful_tests} Successful, {self.failed_tests} Failed)')
        for error in self.error_messages:
            # print(f'{error.message}\n{error.stack_trace}')
            print(error.message)

    def test_blocks(self):
        self.assert_true(Block.objects.filter(name='Ice Age').exists(), 'Ice Age block should exist')
        self.assert_true(Block.objects.filter(name='Ravnica').exists(), 'Ravnica block should exist')
        self.assert_true(Block.objects.filter(name='Ixalan').exists(), 'Ixalan block should exist')
        self.assert_false(Block.objects.filter(name='Weatherlight').exists(), 'Weatherlight block should not exist')

        self.assert_true(Block.objects.get(name='Ice Age').release_date < Block.objects.get(
            name='Onslaught').release_date, 'Ice Age should be released before Onslaught')

        self.assert_true(Block.objects.get(name='Mirrodin').sets.count() == 3, 'Mirrodin should have 3 sets')
        self.assert_true(Block.objects.get(name='Time Spiral').sets.count() == 4, 'Time Spiral should have 4 sets')
        self.assert_true(Block.objects.get(name='Amonkhet').sets.count() == 3,
                         'Amonkhet should have 3 sets (including Welcome Deck 2017)')

    def test_sets(self):
        self.assert_false(Set.objects.filter(name='Worlds').exists(), 'The Worlds set should have been filtered out')
        self.assert_false(Set.objects.filter(code__startswith='p').exists(),
                          'Sets that start with "p" should have been filtered out')

        self.assert_true(Set.objects.get(code='ONS').block.name == 'Onslaught',
                         'Onslaught should be in the Onslaught block')
        self.assert_true(Set.objects.get(code='WTH').block.name == 'Mirage',
                         'Weatherlight should be in the Mirage block')
        self.assert_true(Set.objects.get(code='CSP').block.name == 'Ice Age', 'Coldsnap should be in the Ice Age block')

    def test_rarities(self):
        self.assert_true(Rarity.objects.filter(symbol='R').exists(), 'The rare rarity should exist')

        self.assert_true(
            Rarity.objects.get(symbol='C').display_order < Rarity.objects.get(symbol='U').display_order,
            'Common rarity should be displayed before uncommon rarity')

    def test_card_name(self):
        # Normal card
        self.assert_card_exists('Animate Artifact')

        # Split card
        self.assert_card_exists('Wear')

        # UTF-8
        self.assert_card_exists('Jötun Grunt')
        self.assert_card_exists('Aether Charge')

        # Un-names
        self.assert_card_exists('_____')
        self.assert_card_exists('"Ach! Hans, Run!"')
        self.assert_card_exists('The Ultimate Nightmare of Wizards of the Coast® Customer Service')

        # Fip card
        self.assert_card_exists('Homura, Human Ascendant')

        # Negative tests
        self.assert_card_not_exists('Splendid Genesis')
        self.assert_card_not_exists('Æther Charge')

    def test_card_cost(self):
        # Expensive card
        self.assert_card_cost_eq('Progenitus', '{W}{W}{U}{U}{B}{B}{R}{R}{G}{G}')

        # Lands
        self.assert_card_cost_eq('Forest', None)
        self.assert_card_cost_eq('Dryad Arbor', None)

        # Monocoloured hybrid card
        self.assert_card_cost_eq('Flame Javelin', '{2/R}{2/R}{2/R}')

        # Plane
        self.assert_card_cost_eq('Krosa', None)

        # Multi-numeral symbol cards
        self.assert_card_cost_eq('Gleemax', '{1000000}')
        self.assert_card_cost_eq('Draco', '{16}')

        # Hybrid multicoloured card
        self.assert_card_cost_eq('Naya Hushblade', '{R/W}{G}')

        # Half mana card
        self.assert_card_cost_eq('Little Girl', '{hw}')

        # Meld card
        self.assert_card_cost_eq('Brisela, Voice of Nightmares', None)

        # Flip card
        self.assert_card_cost_eq('Bushi Tenderfoot', '{W}')
        self.assert_card_cost_eq('Kenzo the Hardhearted', '{W}')

        # Phyrexian mana card
        self.assert_card_cost_eq('Birthing Pod', '{3}{G/P}')

    def test_card_cmc(self):
        # Normal cards
        self.assert_card_cmc_eq('Tarmogoyf', 2)
        self.assert_card_cmc_eq('Black Lotus', 0)

        # Costless card
        self.assert_card_cmc_eq('Living End', 0)

        # Half mana card
        self.assert_card_cmc_eq('Little Girl', 0.5)

        # Monocoloured hybrid cards
        self.assert_card_cmc_eq('Reaper King', 10)
        self.assert_card_cmc_eq('Flame Javelin', 6)

        # High cost cards
        self.assert_card_cmc_eq('Blinkmoth Infusion', 14)
        self.assert_card_cmc_eq('Gleemax', 1000000)

        # Phyrexian mana card
        self.assert_card_cmc_eq('Birthing Pod', 4)

        # Land
        self.assert_card_cmc_eq('Dryad Arbor', 0)

        # Colourless mana card
        self.assert_card_cmc_eq('Kozilek, the Great Distortion', 10)

        # Plane
        self.assert_card_cmc_eq('Krosa', 0)

        # X cost card
        self.assert_card_cmc_eq('Comet Storm', 2)

        # Transform card
        self.assert_card_cmc_eq('Garruk Relentless', 4)
        self.assert_card_cmc_eq('Garruk, the Veil-Cursed', 4)

        # Meld card
        self.assert_card_cmc_eq('Brisela, Voice of Nightmares', 11)

        # Split card
        self.assert_card_cmc_eq('Wear', 2)

        # Flip card
        self.assert_card_cmc_eq('Homura\'s Essence', 6)

    def test_card_color(self):
        # Monocoloured card
        self.assert_card_colour_eq('Glory Seeker', Colour.white)

        # Multicoloured card
        self.assert_card_colour_eq('Dark Heart of the Wood', Colour.black | Colour.green)
        self.assert_card_colour_eq('Progenitus', Colour.all)
        self.assert_card_colour_eq('Reaper King', Colour.all)

        # Hybrid card
        self.assert_card_colour_eq('Azorius Guildmage', Colour.white | Colour.blue)

        # Colour indicator cards
        self.assert_card_colour_eq('Transguild Courier', Colour.all)
        self.assert_card_colour_eq('Ghostfire', Colour.none)
        self.assert_card_colour_eq('Dryad Arbor', Colour.green)

        # Same colour transform card
        self.assert_card_colour_eq('Delver of Secrets', Colour.blue)
        self.assert_card_colour_eq('Insectile Aberration', Colour.blue)

        # Different colour transform card
        self.assert_card_colour_eq('Garruk Relentless', Colour.green)
        self.assert_card_colour_eq('Garruk, the Veil-Cursed', Colour.black | Colour.green)

        # Colour identity cards
        self.assert_card_colour_eq('Bosh, Iron Golem', Colour.none)

        # Split card
        self.assert_card_colour_eq('Tear', Colour.white)

        # Flip card
        self.assert_card_colour_eq('Rune-Tail, Kitsune Ascendant', Colour.white)
        self.assert_card_colour_eq('Rune-Tail\'s Essence', Colour.white)

    def test_card_colour_identity(self):
        # Normal cards
        self.assert_card_colour_identity_eq('Goblin Piker', Colour.red)

        # Lands
        self.assert_card_colour_identity_eq('Mountain', Colour.red)
        self.assert_card_colour_identity_eq('Polluted Delta', Colour.none)
        self.assert_card_colour_identity_eq('Tolarian Academy', Colour.blue)

        # Colour indicator cards
        self.assert_card_colour_identity_eq('Ghostfire', Colour.red)
        self.assert_card_colour_identity_eq('Dryad Arbor', Colour.green)

        # Augment cards
        self.assert_card_colour_identity_eq('Half-Orc, Half-', Colour.red)

        # Symbol in rules cards
        self.assert_card_colour_identity_eq('Bosh, Iron Golem', Colour.red)
        self.assert_card_colour_identity_eq('Dawnray Archer', Colour.white | Colour.blue)
        self.assert_card_colour_identity_eq('Obelisk of Alara', Colour.all)

        # Hybrid cards
        self.assert_card_colour_identity_eq('Azorius Guildmage', Colour.white | Colour.blue)

        # Split cards
        self.assert_card_colour_identity_eq('Wear', Colour.white | Colour.red)
        self.assert_card_colour_identity_eq('Tear', Colour.white | Colour.red)

        # Flip cards
        self.assert_card_colour_identity_eq('Garruk Relentless', Colour.black | Colour.green)
        self.assert_card_colour_identity_eq('Garruk, the Veil-Cursed', Colour.black | Colour.green)
        self.assert_card_colour_identity_eq('Gisela, the Broken Blade', Colour.white)
        self.assert_card_colour_identity_eq('Brisela, Voice of Nightmares', Colour.white)

    def test_card_colour_count(self):
        # Normal cards
        self.assert_card_colour_count_eq('Birds of Paradise', 1)
        self.assert_card_colour_count_eq('Edgewalker', 2)
        self.assert_card_colour_count_eq('Naya Hushblade', 3)
        self.assert_card_colour_count_eq('Swamp', 0)
        self.assert_card_colour_count_eq('Ornithopter', 0)
        self.assert_card_colour_count_eq('Glint-Eye Nephilim', 4)
        self.assert_card_colour_count_eq('Cromat', 5)

        # Colour indicator cards
        self.assert_card_colour_count_eq('Evermind', 1)
        self.assert_card_colour_count_eq('Arlinn, Embraced by the Moon', 2)

        # Non-playable cards
        self.assert_card_colour_count_eq('Dance, Pathetic Marionette', 0)

    def test_card_type(self):
        self.assert_card_type_eq('Kird Ape', 'Creature')
        self.assert_card_type_eq('Forest', 'Basic Land')
        self.assert_card_type_eq('Masticore', 'Artifact Creature')
        self.assert_card_type_eq('Tarmogoyf', 'Creature')
        self.assert_card_type_eq('Lignify', 'Tribal Enchantment')
        self.assert_card_type_eq('Sen Triplets', 'Legendary Artifact Creature')
        self.assert_card_type_eq('Walking Atlas', 'Artifact Creature')
        self.assert_card_type_eq('Soul Net', 'Artifact')
        self.assert_card_type_eq('Ajani Goldmane', 'Legendary Planeswalker')
        self.assert_card_type_eq('Bant', 'Plane')
        self.assert_card_type_eq('My Crushing Masterstroke', 'Scheme')
        self.assert_card_type_eq('Nameless Race', 'Creature')

    def test_card_subype(self):
        # Single subtype
        self.assert_card_subtype_eq('Screaming Seahawk', 'Bird')
        self.assert_card_subtype_eq('Mistform Ultimus', 'Illusion')
        self.assert_card_subtype_eq('Forest', 'Forest')
        # Multiple subtypes
        self.assert_card_subtype_eq('Glory Seeker', 'Human Soldier')
        # Planeswalker
        self.assert_card_subtype_eq('Jace, the Mind Sculptor', 'Jace')
        # Tribal
        self.assert_card_subtype_eq('Lignify', 'Treefolk Aura')
        # None
        self.assert_card_subtype_eq('Nameless Race', None)
        self.assert_card_subtype_eq('Spellbook', None)

    def test_card_power(self):
        # Normal Cards
        self.assert_card_power_eq('Birds of Paradise', '0')
        self.assert_card_power_eq('Dryad Arbor', '1')
        self.assert_card_power_eq('Juggernaut', '5')

        # Vehicles
        self.assert_card_power_eq('Irontread Crusher', '6')

        # Negative Cards
        self.assert_card_power_eq('Char-Rumbler', '-1')
        self.assert_card_power_eq('Spinal Parasite', '-1')

        # + Cards
        self.assert_card_power_eq('Tarmogoyf', '*')
        self.assert_card_power_eq('Gaea\'s Avenger', '1+*')
        self.assert_card_power_eq('Zombified', '+2')
        self.assert_card_power_eq('S.N.O.T.', '*²')

        # Noncreature cards
        self.assert_card_power_eq('Ancestral Recall', None)
        self.assert_card_power_eq('Krosa', None)
        self.assert_card_power_eq('Gratuitous Violence', None)

    def test_card_num_power(self):
        # Normal creatures
        self.assert_card_num_power_eq('Stone Golem', 4)
        self.assert_card_num_power_eq('Progenitus', 10)
        self.assert_card_num_power_eq('Emrakul, the Aeons Torn', 15)

        # Negative power creatures
        self.assert_card_num_power_eq('Spinal Parasite', -1)

        # Non-creatures
        self.assert_card_num_power_eq('Ancestral Recall', 0)

        # + Cards
        self.assert_card_num_power_eq('Tarmogoyf', 0)
        self.assert_card_num_power_eq('Haunting Apparition', 1)

    def test_card_toughness(self):
        # Normal Cards
        self.assert_card_toughness_eq('Obsianus Golem', '6')
        self.assert_card_toughness_eq('Dryad Arbor', '1')
        self.assert_card_toughness_eq('Force of Savagery', '0')

        # Vehicles
        self.assert_card_toughness_eq('Heart of Kiran', '4')

        # Negative Cards
        self.assert_card_toughness_eq('Spinal Parasite', '-1')

        # + Cards
        self.assert_card_toughness_eq('Tarmogoyf', '1+*')
        self.assert_card_toughness_eq('Gaea\'s Avenger', '1+*')
        self.assert_card_toughness_eq('Half-Orc, Half-', '+1')
        self.assert_card_toughness_eq('S.N.O.T.', '*²')

        # Noncreature cards
        self.assert_card_toughness_eq('Gratuitous Violence', None)
        self.assert_card_toughness_eq('Ancestral Recall', None)
        self.assert_card_toughness_eq('Krosa', None)

    def test_card_num_toughness(self):
        # Normal Cards
        self.assert_card_num_toughness_eq('Wall of Fire', 5)
        self.assert_card_num_toughness_eq('Daru Lancer', 4)
        self.assert_card_num_toughness_eq('Tree of Redemption', 13)

        # Vehicles
        self.assert_card_num_toughness_eq('Skysovereign, Consul Flagship', 5)

        # Negative cards
        self.assert_card_num_toughness_eq('Spinal Parasite', -1)

        # + Cards
        self.assert_card_num_toughness_eq('Tarmogoyf', 1)
        self.assert_card_num_toughness_eq('Angry Mob', 2)
        self.assert_card_num_toughness_eq('S.N.O.T.', 0)

    def test_loyalty(self):
        # Planeswalkers
        self.assert_card_loyalty_eq('Ajani Goldmane', '4')

        # Flipwalkers
        self.assert_card_loyalty_eq('Chandra, Fire of Kaladesh', None)
        self.assert_card_loyalty_eq('Chandra, Roaring Flame', '4')

        # Non-planeswalkers
        self.assert_card_loyalty_eq('Glimmervoid Basin', None)
        self.assert_card_loyalty_eq('Megatog', None)
        self.assert_card_loyalty_eq('Urza', None)

    def test_card_num_loyalty(self):
        # Planeswalkers
        self.assert_card_num_loyalty_eq('Ajani Goldmane', 4)

        # Flipwalkers
        self.assert_card_num_loyalty_eq('Chandra, Fire of Kaladesh', 0)
        self.assert_card_num_loyalty_eq('Chandra, Roaring Flame', 4)

        # Non-planeswalkers
        self.assert_card_num_loyalty_eq('Glimmervoid Basin', 0)
        self.assert_card_num_loyalty_eq('Megatog', 0)
        self.assert_card_num_loyalty_eq('Urza', 0)

    def test_card_hand_modifier(self):
        # Vanguard
        self.assert_card_hand_mod_eq('Urza', -1)
        self.assert_card_hand_mod_eq('Volrath', 2)
        self.assert_card_hand_mod_eq('Birds of Paradise Avatar', 0)

        # Other
        self.assert_card_hand_mod_eq('Chandra Nalaar', None)
        self.assert_card_hand_mod_eq('Elite Vanguard', None)
        self.assert_card_hand_mod_eq('Incinerate', None)

    def test_card_life_modifier(self):
        # Vanguard
        self.assert_card_life_mod_eq('Urza', 10)
        self.assert_card_life_mod_eq('Volrath', -3)
        self.assert_card_life_mod_eq('Birds of Paradise Avatar', -3)

        # Other
        self.assert_card_life_mod_eq('Chandra Nalaar', None)
        self.assert_card_life_mod_eq('Elite Vanguard', None)
        self.assert_card_life_mod_eq('Incinerate', None)

    def test_card_rules_text(self):
        self.assert_card_rules_eq('Grizzly Bears', None)
        self.assert_card_rules_eq('Elite Vanguard', None)
        self.assert_card_rules_eq('Forest', None)
        self.assert_card_rules_eq('Snow-Covered Swamp', None)

        self.assert_card_rules_eq('Air Elemental', 'Flying')
        self.assert_card_rules_eq('Thunder Spirit', 'Flying, first strike')
        self.assert_card_rules_eq('Dark Ritual', 'Add {B}{B}{B} to your mana pool.')
        self.assert_card_rules_eq('Palladium Myr', '{T}: Add {C}{C} to your mana pool.')
        self.assert_card_rules_eq('Ice Cauldron',
                                  "{X}, {T}: Put a charge counter on Ice Cauldron and exile a nonland card from your " +
                                  "hand. You may cast that card for as long as it remains exiled. Note the type and " +
                                  "amount of mana spent to pay this activation cost. Activate this ability only if " +
                                  "there are no charge counters on Ice Cauldron.\n{T}, Remove a charge counter from " +
                                  "Ice Cauldron: Add Ice Cauldron's last noted type and amount of mana to your mana " +
                                  "pool. Spend this mana only to cast the last card exiled with Ice Cauldron.")

    def assert_card_exists(self, card_name: str):
        self.assert_true(Card.objects.filter(name=card_name).exists(), f'{card_name} should exist')

    def assert_card_not_exists(self, card_name: str):
        self.assert_false(Card.objects.filter(name=card_name).exists(), f'{card_name} should not exist')

    def assert_card_cost_eq(self, card_name: str, cost: str):
        self.assert_card_name_attr_eq(card_name, 'cost', cost)

    def assert_card_cmc_eq(self, card_name: str, cmc: int):
        self.assert_card_name_attr_eq(card_name, 'cmc', cmc)

    def assert_card_colour_eq(self, card_name: str, colour: int):
        self.assert_card_name_attr_eq(card_name, 'colour', colour)

    def assert_card_colour_identity_eq(self, card_name: str, colour_identity: int):
        self.assert_card_name_attr_eq(card_name, 'colour_identity', colour_identity)

    def assert_card_colour_count_eq(self, card_name: str, colour_count):
        self.assert_card_name_attr_eq(card_name, 'colour_count', colour_count)

    def assert_card_type_eq(self, card_name: str, type):
        self.assert_card_name_attr_eq(card_name, 'type', type)

    def assert_card_subtype_eq(self, card_name: str, subtype):
        self.assert_card_name_attr_eq(card_name, 'subtype', subtype)

    def assert_card_power_eq(self, card_name: str, power):
        self.assert_card_name_attr_eq(card_name, 'power', power)

    def assert_card_num_power_eq(self, card_name: str, num_power):
        self.assert_card_name_attr_eq(card_name, 'num_power', num_power)

    def assert_card_toughness_eq(self, card_name: str, toughness):
        self.assert_card_name_attr_eq(card_name, 'toughness', toughness)

    def assert_card_num_toughness_eq(self, card_name: str, num_toughness):
        self.assert_card_name_attr_eq(card_name, 'num_toughness', num_toughness)

    def assert_card_loyalty_eq(self, card_name: str, loyalty: str):
        self.assert_card_name_attr_eq(card_name, 'loyalty', loyalty)

    def assert_card_num_loyalty_eq(self, card_name: str, num_loyalty: int):
        self.assert_card_name_attr_eq(card_name, 'num_loyalty', num_loyalty)

    def assert_card_hand_mod_eq(self, card_name: str, hand_mod: int):
        self.assert_card_name_attr_eq(card_name, 'hand_modifier', hand_mod)

    def assert_card_life_mod_eq(self, card_name: str, life_mod: int):
        self.assert_card_name_attr_eq(card_name, 'life_modifier', life_mod)

    def assert_card_rules_eq(self, card_name: str, rules_text: str):
        self.assert_card_name_attr_eq(card_name, 'rules_text', rules_text)

    def assert_card_name_attr_eq(self, card_name: str, attr_name: str, attr_value):
        if not Card.objects.filter(name=card_name).exists():
            self.assert_true(False, f'Card "{card_name}" could not be found')
            return

        card = Card.objects.get(name=card_name)
        self.assert_card_attr_eq(card, attr_name, attr_value)

    def assert_card_attr_eq(self, card: Card, attr_name: str, expected):
        actual = getattr(card, attr_name)
        self.assert_true(expected == actual, f'{card}.{attr_name} was expected to be "{expected}", actually "{actual}"')

    def assert_false(self, result: bool, message: str):
        self.assert_true(not result, message)

    def assert_true(self, result: bool, message: str):

        if result:
            self.successful_tests += 1
            print('.', end='')
        else:
            self.failed_tests += 1
            print('F', end='')
            error = self.VerificationFailure(message, ''.join(traceback.format_stack()))
            self.error_messages.append(error)

        sys.stdout.flush()
