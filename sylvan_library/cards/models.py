"""
Models for cards
"""

import datetime
import os
import random
import re
from typing import Dict, List, Optional

from django.db import models
from django.db.models import Sum, IntegerField, Case, When, Q, Avg
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
    ('emblem', 'Emblem'),
    ('double_faced_token', 'Double-faced Token'),
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
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Set(models.Model):
    """
    Model for a set of cards
    """
    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True)

    block = models.ForeignKey(Block, null=True, blank=True, related_name='sets',
                              on_delete=models.CASCADE)

    keyrune_code = models.CharField(max_length=10)

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
    def white() -> 'Colour':
        """
        Gets the colour object for white
        :return:
        """
        return Colour.objects.get(symbol='W')

    @staticmethod
    def blue() -> 'Colour':
        """
        Gets the colour object for blue
        :return:
        """
        return Colour.objects.get(symbol='U')

    @staticmethod
    def black() -> 'Colour':
        """
        Gets the colour object for black
        :return:
        """
        return Colour.objects.get(symbol='B')

    @staticmethod
    def red() -> 'Colour':
        """
        Gets the colour object for red
        :return:
        """
        return Colour.objects.get(symbol='R')

    @staticmethod
    def green() -> 'Colour':
        """
        Gets the colour object for green
        :return:
        """
        return Colour.objects.get(symbol='G')

    @staticmethod
    def colour_names_to_flags(colour_names: List[str]) -> int:
        """
        Converts a list of colour names into the combined flags of those colours
        :param colour_names:
        :return:
        """
        flags = 0
        for colour_name in colour_names:
            flags |= Colour.objects.get(name__iexact=colour_name).bit_value

        return flags

    @staticmethod
    def colour_codes_to_flags(colour_codes: List[str]) -> int:
        """
        Converts a list of colour codes to the combined flags of those colours
        :param colour_codes: A list of colour codes (single characters representing the colours)
        :return: The combined colour flags
        """
        flags = 0
        for symbol in colour_codes:
            flags |= Colour.objects.get(symbol__iexact=symbol).bit_value

        return flags

    def __str__(self):
        return self.name


class Card(models.Model):
    """
    Model for a unique card
    """
    name = models.CharField(max_length=200)

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
    scryfall_oracle_id = models.CharField(max_length=36, blank=True, null=True)
    is_token = models.BooleanField()
    links = models.ManyToManyField('self')

    @staticmethod
    def get_random_card() -> 'Card':
        """
        Gets a card chosen at random
        :return:
        """
        last = Card.objects.count() - 1
        index = random.randint(0, last)
        return Card.objects.all()[index]

    def __str__(self):
        return self.name

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this card
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :param user: The user who should own the card
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for card_printing in self.printings.all()
                for printed_language in card_printing.printed_languages.all()
                for physical_card in printed_language.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.printings.aggregate(
            card_count=Sum(
                Case(
                    When(
                        printed_languages__physical_cards__ownerships__owner=user,
                        then='printed_languages__physical_cards__ownerships__count'),
                    output_field=IntegerField(),
                    default=0
                )
            )
        )['card_count']

    def get_all_sides(self) -> List['Card']:
        return [self] + list(self.links.order_by('side').all())


class CardPrinting(models.Model):
    """
    Model for a certain card printed in a certain set
    """
    flavour_text = models.CharField(max_length=500, blank=True, null=True)
    artist = models.CharField(max_length=100, blank=True, null=True)
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

    set = models.ForeignKey(Set, related_name='card_printings', on_delete=models.CASCADE)
    card = models.ForeignKey(Card, related_name='printings', on_delete=models.CASCADE)
    rarity = models.ForeignKey(Rarity, related_name='card_printings', on_delete=models.CASCADE)

    # Set to true if this card was only released as part of a core box set.
    # These are technically part of the core sets and are tournament
    # legal despite not being available in boosters.
    is_starter = models.BooleanField()

    is_timeshifted = models.BooleanField()

    class Meta:
        """
        Metaclass for CardPrinting
        """
        ordering = ['set__release_date', 'set__name', 'number']

    def __str__(self):
        return f'{self.card} in {self.set}'

    def get_set_keyrune_code(self) -> str:
        """
        Gets the keyrune code that should be used for this printing
        In 99% of all cases, this will return the same value as printing.set.keyrune_code
        But for Guild Kit printings, the guild symbol should be used instead
        :return:
        """
        if self.set.code in ('GK1', 'GK2') and self.watermark:
            return self.watermark.lower()

        return self.set.keyrune_code

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this printing
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :param user: The user who should own the card
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for printed_language in self.printed_languages.all()
                for physical_card in printed_language.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.printed_languages.aggregate(
            card_count=Sum(
                Case(
                    When(
                        physical_cards__ownerships__owner=user,
                        then='physical_cards__ownerships__count'),
                    output_field=IntegerField(),
                    default=0
                )
            )
        )['card_count']


class PhysicalCard(models.Model):
    """
    Model for joining one or more CardPrintingLanguages into a single card that can be owned
    """
    layout = models.CharField(max_length=50, choices=CARD_LAYOUT_CHOICES)

    def __str__(self):
        return '//'.join([str(x) for x in self.printed_languages.all()])

    def get_simple_string(self) -> str:
        """
        Gets a simple representation of this Physical Card
        :return:
        """
        if self.printed_languages.count() == 1:
            return str(self.printed_languages.first())

        base = self.printed_languages.first()
        return base.language.name + ' ' \
               + '//'.join(p.card_printing.card.name for p in self.printed_languages.all()) \
               + ' in ' + base.card_printing.set.name

    def get_display_for_adding(self) -> str:
        """
        Gets a simple representation of this Physical card without card names
        :return:
        """
        if self.printed_languages.count() == 1:
            printlang = self.printed_languages.first()
            return f"{printlang.language} {printlang.card_printing.set}"

        return self.get_simple_string()

    def apply_user_change(self, change_count: int, user: User) -> bool:
        """
        Applies a change of the number of cards a user owns (can add or subtract cards)
        :param change_count: The number of cards that should be added/removed
        :param user: The user that the cards should be added/removed to
        :return: True if the change was successful, otherwise False
        """
        if user is None or change_count == 0:
            return False

        try:
            existing_card = UserOwnedCard.objects.get(physical_card=self, owner=user)
            if change_count < 0 and abs(change_count) >= existing_card.count:
                # If the count is below 1 than there is no point thinking that the user "owns"
                # the card anymore, so just delete the record
                change_count = -existing_card.count
                existing_card.delete()
            else:
                existing_card.count += change_count
                existing_card.clean()
                existing_card.save()
        except UserOwnedCard.DoesNotExist:
            if change_count <= 0:
                # You can't subtract cards when you don' have any
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

    def get_image_path(self) -> Optional[str]:
        """
        Gets the relative file path of this prined language
        :return:
        """
        if self.language.code is None:
            return None
        image_name = re.sub(r'\W', 's', self.card_printing.number)
        if self.card_printing.card.layout in ('transform', 'double_faced_token'):
            image_name += '_' + self.card_printing.card.side

        if self.card_printing.card.is_token:
            image_name = 't' + image_name

        return os.path.join(
            'card_images',
            self.language.code.lower(),
            '_' + self.card_printing.set.code.lower(),
            image_name + '.jpg')

    def get_user_ownership_count(self, user: User, prefetched: bool = False) -> int:
        """
        Returns the total number of cards that given user owns of this printed language
        :param user: The user who should own the card
        :param prefetched: Whether to use prefetched data, or to get it from the database again
        :return: The ownership total
        """
        if prefetched:
            return sum(
                ownership.count
                for physical_card in self.physical_cards.all()
                for ownership in physical_card.ownerships.all()
                if ownership.owner_id == user.id
            )

        return self.physical_cards.aggregate(
            card_count=Sum(
                Case(
                    When(
                        ownerships__owner=user,
                        then='ownerships__count'),
                    output_field=IntegerField(),
                    default=0
                )
            )
        )['card_count']


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

    FORMAT_CHOICES = (
        ('standard', 'Standard'),
        ('legacy', 'Legacy'),
        ('prerelease', 'Pre-release'),
        ('mtgo', 'MTGO'),
        ('unformat', 'Unformat'),
        ('unknown', 'Unknown'),
        ('heirloom', 'Heirloom'),
        ('vintage', 'Vintage'),
        ('edh', 'Commander / EDH'),
        ('archenemy', 'Archenemy'),
        ('planechase', 'Planechase'),
        ('vanguard', 'Vanguard'),
        ('modern', 'Modern'),
        ('pauper', 'Pauper'),
        ('noble', 'Noble'),
        ('casual', 'Casual'),
        ('hero', 'Hero'),
        ('quest_magic_rpg', 'Quest Magic RPGs'),
        ('quest_magic', 'Quest Magic'),
        ('block_constructed', 'Block Constructed'),
        ('limited', 'Limited'),
        ('duel_commander', 'Duel Commander'),
        ('tiny_leaders', 'Tiny Leaders'),
        ('highlander', 'Highlander'),
        ('magic_duels', 'Magic Duels'),
        ('penny_dreadful', 'Penny Dreadful'),
        ('frontier', 'Frontier'),
        ('leviathan', 'Leviathan'),
        ('1v1_commander', '1v1 Commander'),
        ('pauper_edh', 'Pauper EDH'),
        ('canadian_highlander', 'Canadian Highlander'),
        ('brawl', 'Brawl'),
        ('arena', 'Arena'),
        ('oathbreaker', 'Oathbreaker'),
    )

    date_created = models.DateField()
    last_modified = models.DateField(auto_now=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, related_name='decks', on_delete=models.CASCADE)
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES)

    # land_count_w = models.IntegerField(null=True, blank=True)
    # land_count_u = models.IntegerField(null=True, blank=True)
    # land_count_b = models.IntegerField(null=True, blank=True)
    # land_count_r = models.IntegerField(null=True, blank=True)
    # land_count_g = models.IntegerField(null=True, blank=True)
    #
    # symbol_count_u = models.IntegerField(null=True, blank=True)
    # symbol_count_b = models.IntegerField(null=True, blank=True)
    # symbol_count_w = models.IntegerField(null=True, blank=True)
    # symbol_count_r = models.IntegerField(null=True, blank=True)
    # symbol_count_g = models.IntegerField(null=True, blank=True)
    #
    # average_cmc = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_card_groups(self) -> Dict[str, List['DeckCard']]:
        board_cards = self.cards.filter(board='main').order_by('card__name')
        lands = board_cards.filter(card__type__contains='Land')
        creatures = board_cards.exclude(id__in=lands).filter(card__type__contains='Creature')
        instants = board_cards.filter(card__type__contains='Instant')
        sorceries = board_cards.filter(card__type__contains='Sorcery')
        enchantments = board_cards.exclude(id__in=lands | creatures).filter(
            card__type__contains='Enchantment')
        artifacts = board_cards.exclude(id__in=lands | creatures | enchantments).filter(
            card__type__contains='Artifact')
        planeswalkers = board_cards.filter(card__type__contains='Planeswalker')
        other = board_cards.exclude(
            id__in=lands | creatures | instants | sorceries | artifacts | enchantments)

        return {
            'Land': lands,
            'Creature': creatures,
            'Instant': instants,
            'Sorcery': sorceries,
            'Artifact': artifacts,
            'Enchantment': enchantments,
            'Planeswalker': planeswalkers,
            'Other': other
        }

    # def save(self, *args, **kwargs):
    #     self.calculate_land_symbol_counts()
    #     self.calculate_cost_symbol_counts()
    #     self.calculate_avg_cmc()
    #     super().save(*args, **kwargs)

    def calculate_land_symbol_counts(self) -> Dict[str, int]:
        land_cards = self.cards.filter(board='main', card__type__contains='Land')
        result = {}
        for colour in Colour.objects.all():
            result['land_count_' + colour.symbol.lower()] = land_cards \
                .filter(card__rules_text__iregex=':.*?add[^\n]*?{' + colour.symbol + '}') \
                .aggregate(sum=Sum('count'))['sum']
        return result

    def calculate_cost_symbol_counts(self) -> Dict[str, int]:
        cards = self.cards.filter(board='main-')
        result = {}
        for colour in Colour.objects.all():
            result['symbol_count_' + colour.symbol.lower()] = \
                sum(deck_card.card.cost.count(colour.symbol) for deck_card in cards)

        return result

    def calculate_avg_cmc(self) -> float:
        return self.cards.filter(board='main') \
            .exclude(card__tpe__contains='Land') \
            .aggregate(Avg('card__cmd'))['card__cmc__avg']


class DeckCard(models.Model):
    """
    Model for a card in a Deck
    """

    BOARD_CHOICES = (
        ('main', 'Main'),
        ('side', 'Side'),
        ('maybe', 'Maybe'),
        ('acquire', 'Acquire'),
    )

    count = models.IntegerField()
    card = models.ForeignKey(Card, related_name='deck_cards', on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, related_name='cards', on_delete=models.CASCADE)
    board = models.CharField(max_length=20, choices=BOARD_CHOICES, default='main')

    def __str__(self):
        return f'{self.card} in {self.deck}'

    def as_deck_text(self) -> str:
        """
        COnverts this card to how it should appear in board text of the DeckForm
        :return: The text representation version of the card for use in the DeckForm
        """
        if self.card.layout == 'split':
            card_name = ' // '.join(c.name for c in self.card.get_all_sides())
        else:
            card_name = self.card.name
        return f'{self.count}x {card_name}'


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
    def english() -> 'Language':
        """
        Gets the cached english language object (English is the default language, and it used
        quite a lot, so this reduces the number of queries made quite a bit)
        :return:
        """
        if not Language.ENGLISH:
            Language.ENGLISH = Language.objects.get(name='English')

        return Language.ENGLISH


class CardImage(models.Model):
    """
    Model for a CardPrintingLanguage's image download status
    (in the future, this might even contain the image itself)
    """
    printed_language = models.OneToOneField(
        CardPrintingLanguage,
        related_name='image',
        on_delete=models.CASCADE)

    downloaded = models.BooleanField()
