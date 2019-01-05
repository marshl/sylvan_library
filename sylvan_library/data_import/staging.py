import datetime, re
from functools import total_ordering

from cards.models import Colour, Card

COLOUR_NAME_TO_FLAG = {
    'white': Card.colour_flags.white,
    'blue': Card.colour_flags.blue,
    'black': Card.colour_flags.black,
    'red': Card.colour_flags.red,
    'green': Card.colour_flags.green,
}

COLOUR_CODE_TO_FLAG = {
    'w': Card.colour_flags.white,
    'u': Card.colour_flags.blue,
    'b': Card.colour_flags.black,
    'r': Card.colour_flags.red,
    'g': Card.colour_flags.green,
}

COLOUR_TO_SORT_KEY = {
    0: 0,
    int(Card.colour_flags.white): 1,
    int(Card.colour_flags.blue): 2,
    int(Card.colour_flags.black): 3,
    int(Card.colour_flags.red): 4,
    int(Card.colour_flags.green): 5,

    int(Card.colour_flags.white | Card.colour_flags.blue): 6,
    int(Card.colour_flags.blue | Card.colour_flags.black): 7,
    int(Card.colour_flags.black | Card.colour_flags.red): 8,
    int(Card.colour_flags.red | Card.colour_flags.green): 9,
    int(Card.colour_flags.green | Card.colour_flags.white): 10,

    int(Card.colour_flags.white | Card.colour_flags.black): 11,
    int(Card.colour_flags.blue | Card.colour_flags.red): 12,
    int(Card.colour_flags.black | Card.colour_flags.green): 13,
    int(Card.colour_flags.red | Card.colour_flags.white): 14,
    int(Card.colour_flags.green | Card.colour_flags.blue): 15,

    int(Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black): 16,
    int(Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red): 17,
    int(Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green): 18,
    int(Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white): 19,
    int(Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue): 20,

    int(Card.colour_flags.white | Card.colour_flags.black | Card.colour_flags.green): 21,
    int(Card.colour_flags.blue | Card.colour_flags.red | Card.colour_flags.white): 22,
    int(Card.colour_flags.black | Card.colour_flags.green | Card.colour_flags.blue): 23,
    int(Card.colour_flags.red | Card.colour_flags.white | Card.colour_flags.black): 24,
    int(Card.colour_flags.green | Card.colour_flags.blue | Card.colour_flags.red): 25,

    int(Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red): 26,
    int(Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green): 27,
    int(Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white): 28,
    int(Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue): 29,
    int(Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black): 30,

    int(Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black
        | Card.colour_flags.red | Card.colour_flags.green): 31,
}


@total_ordering
class StagedCard:
    def __init__(self, value_dict):
        self.value_dict = value_dict
        self.number = value_dict.get('number')

    def __eq__(self, other: 'StagedCard'):
        return self.number == other.number and \
               self.get_multiverse_id() == other.get_multiverse_id() and \
               self.get_name() == other.get_name()

    def __lt__(self, other: 'StagedCard'):

        # Push cards without a collector number to the end of the set
        if self.get_number() is not None and other.get_number() is None:
            return True

        if self.get_number() is None and other.get_number() is not None:
            return False

        if self.get_number() is not None and other.get_number() is not None:
            if self.get_number() != other.get_number():
                return self.get_number() < other.get_number()

        return self.get_name() < other.get_name()

    def get_number(self):
        return self.number

    def get_multiverse_id(self):
        return self.value_dict.get('multiverseId')

    def has_foreign_names(self):
        return 'foreignNames' in self.value_dict

    def get_foreign_names(self):
        return self.value_dict['foreignNames']

    def get_name(self):
        if self.value_dict['name'] == 'B.F.M. (Big Furry Monster)':
            if self.value_dict['number'] == '28':
                return 'B.F.M. (Big Furry Monster) (left)'
            elif self.value_dict['number'] == '29':
                return 'B.F.M. (Big Furry Monster) (right)'

        return self.value_dict['name']

    def get_mana_cost(self):
        return self.value_dict.get('manaCost')

    def get_cmc(self):
        return self.value_dict.get('convertedManaCost') or 0

    def get_colour(self):
        result = 0
        if 'colors' in self.value_dict:
            for colour_name in self.value_dict['colors']:
                result |= COLOUR_CODE_TO_FLAG[colour_name.lower()]

        return result

    def get_colour_sort_key(self):
        return COLOUR_TO_SORT_KEY[int(self.get_colour())]

    def get_colour_weight(self):
        if not self.get_mana_cost():
            return 0

        generic_mana = re.search('(\d+)', self.get_mana_cost())
        if not generic_mana:
            return self.get_cmc()
        else:
            return self.get_cmc() - int(generic_mana.group(0))

    def get_colour_identity(self):
        result = 0
        if 'colorIdentity' in self.value_dict:
            for colour_code in self.value_dict['colorIdentity']:
                result |= COLOUR_CODE_TO_FLAG[colour_code.lower()]

        return result

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

    def get_original_text(self):
        return self.value_dict.get('originalText')

    def get_artist(self):
        return self.value_dict['artist']

    def get_rarity_name(self):
        if 'timeshifted' in self.value_dict and self.value_dict['timeshifted']:
            return 'Timeshifted'

        return self.value_dict['rarity']

    def get_flavour_text(self):
        return self.value_dict.get('flavorText')

    def get_original_type(self):
        return self.value_dict.get('originalType')

    def has_rulings(self):
        return 'rulings' in self.value_dict

    def get_rulings(self):
        return self.value_dict['rulings']

    def get_json_id(self):
        return self.value_dict['uuid']

    def get_layout(self):
        return self.value_dict['layout']

    def get_legalities(self):
        return self.value_dict['legalities'] if 'legalities' in self.value_dict else []

    def get_name_count(self):
        return len(self.value_dict['names'])

    def get_watermark(self):
        return self.value_dict.get('watermark')

    def get_border_colour(self):
        return self.value_dict.get('borderColor')

    def get_release_date(self):
        if 'releaseDate' in self.value_dict:
            date_string = self.value_dict['releaseDate']
            try:
                return datetime.datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.datetime.strptime(date_string, '%Y-%m')
                except ValueError:
                    return datetime.datetime.strptime()

        return None

    def is_reserved(self):
        return 'reserved' in self.value_dict and self.value_dict['reserved']

    def is_starter_printing(self):
        return 'starter' in self.value_dict and self.value_dict['starter']

    def has_other_names(self):
        return 'names' in self.value_dict

    def get_other_names(self):

        # B.F.M. has the same name for both cards, so the link_name has to be manually set
        if self.get_name() == 'B.F.M. (Big Furry Monster) (left)':
            return ['B.F.M. (Big Furry Monster) (right)']
        elif self.get_name() == 'B.F.M. (Big Furry Monster) (right)':
            return ['B.F.M. (Big Furry Monster) (left)']

        return [n for n in self.value_dict['names'] if n != self.get_name()]

    def set_number(self, cnum):
        if self.number is not None:
            raise Exception('Cannot set the collector number if it has already been set')

        self.number = cnum

    def sanitise_name(self, name):
        if name == 'B.F.M. (Big Furry Monster)':
            if self.value_dict['number'] == '28':
                return 'B.F.M. (Big Furry Monster) (left)'
            elif self.value_dict['number'] == '29':
                return 'B.F.M. (Big Furry Monster) (right)'

        return self.value_dict['name']

    def pow_tuff_to_num(self, val):
        match = re.search('(-?[\d.]+)', str(val))
        if match:
            return match.group()

        return 0


class StagedSet:
    def __init__(self, code, value_dict):
        self.code = code
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
        return self.code

    def get_release_date(self):
        return self.value_dict['releaseDate']

    def get_name(self):
        return self.value_dict['name']

    def get_block(self):
        return self.value_dict.get('block')

    def has_block(self):
        return 'block' in self.value_dict
