"""
The module for the scry_export command
"""

import logging
import math
import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Min

from cards.models import Block, Card, Set

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for exporting data for use by Scry apps
    """

    help = "Exports user owned cards "

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.user = None
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "username", nargs=1, type=str, help="The user to who owns the cards"
        )
        parser.add_argument(
            "filename", nargs=1, type=str, help="The file to export the data to"
        )

        parser.add_argument(
            "--pretty-print",
            action="store_true",
            dest="pretty_print",
            default=False,
            help="Pretty print the output XML files",
        )

    def handle(self, *args, **options):

        output_directory = options.get("filename")[0]
        username = options.get("username")[0]

        if not os.path.exists(output_directory):
            logger.error("Could not find directory %s", output_directory)
            return

        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("User with name %s could not be found", username)
            return

        pretty_print = options["pretty_print"]

        self.export_oracle(output_directory, pretty_print)
        self.export_setlist(output_directory, pretty_print)

    def export_oracle(self, output_directory: str, pretty_print: bool):
        """
        Exports all oracle cards as an XML file in the given output directory
        Each card also has a list of the sets that it is in and how many of that card the user owns
        :param output_directory: The directory to put the XML file into
        :param pretty_print: Whether the output file should be pretty printed or raw
        """
        response_xml = ET.Element("oracle")
        for card in (
            Card.objects.prefetch_related("printings__set")
            .prefetch_related("printings__rarity")
            .all()
        ):

            card_xml = ET.SubElement(response_xml, "card")
            ET.SubElement(card_xml, "id").text = str(card.id)
            ET.SubElement(card_xml, "n").text = str(card.name)
            ET.SubElement(card_xml, "nc").text = str(card.colour_count)
            ET.SubElement(card_xml, "ci").text = str(card.colour_identity_flags)
            if card.subtype:
                ET.SubElement(card_xml, "st").text = card.subtype
            ET.SubElement(card_xml, "t").text = card.type
            if card.power:
                ET.SubElement(card_xml, "pw").text = card.power
            if card.toughness:
                ET.SubElement(card_xml, "tf").text = card.toughness
            if card.loyalty:
                ET.SubElement(card_xml, "ly").text = card.loyalty
            if card.rules_text:
                ET.SubElement(card_xml, "r").text = card.rules_text
            ET.SubElement(card_xml, "cl").text = str(card.colour_flags)
            if card.cost:
                ET.SubElement(card_xml, "cs").text = card.cost
            ET.SubElement(card_xml, "npw").text = (
                str(card.num_power) if card.num_power != math.inf else "0"
            )
            ET.SubElement(card_xml, "ntf").text = (
                str(card.num_toughness) if card.num_toughness != math.inf else "0"
            )
            ET.SubElement(card_xml, "cmc").text = str(card.cmc)

            card_sets_xml = ET.SubElement(card_xml, "sets")

            for printing in card.printings.all():
                set_element = ET.SubElement(card_sets_xml, "s")
                ET.SubElement(set_element, "cd").text = printing.set.code
                ET.SubElement(set_element, "r").text = printing.rarity.symbol

                ownership_count = printing.get_user_ownership_count(self.user)

                if ownership_count > 0:
                    ET.SubElement(set_element, "c").text = str(ownership_count)

        tree = ET.ElementTree(response_xml)
        if pretty_print:
            self.indent(response_xml)
        tree.write(os.path.join(output_directory, "oracle.xml"))

    def export_setlist(self, output_directory: str, pretty_print: bool):
        """
        Exports all sets as an XML file in the given output directory
        :param output_directory: The directory to put the XML file into
        :param pretty_print: Whether the output file should be pretty printed or raw
        """
        root_node = ET.Element("cardsets")
        for block in Block.objects.annotate(date=Min("sets__release_date")).order_by(
            "date"
        ):
            format_element = ET.SubElement(root_node, "format")
            ET.SubElement(format_element, "name").text = block.name
            for set_obj in block.sets.order_by("-release_date"):
                set_element = ET.SubElement(format_element, "set")
                ET.SubElement(set_element, "code").text = set_obj.code
                ET.SubElement(set_element, "name").text = set_obj.name

        misc_format = ET.SubElement(root_node, "format")
        ET.SubElement(misc_format, "name").text = "Miscellaneous"
        for set_obj in Set.objects.filter(block__isnull=True).order_by("release_date"):
            set_element = ET.SubElement(misc_format, "set")
            ET.SubElement(set_element, "code").text = set_obj.code
            ET.SubElement(set_element, "name").text = set_obj.name

        tree = ET.ElementTree(root_node)
        if pretty_print:
            self.indent(root_node)
        tree.write(os.path.join(output_directory, "setlist.xml"))

    def indent(self, elem: ET.Element, level: int = 0):
        """
        Recursively indents an XML element to be used for pretty printing
        :param elem: The element to indent
        :param level: The number of levels to indent the element
        """
        i = "\n" + level * "  "
        if elem:
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
                # pylint: disable=redefined-argument-from-local
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
