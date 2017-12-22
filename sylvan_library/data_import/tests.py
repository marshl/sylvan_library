from django.test import TestCase
from data_import.staging import *


class StagedCardTestCase(TestCase):
    def test_get_type(self):
        staged_card = StagedCard({'types': ['Legendary', 'Creature']})
        self.assertEqual(staged_card.get_types(), 'Legendary Creature')

    def test_is_reserved(self):
        staged_card = StagedCard({'reserved': True})
        self.assertTrue(staged_card.is_reserved())
