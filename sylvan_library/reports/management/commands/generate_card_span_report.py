"""
Module for the generate_deck_colour_report command
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    The command for generating the deck colour report
    """


"""
WITH card_and_date AS (
	SELECT cards_cardprinting.card_id, cards_card.name, cards_set.release_date, cards_set.name AS set_name
	FROM cards_cardprinting			   
	JOIN cards_set
	ON cards_set.id = cards_cardprinting.set_id
	JOIN cards_card
	ON cards_card.id = cards_cardprinting.card_id
	WHERE cards_set.type NOT IN ('promo', 'draft_innovation', 'masters', 'box', 'starter')
	AND cards_set.release_date IS NOT NULL
	AND cards_cardprinting.is_online_only = false
	--AND (cards_set.type = 'expansion' OR cards_set.type = 'core')
),
date_spans AS (
	SELECT card_id, name, set_name, release_date AS start_date,
	LEAD (release_date, 1)
	OVER (
		PARTITION BY card_id    
		ORDER BY release_date
	) AS end_date
	FROM card_and_date
)
SELECT card_id, name, set_name, start_date, end_date, (end_date - start_date) AS span
FROM date_spans
WHERE end_date IS NOT NULL
ORDER BY (end_date - start_date) DESC
LIMIT 100
"""
