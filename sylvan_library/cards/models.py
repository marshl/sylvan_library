"""
Models for cards
"""

import random
from os import path

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
        if self.multiverse_id is None:
            return None

        multiverse_string = str(self.multiverse_id)
        # Break up images over multiple folders to stop too many being placed in one folder
        return path.join('card_images',
                         multiverse_string[0:1],
                         multiverse_string[0:2] if len(multiverse_string) >= 2 else '',
                         multiverse_string[0:3] if len(multiverse_string) >= 3 else '',
                         multiverse_string + '.jpg')


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

    def __str__(self):
        return self.name
