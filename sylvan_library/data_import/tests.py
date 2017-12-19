from django.test import TestCase
from data_import.staging import *


class StagedCardTestCase(TestCase):
    def test_get_type(self):
        staged_card = StagedCard({'types': ['Legendary', 'Creature']})
        self.assertEqual(staged_card.get_types(), 'Legendary Creature')
