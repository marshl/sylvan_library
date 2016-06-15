from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Type(models.Model):
    name = models.CharField(max_length = 50, unique = True)
    
class Subtype(models.Model):
    name = models.CharField(max_length = 50, unique = True)

class Block(models.Model):
    name = models.CharField(max_length = 200, unique = True)
    release_date = models.DateField()

class Set(models.Model):
    code = models.CharField(max_length = 10, unique = True)
    release_date = models.DateField(blank = True)
    name = models.CharField(max_length = 200, unique = True)
    
    block = models.ForeignKey('Block', null = True)
    
class Card(models.Model):
    cost = models.CharField(max_length = 50, blank = True)
    cmc = models.IntegerField()
    colour = models.IntegerField()
    colour_identity = models.IntegerField()
    colour_count = models.IntegerField()
    type = models.CharField(max_length = 100, blank = True)
    subtype = models.CharField(max_length = 100, blank = True)
    power = models.CharField(max_length = 20, blank = True)
    num_power = models.IntegerField()
    toughness = models.CharField(max_length = 20, blank = True)
    num_toughness = models.IntegerField()
    loyalty = models.CharField(max_length = 20, blank = True)
    num_loyalty = models.IntegerField()
    rules_text = models.CharField(max_length = 1000, blank = True)
    
class CardPrinting(models.Model):
    
    rarity = models.CharField(max_length = 1)
    flavour_text = models.CharField(max_length = 350)
    artist = models.CharField(max_length = 100)
    collector_number = models.IntegerField(blank = True)
    collector_letter = models.CharField(max_length = 1, blank = True)
    original_text = models.CharField(max_length = 1000, blank = True)
    original_type = models.CharField(max_length = 200, blank = True)
    
    set = models.ForeignKey('Set')
    card = models.ForeignKey('Card')
    
class CardPrintingLanguage(models.Model):
    
    language = models.CharField(max_length = 50)
    card_name = models.CharField(max_length = 200)
    
    card_printing = models.ForeignKey('CardPrinting')
    
class UserOwnedCard(models.Model):
    
    count = models.IntegerField()
    
    card_printing_language = models.ForeignKey('CardPrintingLanguage')
    owner = models.ForeignKey(User)
    
class UserCardChange(models.Model):
    
    difference = models.IntegerField()
    
    card_printing_language = models.ForeignKey('CardPrintingLanguage')
    owner = models.ForeignKey(User)
    
class CardLink(models.Model):
    
    card_from = models.ForeignKey('Card', related_name = 'cardFrom')
    card_to = models.ForeignKey('Card', related_name = 'cardTo')
    
    type = models.CharField(max_length = 1)
    
class CardRuling(models.Model):
    
    date = models.DateField()
    text = models.CharField(max_length = 1000)
    
    card = models.ForeignKey('Card')
    
class CardTag(models.Model):
    
    name = models.CharField(max_length = 200)
    
class CardTagLink(models.Model):
    
    tag = models.ForeignKey('CardTag')
    card = models.ForeignKey('Card')
    
class Deck(models.Model):
    
    date_created = models.DateField()
    last_modiifed = models.DateField()
    
    name = models.CharField(max_length = 200)
    owner = models.ForeignKey(User)
    
class DeckCard(models.Model):
    
    count = models.IntegerField()
    
    card = models.ForeignKey('Card')
    deck = models.ForeignKey('Deck')
    