import random
from os import path

from django.db import models
from django.contrib.auth.models import User
from bitfield import BitField

CARD_LAYOUT_CHOICES = (
    ('normal', 'Normal'),
    ('split', 'Split'),
    ('flip', 'Flip'),
    ('double-faced', 'Double-faced'),
    ('token', 'Token'),
    ('plane', 'Plane'),
    ('scheme', 'Scheme'),
    ('phenomenon', 'Phenomenon'),
    ('leveler', 'Leveler'),
    ('vanguard', 'Vanguard'),
    ('meld', 'Meld'),
)

CARD_LEGALITY_RESTRICTION_CHOICES = (
    ('Legal', 'Legal'),
    ('Banned', 'Banned'),
    ('Restricted', 'Restricted'),
)


class Block(models.Model):
    name = models.CharField(max_length=200, unique=True)
    release_date = models.DateField()

    def __str__(self):
        return self.name


class Format(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Set(models.Model):
    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    mci_code = models.CharField(max_length=10, blank=True, null=True)
    border_colour = models.CharField(max_length=20, blank=True, null=True)

    block = models.ForeignKey(Block, null=True, related_name='sets')

    def __str__(self):
        return self.name


class Rarity(models.Model):
    symbol = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=15, unique=True)
    display_order = models.IntegerField(unique=True)

    def __str__(self):
        return self.name


class Colour(models.Model):
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

    # Vanguard fields
    hand_modifier = models.IntegerField(blank=True, null=True)
    life_modifier = models.IntegerField(blank=True, null=True)

    rules_text = models.CharField(max_length=1000, blank=True, null=True)
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)
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
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    artist = models.CharField(max_length=100)
    collector_number = models.IntegerField()
    collector_letter = models.CharField(max_length=1, blank=True, null=True)
    original_text = models.CharField(max_length=1000, blank=True, null=True)
    original_type = models.CharField(max_length=200, blank=True, null=True)
    watermark = models.CharField(max_length=100, blank=True, null=True)

    # The unique identifier that mtgjson uses for the card
    # It is made up by doing an SHA1 hash of setCode + cardName + cardImageName
    json_id = models.CharField(max_length=40, unique=True)

    mci_number = models.IntegerField(blank=True, null=True)

    # The border colour of the card if it differs from the border colour of the rest of the set
    # (e.g. basic lands in Unglued)
    border_colour = models.CharField(max_length=10, blank=True, null=True)

    # The date this card was released. This is only set for promo cards.
    # The date may not be accurate to an exact day and month, thus only a partial date may be set
    release_date = models.DateField(blank=True, null=True)

    set = models.ForeignKey(Set, related_name='card_printings')
    card = models.ForeignKey(Card, related_name='printings')
    rarity = models.ForeignKey(Rarity, related_name='card_printings')

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament legal despite not being available in boosters.
    is_starter = models.BooleanField()

    def __str__(self):
        return f'{self.card} in {self.set}'


class PhysicalCard(models.Model):
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)

    def __str__(self):
        return 'Physical ' + '//'.join([str(x) for x in self.printed_languages.all()])


class CardPrintingLanguage(models.Model):
    language = models.ForeignKey('Language', related_name='cards')
    card_name = models.CharField(max_length=200)
    multiverse_id = models.IntegerField(blank=True, null=True)

    card_printing = models.ForeignKey(CardPrinting, related_name='printed_languages')

    physical_cards = models.ManyToManyField(PhysicalCard, related_name='printed_languages')

    class Meta:
        unique_together = ('language', 'card_name', 'card_printing')

    def __str__(self):
        return f'{self.language} {self.card_printing}'

    def get_image_path(self):
        if self.multiverse_id is None:
            return None

        ms = str(self.multiverse_id)
        # Break up images over multiple folders to stop too many being placed in one folder
        return path.join('static', 'card_images',
                         ms[0:1],
                         ms[0:2] if len(ms) >= 2 else '',
                         ms[0:3] if len(ms) >= 3 else '',
                         ms + '.jpg')


class UserOwnedCard(models.Model):
    count = models.IntegerField()

    physical_card = models.ForeignKey(PhysicalCard, related_name='ownerships')
    owner = models.ForeignKey(User, related_name='owned_cards')

    class Meta:
        unique_together = ('physical_card', 'owner')

    def __str__(self):
        return f'{self.owner} owns {self.count} of {self.physical_card}'


class UserCardChange(models.Model):
    date = models.DateTimeField()
    difference = models.IntegerField()

    physical_card = models.ForeignKey(PhysicalCard, related_name='user_changes')
    owner = models.ForeignKey(User, related_name='card_changes')

    def __str__(self):
        return f'{self.date} {self.difference} {self.physical_card}'


class CardRuling(models.Model):
    date = models.DateField()
    text = models.CharField(max_length=4000)

    card = models.ForeignKey(Card, related_name='rulings')

    class Meta:
        unique_together = ('date', 'text', 'card')

    def __str__(self):
        return f'Ruling for {self.card}: {self.text}'


class CardLegality(models.Model):
    card = models.ForeignKey(Card, related_name='legalities')
    format = models.ForeignKey(Format, related_name='card_legalities')
    restriction = models.CharField(max_length=50, choices=CARD_LEGALITY_RESTRICTION_CHOICES)

    class Meta:
        unique_together = (
            'card',
            'format',
            'restriction',
        )

    def __str__(self):
        return f'{self.card} is {self.restriction} in {self.format}'


class CardTag(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name='card_tags')
    cards = models.ManyToManyField(Card, related_name='tags')

    def __str__(self):
        return self.name


class Deck(models.Model):
    date_created = models.DateField()
    last_modified = models.DateField()

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name='decks')

    def __str__(self):
        return self.name


class DeckCard(models.Model):
    count = models.IntegerField()

    card = models.ForeignKey(Card, related_name='deck_cards')
    deck = models.ForeignKey(Deck, related_name='cards')

    def __str__(self):
        return f'{self.card} in {self.deck}'


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    mci_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True)

    def __str__(self):
        return self.name
