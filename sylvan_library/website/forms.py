"""
Forms for the website module
"""

from typing import Dict, List, Tuple, Any

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django_select2.forms import Select2MultipleWidget
from tinymce.widgets import TinyMCE

from sylvan_library.cards.deck_text import get_board_text, get_deck_cards
from sylvan_library.cards.models.card import CardPrinting, Card
from sylvan_library.cards.models.decks import Deck, DeckCard
from sylvan_library.cards.models.language import Language
from sylvan_library.cardsearch.parameters.base_parameters import QueryContext
from sylvan_library.cardsearch.parse_search import ParseSearch

User = get_user_model()


class ChangeCardOwnershipForm(forms.Form):
    """
    A form for changing the number of cards that a user owns
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


class QuerySearchForm(forms.Form):
    """
    The search form for searching by a query string
    """

    query_string = forms.CharField(required=False)

    def get_page_number(self) -> int:
        """
        Gets the current page number of the results
        :return: The current page number if it exists, otherwise the first page
        """
        try:
            return int(self.data.get("page"))
        except (TypeError, ValueError):
            return 1

    def get_search(self, user: User) -> Tuple[ParseSearch, QueryContext]:
        """
        Gets the search object using the data from this form
        :return:
        """
        self.full_clean()

        search = ParseSearch(self.data.get("query_string"), user)
        search.build_parameters()
        query_context = QueryContext(
            user=user,
            search_mode=search.root_parameter.get_default_search_context(),
        )
        search.root_parameter.validate(query_context)
        search.search(query_context, self.get_page_number())
        return search, query_context


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

        widgets = {"exclude_colours": Select2MultipleWidget, "description": TinyMCE()}
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
        for board_key, text in get_board_text(self.instance).items():
            self.fields[board_key + "_board"].initial = text

    def get_cards(self) -> List[DeckCard]:
        """
        Gets the cards from all the boards in the deck.
        :return: The list of DeckCards as long as they are all valid
        :raises: ValidationError if ANY of the cards are invalid (wrong number, wrong name etc.)
        """
        return get_deck_cards(self.get_boards(), self.instance)
