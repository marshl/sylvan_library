import re
from functools import total_ordering

from cards import colour


@total_ordering
class StagedCard:
    def __init__(self, value_dict):
        self.value_dict = value_dict

        self.collector_number = None
        self.collector_letter = None
        self._parse_number()

    def _parse_number(self):
        if 'number' not in self.value_dict:
            return

        match = re.search(
            '^(?P<special>[\D]+)?(?P<number>[\d]+)(?P<letter>[\D]+)?$',
            self.value_dict['number'])

        self.collector_number = int(match.group('number'))
        self.collector_letter = (
            match.group('special') or
            match.group('letter'))

    def __eq__(self, other: 'StagedCard'):
        return self.collector_number == other.collector_number and \
               self.collector_letter == other.collector_letter and \
               self.get_multiverse_id() == other.get_multiverse_id() and \
               self.get_mci_number() == other.get_mci_number() and \
               self.get_name() == other.get_name()

    def __lt__(self, other: 'StagedCard'):

        # Push cards without a collector number to the end of the set
        if self.get_collector_number() is not None and other.get_collector_number() is None:
            return True

        if self.get_collector_number() is None and other.get_collector_number() is not None:
            return False

        if self.get_collector_number() is not None and other.get_collector_number() is not None:

            # Push '★" cards to the end of the set
            if self.get_collector_letter() == '★':
                return False

            if other.get_collector_letter() == '★':
                return True

            if self.get_collector_number() != other.get_collector_number():
                return self.get_collector_number() < other.get_collector_number()

            if self.get_collector_letter() is not None and other.get_collector_letter() is None:
                return True

            if self.get_collector_letter() is None and other.get_collector_letter() is not None:
                return False

            if self.get_collector_letter() is not None and other.get_collector_letter() is not None:
                return self.get_collector_letter() < other.get_collector_letter()

        return self.get_name() < other.get_name()

    def get_multiverse_id(self):
        return self.value_dict.get('multiverseid')

    def has_foreign_names(self):
        return 'foreignNames' in self.value_dict

    def get_foreign_names(self):
        return self.value_dict['foreignNames']

    def get_name(self):
        if self.value_dict['name'] == 'B.F.M. (Big Furry Monster)':
            if self.value_dict['imageName'] == "b.f.m. 1":
                return 'B.F.M. (Big Furry Monster) (left)'
            elif self.value_dict['imageName'] == "b.f.m. 2":
                return 'B.F.M. (Big Furry Monster) (right)'

        return self.value_dict['name']

    def get_mana_cost(self):
        return self.value_dict.get('manaCost')

    def get_cmc(self):
        return self.value_dict.get('cmc') or 0

    def get_colour(self):
        if 'colors' in self.value_dict:
            return colour.colour_names_to_flags(self.value_dict['colors'])
        else:
            return 0

    def get_colour_identity(self):
        if 'colorIdentity' in self.value_dict:
            return colour.colour_codes_to_flags(self.value_dict['colorIdentity'])
        else:
            return 0

    def get_colour_count(self):
        return bin(self.get_colour()).count('1')

    def get_power(self):
        return self.value_dict.get('power')

    def get_toughness(self):
        return self.value_dict.get('toughness')

    def get_num_power(self):
        if 'power' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['power'])
        else:
            return 0

    def get_num_toughness(self):
        if 'toughness' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['toughness'])
        else:
            return 0

    def get_loyalty(self):
        return self.value_dict.get('loyalty')

    def get_num_loyalty(self):
        if 'loyalty' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['loyalty'])
        else:
            return 0

    def get_types(self):
        if 'types' in self.value_dict:
            types = (self.value_dict.get('supertypes') or []) + \
                    (self.value_dict['types'])
            return ' '.join(types)
        else:
            return None

    def get_subtypes(self):
        if 'subtypes' in self.value_dict:
            return ' '.join(self.value_dict.get('subtypes'))
        else:
            return None

    def get_rules_text(self):
        return self.value_dict.get('text')

    def get_collector_number(self):
        return self.collector_number

    def get_collector_letter(self):
        return self.collector_letter

    def get_artist(self):
        return self.value_dict['artist']

    def get_rarity_name(self):
        if 'timeshifted' in self.value_dict and self.value_dict['timeshifted']:
            return 'Timeshifted'

        return self.value_dict['rarity']

    def get_flavour_text(self):
        return self.value_dict.get('flavor')

    def get_original_text(self):
        return self.value_dict.get('originalText')

    def get_original_type(self):
        return self.value_dict.get('originalType')

    def has_rulings(self):
        return 'rulings' in self.value_dict

    def get_rulings(self):
        return self.value_dict['rulings']

    def get_json_id(self):
        return self.value_dict['id']

    def get_mci_number(self):
        if 'mciNumber' not in self.value_dict:
            return None

        mci_match = re.search(
            '^(/(?P<set>[^/]*)/(?P<lang>[^/]*)/)?(?P<num>[0-9]+)(\.html)?$',
            self.value_dict['mciNumber'])

        if mci_match:
            return mci_match.group('num')

    def get_layout(self):
        return self.value_dict['layout']

    def get_legalities(self):
        return self.value_dict['legalities'] if 'legalities' in self.value_dict else []

    def get_name_count(self):
        return len(self.value_dict['names'])

    def has_other_names(self):
        return 'names' in self.value_dict

    def get_other_names(self):

        # B.F.M. has the same name for both cards, so the link_name has to be manually set
        if self.get_name() == 'B.F.M. (Big Furry Monster) (left)':
            return ['B.F.M. (Big Furry Monster) (right)']
        elif self.get_name() == 'B.F.M. (Big Furry Monster) (right)':
            return ['B.F.M. (Big Furry Monster) (left)']

        return [n for n in self.value_dict['names'] if n != self.get_name()]

    def set_collector_number(self, cnum):
        if self.collector_number is not None:
            raise Exception('Cannot set the collector number if it has already been set')

        self.collector_number = cnum

    def sanitise_name(self, name):
        if name == 'B.F.M. (Big Furry Monster)':
            if self.value_dict['imageName'] == "b.f.m. 1":
                return 'B.F.M. (Big Furry Monster) (left)'
            elif self.value_dict['imageName'] == "b.f.m. 2":
                return 'B.F.M. (Big Furry Monster) (right)'

        return self.value_dict['name']

    def pow_tuff_to_num(self, val):
        match = re.search('(-?[\d.]+)', str(val))
        if match:
            return match.group()

        return 0


class StagedSet:
    def __init__(self, value_dict):
        self.value_dict = value_dict
        self.staged_cards = list()

        for card in self.value_dict['cards']:
            self.add_card(card)

    def add_card(self, card):
        staged_card = StagedCard(card)
        self.staged_cards.append(staged_card)

    def get_cards(self):
        return sorted(self.staged_cards)

    def get_code(self):
        return self.value_dict['code']

    def get_release_date(self):
        return self.value_dict['releaseDate']

    def get_name(self):
        return self.value_dict['name']

    def get_block(self):
        return self.value_dict.get('block')

    def has_block(self):
        return 'block' in self.value_dict

    def get_mci_code(self):
        return self.value_dict.get('magicCardsInfoCode')

    def get_border_colour(self):
        return self.value_dict.get('border')
