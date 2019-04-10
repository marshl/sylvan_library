"""
Forms for the website module
"""

from django import forms
from django_select2.forms import Select2MultipleWidget

from cards.models import CardPrinting, Colour, Language, PhysicalCard, Rarity, Set
from cardsearch.fieldsearch import FieldSearch
from cardsearch.namesearch import NameSearch


def get_physical_card_key_pair(physical_card: PhysicalCard, printing: CardPrinting):
    """
    Gets the ID and display name of th given PhysicalCard for the given CardPrinting
    :param physical_card: The physical card the user can select from
    :param printing: The printing of the physical card
    :return: A tuple of the physical card's ID and a display string
    """
    return physical_card.id, f'{physical_card.get_display_for_adding()} ({printing.number})'


class ChangeCardOwnershipForm(forms.Form):
    """
    A for mfor changing the number of cards that a user owns
    """
    count = forms.IntegerField()
    printed_language = forms.ChoiceField(widget=forms.Select)

    def __init__(self, printing: CardPrinting):
        super().__init__()
        if any(pl for pl in printing.printed_languages.all()
               if pl.language_id == Language.english().id):
            # Put the english print first as that is the most likely one that the user will add
            english_print = next(pl for pl in printing.printed_languages.all()
                                 if pl.language_id == Language.english().id)
            choices = [get_physical_card_key_pair(physical_card, printing)
                       for physical_card in english_print.physical_cards.all()]
            choices.extend([
                get_physical_card_key_pair(physical_card, printing)
                for lang in printing.printed_languages.all()
                for physical_card in lang.physical_cards.all()
                if lang.language_id != Language.english().id
            ])
        else:
            choices = [
                get_physical_card_key_pair(physical_card, printing)
                for lang in printing.printed_languages.all()
                for physical_card in lang.physical_cards.all()
            ]

        self.fields['printed_language'].choices = choices


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
            return int(self.data.get('page'))
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
        search.card_name = self.data.get('card_name')
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

    sets = forms.ModelMultipleChoiceField(queryset=Set.objects.all().order_by('-release_date'),
                                          widget=Select2MultipleWidget, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for colour in Colour.objects.all().order_by('display_order'):
            self.fields['colour_' + colour.symbol.lower()] = forms.BooleanField(required=False)
            self.fields['colourid_' + colour.symbol.lower()] = forms.BooleanField(required=False)

        for rarity in Rarity.objects.all().order_by('display_order'):
            self.fields['rarity_' + rarity.symbol.lower()] = forms.BooleanField(required=False)

    def colour_fields(self) -> dict:
        """
        Gets all the colour fields
        :return:
        """
        return {colour.symbol.lower(): self['colour_' + colour.symbol.lower()]
                for colour in Colour.objects.all().order_by('display_order')}

    def colourid_fields(self) -> dict:
        """
        Gets all the colour identity fields
        :return: A dictionary of fields
        """
        return {colour.symbol.lower(): self['colourid_' + colour.symbol.lower()]
                for colour in Colour.objects.all().order_by('display_order')}

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
        return {r.symbol.lower(): self['rarity_' + r.symbol.lower()]
                for r in Rarity.objects.all().order_by('display_order')}

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
        search.card_name = self.data.get('card_name')
        search.rules_text = self.data.get('rules_text')
        search.flavour_text = self.data.get('flavour_text')
        search.type_text = self.data.get('type_text')
        search.subtype_text = self.data.get('subtype_text')
        search.mana_cost = self.data.get('mana_cost_text')

        search.min_cmc = self.cleaned_data.get('min_cmc')
        search.max_cmc = self.cleaned_data.get('max_cmc')
        search.min_power = self.cleaned_data.get('min_power')
        search.max_power = self.cleaned_data.get('max_power')
        search.min_toughness = self.cleaned_data.get('min_toughness')
        search.max_toughness = self.cleaned_data.get('max_toughness')

        for colour in Colour.objects.all():
            if self.data.get('colour_' + colour.symbol.lower()):
                search.colours.append(colour.bit_value)

            if self.data.get('colourid_' + colour.symbol.lower()):
                search.colour_identities.append(colour.bit_value)

        search.exclude_unselected_colours = bool(self.data.get('exclude_colours'))
        search.match_colours_exactly = bool(self.data.get('match_colours'))
        search.exclude_unselected_colour_identities = bool(self.data.get('exclude_colourids'))
        search.match_colour_identities_exactly = bool(self.data.get('match_colourids'))

        for rarity in Rarity.objects.all():
            if self.data.get('rarity_' + rarity.symbol.lower()):
                search.rarities.append(rarity)

        search.match_rarities_exactly = bool(self.data.get('match_rarity'))

        search.sets = self.data.get('sets')
        if search.sets and not isinstance(search.sets, list):
            search.sets = [search.sets]

        search.build_parameters()
        search.search(self.get_page_number())
        return search
