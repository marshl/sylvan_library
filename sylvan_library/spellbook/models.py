from django.db import models
from django.contrib.auth.models import User

class Block(models.Model):
    name = models.CharField(max_length = 200, unique = True)
    release_date = models.DateField()
    
    def __str__(self):
        return self.name

class Set(models.Model):
    code = models.CharField(max_length = 10, unique = True)
    release_date = models.DateField(blank = True, null = True)
    name = models.CharField(max_length = 200, unique = True)
    
    block = models.ForeignKey('Block', null = True)
    
    def __str__(self):
        return self.name
    
class Rarity(models.Model):
    symbol = models.CharField(max_length = 1, unique = True)
    name = models.CharField(max_length = 15, unique = True)
    display_order = models.IntegerField(unique = True)
    
    def __str__(self):
        return self.name

class Card(models.Model):
    
    name = models.CharField(max_length = 200, unique=True)
    cost = models.CharField(max_length = 50, blank = True, null = True)
    cmc = models.IntegerField()
    colour = models.IntegerField()
    colour_identity = models.IntegerField()
    colour_count = models.IntegerField()
    type = models.CharField(max_length = 100, blank = True, null = True)
    subtype = models.CharField(max_length = 100, blank = True, null = True)
    power = models.CharField(max_length = 20, blank = True, null = True)
    num_power = models.FloatField()
    toughness = models.CharField(max_length = 20, blank = True, null = True)
    num_toughness = models.FloatField()
    loyalty = models.CharField(max_length = 20, blank = True, null = True)
    num_loyalty = models.FloatField()
    rules_text = models.CharField(max_length = 1000, blank = True, null = True)
    
    def __str__(self):
        return self.name
    
class CardPrinting(models.Model):
    flavour_text = models.CharField(max_length = 350, blank = True, null = True)
    artist = models.CharField(max_length = 100)
    collector_number = models.IntegerField()
    collector_letter = models.CharField(max_length = 1, blank = True, null = True)
    original_text = models.CharField(max_length = 1000, blank = True, null = True)
    original_type = models.CharField(max_length = 200, blank = True, null = True)
    
    set = models.ForeignKey('Set')
    card = models.ForeignKey('Card')
    rarity = models.ForeignKey('Rarity')
    
    class Meta:
        unique_together = ("set", "card", "collector_number", "collector_letter")
        
    def __str__(self):
        return self.card + ' in ' + self.set.name
    
class CardPrintingLanguage(models.Model):
    
    language = models.CharField(max_length = 50)
    card_name = models.CharField(max_length = 200)
    multiverse_id = models.IntegerField(blank = True, null = True)

    card_printing = models.ForeignKey('CardPrinting')
    
    physical_card = models.ForeignKey('PhysicalCard', blank=True, null=True)
    
    class Meta:
        unique_together = ("language", "card_name", "card_printing")
        
    def __str__(self):
        return self.language + ' ' + self.card_printing
    
class PhysicalCard(models.Model):
    
    layout = models.CharField(max_length=20)
    
    def __str__(self):
        return self.id
    
class UserOwnedCard(models.Model):
    
    count = models.IntegerField()
    
    physical_card = models.ForeignKey('PhysicalCard')
    owner = models.ForeignKey(User)
    
    class Meta:
        unique_together = ("physical_card", "owner")
    
    def __str__(self):
        return self.count + ' of ' + self.physical_card
    
class UserCardChange(models.Model):
    
    date = models.DateTimeField()
    difference = models.IntegerField()
    
    physical_card = models.ForeignKey('PhysicalCard')
    owner = models.ForeignKey(User)
    
    def __str__(self):
        return self.date + ' ' + self.difference + ' ' + self.physical_card
    
class CardRuling(models.Model):
    
    date = models.DateField()
    text = models.CharField(max_length = 4000)
    
    card = models.ForeignKey('Card')
    
    class Meta:
        unique_together = ("date", "text", "card")
        
    def __str__(self):
        return self.text + ' ' + self.card
    
class CardTag(models.Model):
    
    name = models.CharField(max_length = 200)
    
    def __str__(self):
        return self.name
    
class CardTagLink(models.Model):
    
    tag = models.ForeignKey('CardTag')
    card = models.ForeignKey('Card')
    
    def __str__(self):
        return self.tag + ' on ' + self.card
    
class Deck(models.Model):
    
    date_created = models.DateField()
    last_modiifed = models.DateField()
    
    name = models.CharField(max_length = 200)
    owner = models.ForeignKey(User)
    
    def __str__(self):
        return self.name
    
class DeckCard(models.Model):
    
    count = models.IntegerField()
    
    card = models.ForeignKey('Card')
    deck = models.ForeignKey('Deck')
    
    def __str__(self):
        return self.card + ' in ' + self.deck
    