"""
Forms for the website module
"""
import re
from typing import Dict, Optional, List, Tuple, Any

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Func, Value, F
from django_select2.forms import Select2MultipleWidget
from tinymce.widgets import TinyMCE

from cards.models import Card, CardPrinting, Deck, DeckCard, Language
from cardsearch.parse_search import ParseSearch


class ChangeCardOwnershipForm(forms.Form):
    """
    A for mfor changing the number of cards that a user owns
    """

    count = forms.IntegerField()
    localisation = forms.ChoiceField(widget=forms.Select)

    def __init__(self, printing: CardPrinting):
        super().__init__()
        # Put the english print first as that is the most likely one that the user will add
        english_localisation = next(
            (
                localisation
                for localisation in printing.localisations.all()
                if localisation.language_id == Language.english().id
            )
        )
        if english_localisation:
            choices = [(english_localisation.id, str(english_localisation))]
        else:
            choices = []
        choices.extend(
            [
                (localisation.id, str(localisation))
                for localisation in printing.localisations.all()
                if localisation.language_id != Language.english().id
            ]
        )
        self.fields["localisation"].choices = choices


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


class QuerySearchForm(SearchForm):
    """
    The search form for searching by a query string
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = None

    query_string = forms.CharField(required=False)

    def get_search(self) -> ParseSearch:
        """
        Gets the search object using the data from this form
        :return:
        """
        self.full_clean()

        search = ParseSearch(self.user)
        search.query_string = self.data.get("query_string")
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

        widgets = {
            "exclude_colours": Select2MultipleWidget,
            "description": TinyMCE(),
        }
        fields = [
            "date_created",
            "name",
            "subtitle",
            "format",
            "exclude_colours",
            "description",
            "is_prototype",
            "is_private",
        ]

    def clean(self) -> Dict[str, Any]:
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
        Populates the text values of all the boards
        """
        self.fields["main_board"].initial = ""
        for card_group in self.instance.get_card_groups():
            if not card_group["cards"]:
                continue

            self.fields["main_board"].initial += card_group["name"] + "\n"
            self.fields["main_board"].initial += (
                "\n".join(card.as_deck_text() for card in card_group["cards"]) + "\n\n"
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
        deck_cards: List[DeckCard] = []
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
    def parse_card_text(self, text: str) -> Optional[Tuple[int, str, dict]]:
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
        self, count: int, card_name: str, board: str, options: Dict[str, Any]
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
            "other spells",
            "instants and sorc.",
        ):
            return None

        try:
            # We have to ignore tokens, as otherwise Earthshaker Khenra would return two results
            # But you shouldn't be putting tokens in a deck anyway
            card = Card.objects.get(name__iexact=card_name, is_token=False)
        except Card.DoesNotExist as ex:
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
                raise ValidationError(f'Unknown card "{card_name}"') from ex

        if card.layout in ("scheme", "planar", "vanguard", "emblem"):
            raise ValidationError(
                f'You can\'t put the {card.layout} card "{card.name}" in a deck'
            )

        # Two-sided cards should always be stored as the front-facing card
        # This even includes cards like Fire // Ice (which will be stored as Fire)
        # However the DeckCard will be displayed as "Fire // Ice"
        # if card.layout in ("flip", "split", "transform") and card.side == "b":
        #     card = card.links.get(side="a")

        # Related to the above rule, it doesn't make sense to put a back half of a meld card in
        if card.layout == "meld" and card.side == "c":
            raise ValidationError(
                f"Reverse side meld cards like {card.name} are not allowed"
            )

        deck_card = DeckCard(card=card, count=count, board=board, deck=self.instance)
        if options["is_commander"]:
            deck_card.is_commander = True

        return deck_card
