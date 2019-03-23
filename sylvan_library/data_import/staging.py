"""
Module for staging classes
"""
import datetime
import math
import re
from typing import Dict, List, Optional
from functools import total_ordering

from cards.models import Colour

COLOUR_TO_SORT_KEY = {
    0: 0,
    int(Colour.white().bit_value): 1,
    int(Colour.blue().bit_value): 2,
    int(Colour.black().bit_value): 3,
    int(Colour.red().bit_value): 4,
    int(Colour.green().bit_value): 5,

    int(Colour.white().bit_value | Colour.blue().bit_value): 6,
    int(Colour.blue().bit_value | Colour.black().bit_value): 7,
    int(Colour.black().bit_value | Colour.red().bit_value): 8,
    int(Colour.red().bit_value | Colour.green().bit_value): 9,
    int(Colour.green().bit_value | Colour.white().bit_value): 10,

    int(Colour.white().bit_value | Colour.black().bit_value): 11,
    int(Colour.blue().bit_value | Colour.red().bit_value): 12,
    int(Colour.black().bit_value | Colour.green().bit_value): 13,
    int(Colour.red().bit_value | Colour.white().bit_value): 14,
    int(Colour.green().bit_value | Colour.blue().bit_value): 15,

    int(Colour.white().bit_value | Colour.blue().bit_value | Colour.black().bit_value): 16,
    int(Colour.blue().bit_value | Colour.black().bit_value | Colour.red().bit_value): 17,
    int(Colour.black().bit_value | Colour.red().bit_value | Colour.green().bit_value): 18,
    int(Colour.red().bit_value | Colour.green().bit_value | Colour.white().bit_value): 19,
    int(Colour.green().bit_value | Colour.white().bit_value | Colour.blue().bit_value): 20,

    int(Colour.white().bit_value | Colour.black().bit_value | Colour.green().bit_value): 21,
    int(Colour.blue().bit_value | Colour.red().bit_value | Colour.white().bit_value): 22,
    int(Colour.black().bit_value | Colour.green().bit_value | Colour.blue().bit_value): 23,
    int(Colour.red().bit_value | Colour.white().bit_value | Colour.black().bit_value): 24,
    int(Colour.green().bit_value | Colour.blue().bit_value | Colour.red().bit_value): 25,

    int(Colour.white().bit_value | Colour.blue().bit_value
        | Colour.black().bit_value | Colour.red().bit_value): 26,
    int(Colour.blue().bit_value | Colour.black().bit_value
        | Colour.red().bit_value | Colour.green().bit_value): 27,
    int(Colour.black().bit_value | Colour.red().bit_value
        | Colour.green().bit_value | Colour.white().bit_value): 28,
    int(Colour.red().bit_value | Colour.green().bit_value
        | Colour.white().bit_value | Colour.blue().bit_value): 29,
    int(Colour.green().bit_value | Colour.white().bit_value
        | Colour.blue().bit_value | Colour.black().bit_value): 30,

    int(Colour.white().bit_value | Colour.blue().bit_value | Colour.black().bit_value
        | Colour.red().bit_value | Colour.green().bit_value): 31,
}


# pylint: disable=too-many-public-methods
@total_ordering
class StagedCard:
    """
    Class for staging a card record from json
    """

    def __init__(self, value_dict: dict):
        self.value_dict = value_dict
        self.number = value_dict.get('number')

    def __eq__(self, other: 'StagedCard') -> bool:
        return self.number == other.number and \
               self.get_multiverse_id() == other.get_multiverse_id() and \
               self.get_name() == other.get_name()

    def __lt__(self, other: 'StagedCard') -> bool:

        # Push cards without a collector number to the end of the set
        if self.get_number() is not None and other.get_number() is None:
            return True

        if self.get_number() is None and other.get_number() is not None:
            return False

        if self.get_number() is not None and other.get_number() is not None:
            if self.get_number() != other.get_number():
                return self.get_number() < other.get_number()

        return self.get_name() < other.get_name()

    def get_number(self) -> str:
        return self.number

    def get_multiverse_id(self) -> str:
        return self.value_dict.get('multiverseId')

    def has_foreign_data(self) -> bool:
        return bool(self.value_dict.get('foreignData'))

    def get_foreign_data(self) -> dict:
        return self.value_dict['foreignData']

    def get_name(self) -> str:
        return self.value_dict['name']

    def get_mana_cost(self) -> str:
        return self.value_dict.get('manaCost')

    def get_cmc(self) -> float:
        return self.value_dict.get('convertedManaCost') or 0

    def get_colour(self) -> int:
        if 'colors' in self.value_dict:
            return Colour.colour_codes_to_flags(self.value_dict['colors'])

        return 0

    def get_colour_sort_key(self) -> int:
        return COLOUR_TO_SORT_KEY[int(self.get_colour())]

    def get_colour_weight(self) -> int:
        if not self.get_mana_cost():
            return 0

        generic_mana = re.search(r'(\d+)', self.get_mana_cost())
        if not generic_mana:
            return int(self.get_cmc())

        return int(self.get_cmc()) - int(generic_mana.group(0))

    def get_colour_identity(self) -> int:
        if 'colorIdentity' in self.value_dict:
            return Colour.colour_codes_to_flags(self.value_dict['colorIdentity'])

        return 0

    def get_colour_count(self) -> int:
        """
        Gets the number of colours of the card
        :return:
        """
        return bin(self.get_colour()).count('1')

    def get_power(self) -> str:
        """
        Gets the string representation of the power of the card
        :return:
        """
        return self.value_dict.get('power')

    def get_toughness(self) -> str:
        """
        Gets the string represeentation of the toughness of the card
        :return:
        """
        return self.value_dict.get('toughness')

    def get_num_power(self) -> float:
        """
        Gets the numerical representation of the power of the card
        :return:
        """
        if 'power' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['power'])

        return 0

    def get_num_toughness(self) -> float:
        """
        Gets the numerical representation of the toughness of the card
        :return:
        """
        if 'toughness' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['toughness'])

        return 0

    def get_loyalty(self) -> str:
        """
        Gets the string representation of the loyalty of the card
        :return:
        """
        return self.value_dict.get('loyalty')

    def get_num_loyalty(self) -> float:
        if 'loyalty' in self.value_dict:
            return self.pow_tuff_to_num(self.value_dict['loyalty'])

        return 0

    def get_types(self) -> Optional[str]:
        """
        Gets the types of the card
        :return: The card's types
        """
        if 'types' in self.value_dict:
            types = (self.value_dict.get('supertypes') or []) + \
                    (self.value_dict['types'])
            return ' '.join(types)

        return None

    def get_subtypes(self) -> Optional[str]:
        """
        Gets the subtypes of the card
        :return: The card's subtypes
        """
        if 'subtypes' in self.value_dict:
            return ' '.join(self.value_dict.get('subtypes'))

        return None

    def get_rules_text(self) -> str:
        """
        Gets the rules text of the card
        :return: The card's rules text
        """
        return self.value_dict.get('text')

    def get_original_text(self) -> str:
        """
        Gets the original (non-oracle) rules text of the card printing
        :return: The card printing's original text
        """
        return self.value_dict.get('originalText')

    def get_artist(self) -> str:
        """
        Gets the artist of this card printing
        :return:
        """
        return self.value_dict['artist']

    def get_rarity_name(self) -> str:
        return self.value_dict['rarity']

    def get_flavour_text(self) -> str:
        return self.value_dict.get('flavorText')

    def get_original_type(self) -> str:
        return self.value_dict.get('originalType')

    def has_rulings(self) -> bool:
        return 'rulings' in self.value_dict

    def get_rulings(self) -> List[dict]:
        return self.value_dict['rulings']

    def get_json_id(self) -> str:
        return self.value_dict['uuid']

    def get_layout(self) -> str:
        return self.value_dict['layout']

    def get_side(self) -> str:
        return self.value_dict.get('side')

    def get_legalities(self) -> Dict[str, str]:
        return self.value_dict['legalities'] if 'legalities' in self.value_dict else {}

    def get_name_count(self) -> int:
        return len(self.value_dict['names'])

    def get_watermark(self) -> str:
        return self.value_dict.get('watermark')

    def get_border_colour(self) -> str:
        return self.value_dict.get('borderColor')

    def get_scryfall_id(self) -> str:
        return self.value_dict.get('scryfallId')

    def is_reserved(self) -> bool:
        return 'reserved' in self.value_dict and self.value_dict['reserved']

    def is_starter_printing(self) -> bool:
        return 'starter' in self.value_dict and self.value_dict['starter']

    def is_timeshifted(self) -> bool:
        return 'isTimeshifted' in self.value_dict and self.value_dict['isTimeshifted']

    def has_other_names(self) -> bool:
        return 'names' in self.value_dict

    def get_other_names(self) -> List[str]:
        return [n for n in self.value_dict['names'] if n != self.get_name()]

    def set_number(self, cnum: str) -> None:
        if self.number is not None:
            raise Exception('Cannot set the collector number if it has already been set')

        self.number = cnum

    def sanitise_name(self) -> str:
        return self.value_dict['name']

    def pow_tuff_to_num(self, val) -> float:
        if val == '\u221e':
            return math.inf

        match = re.search(r'(-?[\d.]+)', str(val))
        if match:
            return float(match.group())

        return 0


class StagedSet:
    """
    Class for staging a set record from json
    """

    def __init__(self, code: str, value_dict: dict):
        self.code = code.upper()
        self.value_dict = value_dict
        self.staged_cards = list()

        for card in self.value_dict['cards']:
            self.add_card(card)

    def add_card(self, card: dict) -> None:
        staged_card = StagedCard(card)
        self.staged_cards.append(staged_card)

    def get_cards(self) -> List[StagedCard]:
        return sorted(self.staged_cards)

    def get_code(self) -> str:
        return self.code

    def get_release_date(self) -> Optional[datetime.date]:
        """
        Gets the date that this set was released
        :return:
        """
        return self.value_dict['releaseDate']

    def get_name(self) -> str:
        """
        Gets the name of the set
        :return:
        """
        return self.value_dict['name']

    def get_type(self) -> str:
        """
        Gets the type of the set
        :return:
        """
        return self.value_dict.get('type')

    def get_block(self) -> str:
        return self.value_dict.get('block')

    def has_block(self) -> bool:
        return 'block' in self.value_dict

    def get_keyrune_code(self) -> str:
        mappings = {
            # Generic M Symbol
            'PWOR': 'pmtg1',
            'WC99': 'pmtg1',
            'PWOS': 'pmtg1',
            'WC00': 'pmtg1',
            'CST': 'pmtg1',
            'G99': 'pmtg1',
            'WC01': 'pmtg1',
            'WC02': 'pmtg1',
            'WC03': 'pmtg1',
            'WC04': 'pmtg1',
            'WC97': 'pmtg1',
            'WC98': 'pmtg1',
            'G11': 'pmtg1',
            'L12': 'pmtg1',
            'L13': 'pmtg1',
            'L14': 'pmtg1',
            'L15': 'pmtg1',
            'L16': 'pmtg1',
            'L17': 'pmtg1',
            'JGP': 'pmtg1',
            'MGB': 'pmtg1',
            'P07': 'pmtg1',
            'P08': 'pmtg1',
            'P09': 'pmtg1',
            'P10': 'pmtg1',
            'P11': 'pmtg1',
            'P15A': 'pmtg1',
            'PCEL': 'pmtg1',
            'PCMP': 'pmtg1',
            'PGPX': 'pmtg1',
            'PJJT': 'pmtg1',
            'PLGM': 'pmtg1',
            'PLPA': 'pmtg1',
            'PMPS06': 'pmtg1',
            'PPRE': 'pmtg1',
            'PRED': 'pmtg1',
            'PREL': 'pmtg1',
            'PS14': 'pmtg1',
            'PS15': 'pmtg1',
            'PS16': 'pmtg1',
            'PS17': 'pmtg1',
            'PS18': 'pmtg1',
            'PSDC': 'pmtg1',
            'PTC': 'pmtg1',
            'RQS': 'pmtg1',

            # DCI Symbol
            'PSUS': 'parl',
            'G00': 'parl',
            'G01': 'parl',
            'G02': 'parl',
            'G03': 'parl',
            'G04': 'parl',
            'G05': 'parl',
            'G06': 'parl',
            'G07': 'parl',
            'G08': 'parl',
            'G09': 'parl',
            'G10': 'parl',
            'F01': 'parl',
            'F02': 'parl',
            'F03': 'parl',
            'F04': 'parl',
            'F05': 'parl',
            'F06': 'parl',
            'F07': 'parl',
            'F08': 'parl',
            'F09': 'parl',
            'F10': 'parl',
            'MPR': 'parl',
            'PR2': 'parl',
            'P03': 'parl',
            'P04': 'parl',
            'P05': 'parl',
            'P06': 'parl',
            'P2HG': 'parl',
            'PARC': 'parl',
            'PGTW': 'parl',
            'PG07': 'parl',
            'PG08': 'parl',
            'PHOP': 'parl',
            'PJSE': 'parl',
            'PRES': 'parl',
            'PWP09': 'parl',
            'PWP10': 'parl',
            'PWPN': 'parl',

            'PAL00': 'parl2',
            'PAL02': 'parl2',
            'PAL03': 'parl2',
            'PAL04': 'parl2',
            'PAL05': 'parl2',
            'PAL06': 'parl2',

            # FNM Symbol
            'FNM': 'pfnm',

            'PAL01': 'parl2',

            'ANA': 'parl3',

            'CED': 'xcle',
            'CEI': 'xice',

            'CP1': 'pmei',
            'CP2': 'pmei',
            'CP3': 'pmei',
            'F11': 'pmei',
            'F12': 'pmei',
            'F13': 'pmei',
            'F14': 'pmei',
            'F15': 'pmei',
            'F16': 'pmei',
            'F17': 'pmei',
            'F18': 'pmei',
            'G17': 'pmei',
            'HHO': 'pmei',
            'HTR': 'pmei',
            'HTR17': 'pmei',
            'J12': 'pmei',
            'J13': 'pmei',
            'J14': 'pmei',
            'J15': 'pmei',
            'J16': 'pmei',
            'J17': 'pmei',
            'J18': 'pmei',
            'OLGC': 'pmei',
            'OVNT': 'pmei',
            'PF19': 'pmei',
            'PLNY': 'pmei',
            'PNAT': 'pmei',
            'PPRO': 'pmei',
            'PURL': 'pmei',
            'PWCQ': 'pmei',
            'PWP11': 'pmei',
            'PWP12': 'pmei',

            # Duel Decks
            'DD1': 'evg',
            'DVD': 'ddc',
            'PDD2': 'dd2',
            'GVL': 'ddd',
            'JVC': 'dd2',

            'FBB': '3ed',
            'SUM': '3ed',

            # Oversized
            'OC13': 'c13',
            'OC14': 'c14',
            'OC15': 'c15',
            'OC16': 'c16',
            'OC17': 'c17',
            'OC18': 'c18',
            'OHOP': 'hop',
            'OPC2': 'pc2',
            'OARC': 'arc',
            'OCM1': 'cm1',
            'OCMD': 'cmd',
            'PCMD': 'cmd',
            'OE01': 'e01',
            'OPCA': 'pca',

            'UGIN': 'frf',

            # Core set promos
            'PM10': 'm10',
            'PM11': 'm11',
            'PM12': 'm12',
            'PM13': 'm13',
            'PM14': 'm14',
            'PM15': 'm15',
            'PM19': 'm19',

            'PPC1': 'm15',
            'G18': 'm19',

            'GK2': 'rna',

            'P10E': '10e',
            'PAER': 'aer',
            'PAKH': 'akh',
            'PAVR': 'avr',
            'PBBD': 'bbd',
            'PBFZ': 'bfz',
            'PBNG': 'bng',
            'PDGM': 'dgm',
            'PDKA': 'dka',
            'PDOM': 'dom',
            'PDTK': 'dtk',
            'PEMN': 'emn',
            'PFRF': 'frf',
            'PGRN': 'grn',
            'PGTC': 'gtc',
            'PHOU': 'hou',
            'PISD': 'isd',
            'PJOU': 'jou',
            'PKLD': 'kld',
            'PKTK': 'ktk',
            'PMBS': 'mbs',
            'PNPH': 'nph',
            'POGW': 'ogw',
            'PORI': 'ori',
            'PRIX': 'rix',
            'PRNA': 'rna',
            'PROE': 'roe',
            'PRTR': 'rtr',
            'PRW2': 'rna',
            'PRWK': 'grn',
            'PSOI': 'soi',
            'PSOM': 'som',
            'PSS1': 'bfz',
            'PSS2': 'xln',
            'PSS3': 'm19',
            'PTHS': 'ths',
            'PTKDF': 'dtk',
            'PUST': 'ust',
            'PVAN': 'van',
            'PWWK': 'wwk',
            'PXLN': 'xln',
            'PXTC': 'xln',
            'PZEN': 'zen',
            'TBTH': 'bng',
            'TDAG': 'ths',
            'TFTH': 'ths',
            'THP1': 'ths',
            'THP2': 'bng',
            'THP3': 'jou',

            # Open the Helvault
            'PHEL': 'avr',

            'PAL99': 'usg',
            'PUMA': 'usg',

            # Asia Pacific Lands
            'PALP': 'papac',
            'PJAS': 'papac',
            'PELP': 'peuro',

            'PBOK': 'pbook',
            'PHPR': 'pbook',

            'PDTP': 'dpa',
            'PDP11': 'dpa',
            'PDP12': 'dpa',
            'PDP10': 'dpa',
            'PDP13': 'dpa',
            'PDP14': 'dpa',

            # Salvat
            'PHUK': 'psalvat05',
            'PSAL': 'psalvat05',
            'PS11': 'psalvat11',

            # IDW
            'PI13': 'pidw',
            'PI14': 'pidw',

            'PMOA': 'pmodo',
            'PRM': 'pmodo',

            'TD0': 'xmods',

            'PMPS07': 'pmps',
            'PMPS08': 'pmps',
            'PMPS09': 'pmps',
            'PMPS10': 'pmps',
            'PMPS11': 'pmps',

            'PPOD': 'por',

            # Timeshifted
            'TSB': 'tsp',

            'REN': 'xren',
            'RIN': 'xren',

            'ITP': 'x2ps',

        }
        code = mappings.get(self.get_code())
        if code:
            return code

        return self.code.lower()
