"""
Forms for the website module
"""
import re
from typing import Dict, Optional, List

from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Func, Value, F
from django_select2.forms import Select2MultipleWidget

from cards.models import (
    Card,
    CardPrinting,
    Colour,
    Deck,
    DeckCard,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from cardsearch.fieldsearch import FieldSearch
from cardsearch.namesearch import NameSearch


def get_physical_card_key_pair(physical_card: PhysicalCard, printing: CardPrinting):
    """
    Gets the ID and display name of th given PhysicalCard for the given CardPrinting
    :param physical_card: The physical card the user can select from
    :param printing: The printing of the physical card
    :return: A tuple of the physical card's ID and a display string
    """
    return (
        physical_card.id,
        f"{physical_card.get_display_for_adding()} ({printing.number})",
    )


class ChangeCardOwnershipForm(forms.Form):
    """
    A for mfor changing the number of cards that a user owns
    """

    count = forms.IntegerField()
    printed_language = forms.ChoiceField(widget=forms.Select)

    def __init__(self, printing: CardPrinting):
        super().__init__()
        if any(
            pl
            for pl in printing.printed_languages.all()
            if pl.language_id == Language.english().id
        ):
            # Put the english print first as that is the most likely one that the user will add
            english_print = next(
                pl
                for pl in printing.printed_languages.all()
                if pl.language_id == Language.english().id
            )
            choices = [
                get_physical_card_key_pair(physical_card, printing)
                for physical_card in english_print.physical_cards.all()
            ]
            choices.extend(
                [
                    get_physical_card_key_pair(physical_card, printing)
                    for lang in printing.printed_languages.all()
                    for physical_card in lang.physical_cards.all()
                    if lang.language_id != Language.english().id
                ]
            )
        else:
            choices = [
                get_physical_card_key_pair(physical_card, printing)
                for lang in printing.printed_languages.all()
                for physical_card in lang.physical_cards.all()
            ]

        self.fields["printed_language"].choices = choices


class SearchForm(forms.Form):
    """
    The base search form
    """

    def get_page_number(self) -> int:
        """
        Gets the current page number of the results
        :return: The current page number if it exists, otherwise the first page
        """
        try:
            return int(self.data.get("page"))
        except (TypeError, ValueError):
            return 1


class NameSearchForm(SearchForm):
    """
    The search form for searching only bu the card's name
    """

    card_name = forms.CharField(required=False)

    def get_search(self) -> NameSearch:
        """
        Gets the search object using the data from this form
        :return:
        """
        self.full_clean()
        search = NameSearch()
        search.card_name = self.data.get("card_name")
        search.build_parameters()
        search.search(self.get_page_number())
        return search


class FieldSearchForm(SearchForm):
    """
    The primary search form
    """

    card_name = forms.CharField(required=False)
    rules_text = forms.CharField(required=False)
    flavour_text = forms.CharField(required=False)
    type_text = forms.CharField(required=False)
    subtype_text = forms.CharField(required=False)
    mana_cost_text = forms.CharField(required=False)

    min_cmc = forms.IntegerField(required=False)
    max_cmc = forms.IntegerField(required=False)

    min_power = forms.IntegerField(required=False)
    max_power = forms.IntegerField(required=False)

    min_toughness = forms.IntegerField(required=False)
    max_toughness = forms.IntegerField(required=False)

    exclude_colours = forms.BooleanField(required=False)
    match_colours = forms.BooleanField(required=False)

    exclude_colourids = forms.BooleanField(required=False)
    match_colourids = forms.BooleanField(required=False)

    match_rarity = forms.BooleanField(required=False)

    match_sets = forms.BooleanField(required=False)
    sets = forms.ModelMultipleChoiceField(
        queryset=Set.objects.all().order_by("-release_date"),
        widget=Select2MultipleWidget,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for colour in Colour.objects.all().order_by("display_order"):
            self.fields["colour_" + colour.symbol.lower()] = forms.BooleanField(
                required=False
            )
            self.fields["colourid_" + colour.symbol.lower()] = forms.BooleanField(
                required=False
            )

        for rarity in Rarity.objects.all().order_by("display_order"):
            self.fields["rarity_" + rarity.symbol.lower()] = forms.BooleanField(
                required=False
            )

    def colour_fields(self) -> dict:
        """
        Gets all the colour fields
        :return:
        """
        return {
            colour.symbol.lower(): self["colour_" + colour.symbol.lower()]
            for colour in Colour.objects.all().order_by("display_order")
        }

    def colourid_fields(self) -> dict:
        """
        Gets all the colour identity fields
        :return: A dictionary of fields
        """
        return {
            colour.symbol.lower(): self["colourid_" + colour.symbol.lower()]
            for colour in Colour.objects.all().order_by("display_order")
        }

    def is_colour_enabled(self) -> bool:
        """
        Gets whether any colour fields are  currently enabled
        :return: True if any colour fields are enabled ,otherwise False
        """
        return any(field.data for symbol, field in self.colour_fields().items())

    def is_colourid_enabled(self) -> bool:
        """
        Gets whether any colour identity fields are currently enabled
        :return: TTrue if any colour identity fields are enabled, otherwise Talse
        """
        return any(field.data for symbol, field in self.colourid_fields().items())

    def rarity_fields(self) -> dict:
        """
        Gets a dictionary of the rarity fields
        :return:
        """
        return {
            r.symbol.lower(): self["rarity_" + r.symbol.lower()]
            for r in Rarity.objects.all().order_by("display_order")
        }

    def is_rarity_enabled(self) -> bool:
        """
        Gets whether any rarity fields are currently enabled
        :return: True if any rarity fields are set, otherwise False
        """
        return any(field.data for key, field in self.rarity_fields().items())

    def get_field_search(self) -> FieldSearch:
        """
        Generates a search object using the contents of this form
        :return: A populated FieldSearch
        """
        self.full_clean()

        search = FieldSearch()
        search.card_name = self.data.get("card_name")
        search.rules_text = self.data.get("rules_text")
        search.flavour_text = self.data.get("flavour_text")
        search.type_text = self.data.get("type_text")
        search.subtype_text = self.data.get("subtype_text")
        search.mana_cost = self.data.get("mana_cost_text")

        search.min_cmc = self.cleaned_data.get("min_cmc")
        search.max_cmc = self.cleaned_data.get("max_cmc")
        search.min_power = self.cleaned_data.get("min_power")
        search.max_power = self.cleaned_data.get("max_power")
        search.min_toughness = self.cleaned_data.get("min_toughness")
        search.max_toughness = self.cleaned_data.get("max_toughness")

        for colour in Colour.objects.all():
            if self.data.get("colour_" + colour.symbol.lower()):
                search.colours.append(colour.bit_value)

            if self.data.get("colourid_" + colour.symbol.lower()):
                search.colour_identities.append(colour.bit_value)

        search.exclude_unselected_colours = bool(self.data.get("exclude_colours"))
        search.match_colours_exactly = bool(self.data.get("match_colours"))
        search.exclude_unselected_colour_identities = bool(
            self.data.get("exclude_colourids")
        )
        search.match_colour_identities_exactly = bool(self.data.get("match_colourids"))

        for rarity in Rarity.objects.all():
            if self.data.get("rarity_" + rarity.symbol.lower()):
                search.rarities.append(rarity)

        search.match_rarities_exactly = bool(self.data.get("match_rarity"))

        search.match_sets_exactly = bool(self.cleaned_data.get("match_sets"))
        search.sets = self.cleaned_data.get("sets")

        search.build_parameters()
        search.search(self.get_page_number())
        return search


class DeckForm(forms.ModelForm):
    """
    Form for creating or updating a deck plus all of its cards
    """

    cards = forms.ModelMultipleChoiceField(
        queryset=Card.objects.all().order_by("name"),
        widget=Select2MultipleWidget,
        required=False,
    )
    quantity = forms.IntegerField(
        validators=[MinValueValidator(1)], required=False, min_value=1
    )

    main_board = forms.CharField(widget=forms.widgets.Textarea(), required=False)
    side_board = forms.CharField(widget=forms.widgets.Textarea(), required=False)
    maybe_board = forms.CharField(widget=forms.widgets.Textarea(), required=False)
    acquire_board = forms.CharField(widget=forms.widgets.Textarea(), required=False)

    card_board = forms.ChoiceField(choices=DeckCard.BOARD_CHOICES)

    skip_validation = forms.BooleanField(required=False)

    class Meta:
        model = Deck

        widgets = {"exclude_colours": Select2MultipleWidget}
        fields = [
            "date_created",
            "name",
            "subtitle",
            "format",
            "description",
            "exclude_colours",
        ]

    def clean(self) -> dict:
        """
        Validates the content of this form
        :return: The cleaned data
        """
        form_data = super().clean()
        self.get_cards()
        for exclude_colour in form_data["exclude_colours"]:
            self.instance.exclude_colours.add(exclude_colour)
        return form_data

    def get_boards(self) -> Dict[str, str]:
        """
        Gets the boards and their cleaned data
        :return: The board keys to their text values
        """
        return {
            "main": self.cleaned_data.get("main_board"),
            "side": self.cleaned_data.get("side_board"),
            "maybe": self.cleaned_data.get("maybe_board"),
            "acquire": self.cleaned_data.get("acquire_board"),
        }

    def populate_boards(self) -> None:
        """
        Populates the text values of all teh boards
        """
        self.fields["main_board"].initial = ""
        for group_name, cards in self.instance.get_card_groups().items():
            if not cards:
                continue
            self.fields["main_board"].initial += group_name + "\n"
            self.fields["main_board"].initial += (
                "\n".join(card.as_deck_text() for card in cards) + "\n\n"
            )

        for board_key in ["side", "maybe", "acquire"]:
            board_cards = self.instance.cards.filter(board=board_key).order_by(
                "card__name"
            )
            self.fields[board_key + "_board"].initial = "\n".join(
                card.as_deck_text() for card in board_cards
            )

    def get_cards(self) -> List[DeckCard]:
        """
        Gets the cards from all the boards in the deck.
        :return: The list of DeckCards as long as they are all valid
        :raises: ValidationError if ANY of the cards are invalid (wrong number, wrong name etc.)
        """
        deck_cards = []
        validation_errors = []
        for board_key, board in self.get_boards().items():
            for line in board.split("\n"):
                try:
                    parts = self.parse_card_text(line)
                    if parts is None:
                        continue
                    count, card_name, options = parts
                    deck_card = self.card_from_text(
                        count, card_name, board_key, options
                    )
                    if not deck_card:
                        continue
                    # If the card already exists in this board...
                    existing_card = next(
                        (
                            dc
                            for dc in deck_cards
                            if dc.card == deck_card.card and dc.board == board_key
                        ),
                        None,
                    )
                    # ... then just add to the existing count
                    if existing_card:
                        existing_card.count += deck_card.count
                    else:
                        deck_cards.append(deck_card)
                except ValidationError as error:
                    validation_errors.append(error)

        if validation_errors:
            raise ValidationError(validation_errors)

        return deck_cards

    # pylint: disable=no-self-use
    def parse_card_text(self, text: str) -> (int, str, dict):
        """
        Parses the text of a card row and returns the count, name and other options of the card
        :param text: The line of deck text for the card
        :return: If the text is valid, then a tuple containing the count, name and options
                 for hte card, otherwise None
        """
        if text is None or text.strip() == "":
            return None

        text = text.strip().replace("’", "'").replace("Æ", "Ae")
        if re.match(r"^\d+$", text):
            return None

        # Note that this regex won't work for cards that start with numbers
        # Fortunately the only card like that is "1998 World Champion"
        matches = re.match(
            r"((?P<count>\d+)\s*x?)? *(?P<name>.+?)(?P<cmdr> ?\*cmdr\*)?$",
            text,
            re.IGNORECASE,
        )

        if not matches:
            raise ValidationError(f"Invalid card {text}")

        card_name = matches["name"].strip()

        if matches["count"] is None:
            count = 1
        else:
            try:
                count = int(matches["count"])
            except (TypeError, ValueError):
                raise ValidationError(
                    f"Invalid count '{matches['count']}'' for {card_name}"
                )

        if count == 0:
            return None

        return count, card_name, {"is_commander": bool(matches["cmdr"])}

    def card_from_text(
        self, count: int, card_name: str, board: str, options: Dict
    ) -> Optional[DeckCard]:
        """
        Parses a single line of text and returns the DeckCard for it
        :param count: The card count
        :param card_name: The name of the card
        :param board: The board that the card belongs to
        :param options: A dict of additional configuration for the card, (e.g. is_commander: bool)
        :return: A DeckCard object if it is valid
        :raises: ValidationError if the card could not be parsed for some reason
        """

        if card_name.lower() in (
            "creatures",
            "creature",
            "artifacts",
            "artifact",
            "land",
            "lands",
            "basic land",
            "non-basic land",
            "nonbasic land",
            "planeswalker",
            "planeswalkers",
            "instant",
            "instants",
            "sorcery",
            "sorceries",
            "general",
            "commander",
            "x",
            "enchantment",
            "enchantments",
        ):
            return None

        # If they enter a card name like "Fire // Ice", then use Fire (a DeckCard is tied to a
        # single Card object, so the first half of split/flip/transform cards should be used
        if "//" in card_name:
            names = card_name.split("/")
            card_name = names[0].strip()

        try:
            # We have to ignore tokens, as otherwise Earthshaker Khenra would return two results
            # But you shouldn't be putting tokens in a deck anyway
            card = Card.objects.get(name__iexact=card_name, is_token=False)
        except Card.DoesNotExist:
            stripped_name = re.sub(r"\W", "", card_name)
            card_matches = Card.objects.annotate(
                short_name=Func(
                    F("name"),
                    Value(r"\W"),
                    Value(""),
                    Value("g"),
                    function="regexp_replace",
                )
            ).filter(is_token=False, short_name__icontains=stripped_name)
            if card_matches.count() == 1:
                card = card_matches.first()
            else:
                raise ValidationError(f'Unknown card "{card_name}"')

        if card.layout in ("scheme", "planer", "vanguard", "emblem"):
            raise ValidationError(f"You can't out {card.name} in a deck")

        # Two-sided cards should always be stored as the front-facing card
        # This even includes cards like Fire // Ice (which will be stored as Fire)
        # However the DeckCard will be displayed as "Fire // Ice"
        if card.layout in ("flip", "split", "transform") and card.side == "b":
            card = card.links.get(side="a")

        # Related to the above rule, it doesn't make sense to put a back half of a meld card in
        if card.layout == "meld" and card.side == "c":
            raise ValidationError(
                f"Reverse side meld cards like {card.name} are not allowed"
            )

        deck_card = DeckCard(card=card, count=count, board=board, deck=self.instance)
        if options["is_commander"]:
            deck_card.is_commander = True

        return deck_card
