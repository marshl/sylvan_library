from django.db import migrations

# From 16 May to 29 Aug 2022 the price data had inflated non-foil prices for tens of
# thousands of printings, which look like foil prices given as non-foil ones
SPIKE_START = "2022-05-16"
SPIKE_END = "2022-08-29"
# How far either side of the spike to look for a normal price to draw a line from
EDGE_SEARCH = "8 weeks"

# Printings that have no non-foil price at any other time (mostly foil-only promos and
# masterpieces) only had foil prices, so their non-foil prices in the spike are removed
CLEAR_FOIL_ONLY_PRINTINGS = """
UPDATE cards_cardprice price
SET paper_value = NULL
WHERE price.date BETWEEN %(start)s AND %(end)s
AND price.paper_value IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM cards_cardprice other
    WHERE other.card_printing_id = price.card_printing_id
    AND other.paper_value IS NOT NULL
    AND other.date NOT BETWEEN %(start)s AND %(end)s
)
"""

# A printing was affected if every non-foil price in the spike is higher than the
# prices either side of it. Those prices are replaced with a straight line between the
# prices either side.
DRAW_LINE_ACROSS_SPIKE = """
WITH edges AS (
    SELECT printing.card_printing_id,
        before.date AS before_date, before.paper_value AS before_value,
        after.date AS after_date, after.paper_value AS after_value
    FROM (
        SELECT DISTINCT card_printing_id FROM cards_cardprice
        WHERE date BETWEEN %(start)s AND %(end)s AND paper_value IS NOT NULL
    ) printing
    CROSS JOIN LATERAL (
        SELECT date, paper_value FROM cards_cardprice
        WHERE card_printing_id = printing.card_printing_id
        AND paper_value IS NOT NULL
        AND date < %(start)s
        AND date >= %(start)s::date - %(edge_search)s::interval
        ORDER BY date DESC LIMIT 1
    ) before
    CROSS JOIN LATERAL (
        SELECT date, paper_value FROM cards_cardprice
        WHERE card_printing_id = printing.card_printing_id
        AND paper_value IS NOT NULL
        AND date > %(end)s
        AND date <= %(end)s::date + %(edge_search)s::interval
        ORDER BY date LIMIT 1
    ) after
),
affected AS (
    SELECT * FROM edges
    WHERE NOT EXISTS (
        SELECT 1 FROM cards_cardprice price
        WHERE price.card_printing_id = edges.card_printing_id
        AND price.date BETWEEN %(start)s AND %(end)s
        AND price.paper_value <= GREATEST(edges.before_value, edges.after_value)
    )
)
UPDATE cards_cardprice price
SET paper_value = ROUND(
    affected.before_value
    + (affected.after_value - affected.before_value)
    * (price.date - affected.before_date)
    / (affected.after_date - affected.before_date),
    2
)
FROM affected
WHERE price.card_printing_id = affected.card_printing_id
AND price.date BETWEEN %(start)s AND %(end)s
AND price.paper_value IS NOT NULL
"""


def smooth_price_spike(apps, schema_editor):
    """
    Removes the 2022 non-foil price spike. The original prices aren't kept, so this
    can't be undone.
    """
    params = {"start": SPIKE_START, "end": SPIKE_END, "edge_search": EDGE_SEARCH}
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(DRAW_LINE_ACROSS_SPIKE, params)
        cursor.execute(CLEAR_FOIL_ONLY_PRINTINGS, params)


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0010_cardimage_forward_slash_paths"),
    ]

    operations = [
        migrations.RunPython(smooth_price_spike, migrations.RunPython.noop),
    ]
