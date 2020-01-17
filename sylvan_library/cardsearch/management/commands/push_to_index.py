import logging

from django.core.management.base import BaseCommand
from cards.models import Card

from elasticsearch_dsl import Document, Text, Float
from elasticsearch import Elasticsearch


class CardDocument(Document):
    name = Text()
    power = Float()
    toughness = Float()
    rules_text = Text()

    class Index:
        name = "cards-index"


class Command(BaseCommand):

    help = ()

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # CardDocument.init()
        # es = Elasticsearch()
        # bulk(
        #     client=es,
        #     actions=(self.index_card(c) for c in Card.objects.all().iterator()),
        # )
        es = Elasticsearch()
        # res = es.search(
        #     index=CardDocument.Index.name, body={"query": {"match": {"power": 5}}}
        # )
        res = es.search(
            index=CardDocument.Index.name,
            body={
                "query": {
                    "query_string": {
                        "query": "power:>=10 toughness:<=3",
                        "default_field": "name",
                        "default_operator": "AND",
                    }
                }
            },
            scroll="10m",
        )
        while res.get("hits", {}).get("hits"):

            if res.get("hits") and res["hits"].get("total").get("value"):
                print(f"Total: {res['hits']['total']}")
                for hit in res.get("hits").get("hits"):
                    print(hit)

            scroll_id = res["_scroll_id"]
            res = es.scroll(scroll="10m", scroll_id=scroll_id)
            pass

    def index_card(self, card: Card):
        doc = CardDocument(meta={"id": card.id})
        doc.name = card.name

        if card.num_power == float("inf"):
            doc.power = 2 ** 127
        else:
            doc.power = card.num_power
        if card.num_toughness == float("inf"):
            doc.toughness = 2 ** 127
        else:
            doc.toughness = card.num_toughness

        doc.rules_text = card.rules_text
        doc.save()
        return doc.to_dict(include_meta=True)
