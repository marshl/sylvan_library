"""
Models for set related objects
"""
from django.db import models


class Block(models.Model):
    """
    Model for a block of sets
    """

    name = models.CharField(max_length=200, unique=True)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name


class Format(models.Model):
    """
    Model for a format of cards
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Set(models.Model):
    """
    Model for a set of cards
    """

    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True)

    block = models.ForeignKey(
        Block, null=True, blank=True, related_name="sets", on_delete=models.CASCADE
    )

    keyrune_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name
