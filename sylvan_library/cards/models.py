"""
Models for cards
"""

import datetime
import os
import random
import re

from django.db import models
from django.contrib.auth.models import User
from bitfield import BitField

CARD_LAYOUT_CHOICES = (
    ('normal', 'Normal'),
    ('split', 'Split'),
    ('flip', 'Flip'),
    ('transform', 'Transform'),
    ('token', 'Token'),
    ('planar', 'Planar'),
    ('scheme', 'Scheme'),
    ('leveler', 'Leveler'),
    ('vanguard', 'Vanguard'),
    ('meld', 'Meld'),
    ('host', 'Host'),
    ('augment', 'Augment'),
    ('saga', 'Saga'),
)

CARD_LEGALITY_RESTRICTION_CHOICES = (
    ('Legal', 'Legal'),
    ('Banned', 'Banned'),
    ('Restricted', 'Restricted'),
)


class Block(models.Model):
    """
    Model for a block of sets
    """
    name = models.CharField(max_length=200, unique=True)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name


class Format(models.Model):
    """
    Model for a format of cards
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Set(models.Model):
    """
    Model for a set of cards
    """
    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)

    block = models.ForeignKey(Block, null=True, blank=True, related_name='sets',
                              on_delete=models.CASCADE)

    def get_keyrune_setcode(self):
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
        code = mappings.get(self.code)
        if code:
            return code

        return self.code.lower()

    def __str__(self):
        return self.name


class Rarity(models.Model):
    """
    Model for a card rarity
    """
    symbol = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=30, unique=True)
    display_order = models.IntegerField(unique=True)

    def __str__(self):
        return self.name


class Colour(models.Model):
    """
    Model for a card's colour
    """
    symbol = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=15, unique=True)
    display_order = models.IntegerField(unique=True)
    bit_value = models.IntegerField(unique=True)

    @staticmethod
    def white():
        return Colour.objects.get(symbol='W')

    @staticmethod
    def blue():
        return Colour.objects.get(symbol='U')

    @staticmethod
    def black():
        return Colour.objects.get(symbol='B')

    @staticmethod
    def red():
        return Colour.objects.get(symbol='R')

    @staticmethod
    def green():
        return Colour.objects.get(symbol='G')

    def __str__(self):
        return self.name


class Card(models.Model):
    """
    Model for a unique card
    """
    name = models.CharField(max_length=200, unique=True)

    cost = models.CharField(max_length=50, blank=True, null=True)
    cmc = models.FloatField()
    colour_flags = BitField(flags=('white', 'blue', 'black', 'red', 'green'))
    colour_identity_flags = BitField(flags=('white', 'blue', 'black', 'red', 'green'))
    colour_count = models.IntegerField()
    colour_sort_key = models.IntegerField()
    colour_weight = models.IntegerField()

    type = models.CharField(max_length=100, blank=True, null=True)
    subtype = models.CharField(max_length=100, blank=True, null=True)

    power = models.CharField(max_length=20, blank=True, null=True)
    num_power = models.FloatField()
    toughness = models.CharField(max_length=20, blank=True, null=True)
    num_toughness = models.FloatField()
    loyalty = models.CharField(max_length=20, blank=True, null=True)
    num_loyalty = models.FloatField()

    rules_text = models.CharField(max_length=1000, blank=True, null=True)
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)
    side = models.CharField(max_length=1, blank=True, null=True)
    is_reserved = models.BooleanField()

    links = models.ManyToManyField('self')

    @staticmethod
    def get_random_card():
        last = Card.objects.count() - 1
        index = random.randint(0, last)
        return Card.objects.all()[index]

    def __str__(self):
        return self.name


class CardPrinting(models.Model):
    """
    Model for a certain card printed in a certain set
    """
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    artist = models.CharField(max_length=100)
    number = models.CharField(max_length=10, blank=True, null=True)
    original_text = models.CharField(max_length=1000, blank=True, null=True)
    original_type = models.CharField(max_length=200, blank=True, null=True)
    watermark = models.CharField(max_length=100, blank=True, null=True)

    # The unique identifier that mtgjson uses for the card
    # It is made up by doing an SHA1 hash of setCode + cardName + cardImageName
    json_id = models.CharField(max_length=40, unique=True)

    scryfall_id = models.CharField(max_length=40, blank=True, null=True)

    # The border colour of the card if it differs from the border colour of the rest of the set
    # (e.g. basic lands in Unglued)
    border_colour = models.CharField(max_length=10, blank=True, null=True)

    # The date this card was released. This is only set for promo cards.
    # The date may not be accurate to an exact day and month, thus only a partial date may be set
    release_date = models.DateField(blank=True, null=True)

    set = models.ForeignKey(Set, related_name='card_printings', on_delete=models.CASCADE)
    card = models.ForeignKey(Card, related_name='printings', on_delete=models.CASCADE)
    rarity = models.ForeignKey(Rarity, related_name='card_printings', on_delete=models.CASCADE)

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament
    # legal despite not being available in boosters.
    is_starter = models.BooleanField()

    class Meta:
        """
        Metaclass for CardPrinting
        """
        ordering = ['set__release_date']

    def __str__(self):
        return f'{self.card} in {self.set}'


class PhysicalCard(models.Model):
    """
    Model for joining one or more CardPrintingLanguages into a single card that can be owned
    """
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)

    def __str__(self):
        return '//'.join([str(x) for x in self.printed_languages.all()])

    def get_simple_string(self):
        if self.printed_languages.count() == 1:
            return str(self.printed_languages.first())

        base = self.printed_languages.first()
        return base.language.name + ' ' \
               + '//'.join(p.card_printing.card.name for p in self.printed_languages.all()) \
               + ' in ' + base.card_printing.set.name

    def apply_user_change(self, change_count: int, user: User):
        if user is None:
            return False

        try:
            existing_card = UserOwnedCard.objects.get(physical_card=self, owner=user)
            existing_card.count += change_count
            if existing_card.count <= 0:
                existing_card.delete()
            else:
                existing_card.clean()
                existing_card.save()
        except UserOwnedCard.DoesNotExist:
            if change_count <= 0:
                return False
            new_card = UserOwnedCard(count=change_count, owner=user, physical_card=self)
            new_card.clean()
            new_card.save()

        change = UserCardChange(physical_card=self, owner=user, difference=change_count,
                                date=datetime.datetime.now())
        change.clean()
        change.save()
        return True


class CardPrintingLanguage(models.Model):
    """
    Model for a card printed in a certain set of a certain language
    """
    language = models.ForeignKey('Language', related_name='cards', on_delete=models.CASCADE)
    card_name = models.CharField(max_length=200)
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    multiverse_id = models.IntegerField(blank=True, null=True)

    card_printing = models.ForeignKey(CardPrinting, related_name='printed_languages',
                                      on_delete=models.CASCADE)

    physical_cards = models.ManyToManyField(PhysicalCard, related_name='printed_languages')

    class Meta:
        """
        Meta information for CardPrintingLanguages
        """
        unique_together = ('language', 'card_name', 'card_printing')

    def __str__(self):
        return f'{self.language} {self.card_printing}'

    def get_image_path(self):
        image_name = re.sub(r'\W', 's', self.card_printing.number)
        if self.card_printing.card.layout == 'transform':
            image_name += '_' + self.card_printing.card.side
        return os.path.join(
            'card_images',
            self.language.code.lower(),
            '_' + self.card_printing.set.code.lower(),
            image_name + '.jpg')


class UserOwnedCard(models.Model):
    """
    Model for a user owned a number of physical cards
    """
    count = models.IntegerField()

    physical_card = models.ForeignKey(PhysicalCard, related_name='ownerships',
                                      on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owned_cards', on_delete=models.CASCADE)

    class Meta:
        """
        Meta information for the UserOwnedCard class
        """
        unique_together = ('physical_card', 'owner')

    def __str__(self):
        return f'{self.owner} owns {self.count} of {self.physical_card}'


class UserCardChange(models.Model):
    """
    Model for a change in the number of cards that a user owns
    """
    date = models.DateTimeField()
    difference = models.IntegerField()

    physical_card = models.ForeignKey(PhysicalCard, related_name='user_changes',
                                      on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='card_changes', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.date} {self.difference} {self.physical_card}'


class CardRuling(models.Model):
    """
    Model for a ruling made on a card
    """
    date = models.DateField()
    text = models.CharField(max_length=4000)

    card = models.ForeignKey(Card, related_name='rulings', on_delete=models.CASCADE)

    class Meta:
        """
        Meta configuration for the CardRuling class
        """
        unique_together = ('date', 'text', 'card')

    def __str__(self):
        return f'Ruling for {self.card}: {self.text}'


class CardLegality(models.Model):
    """
    Model for a restriction on the legality of a card in a format
    """
    card = models.ForeignKey(Card, related_name='legalities', on_delete=models.CASCADE)
    format = models.ForeignKey(Format, related_name='card_legalities', on_delete=models.CASCADE)
    restriction = models.CharField(max_length=50, choices=CARD_LEGALITY_RESTRICTION_CHOICES)

    class Meta:
        """
        Meta configuration for the CardLegality class
        """
        unique_together = (
            'card',
            'format',
            'restriction',
        )

    def __str__(self):
        return f'{self.card} is {self.restriction} in {self.format}'


class CardTag(models.Model):
    """
    Model for a user owned tag that can be applied to many cards
    """
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name='card_tags', on_delete=models.CASCADE)
    cards = models.ManyToManyField(Card, related_name='tags')

    def __str__(self):
        return self.name


class Deck(models.Model):
    """
    Model for a user owned deck of cards
    """
    date_created = models.DateField()
    last_modified = models.DateField()

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name='decks', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class DeckCard(models.Model):
    """
    Model for a card in a Deck
    """
    count = models.IntegerField()

    card = models.ForeignKey(Card, related_name='deck_cards', on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, related_name='cards', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.card} in {self.deck}'


class Language(models.Model):
    """
    Model for a language that a card could be printed in
    """
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, null=True, blank=True)

    ENGLISH = None

    def __str__(self):
        return self.name

    @staticmethod
    def english():
        if not Language.ENGLISH:
            Language.ENGLISH = Language.objects.get(name='English')

        return Language.ENGLISH


class CardImage(models.Model):
    printed_language = models.OneToOneField(
        CardPrintingLanguage,
        related_name='image',
        on_delete=models.CASCADE)

    downloaded = models.BooleanField()
