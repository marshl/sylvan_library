"""
Card language models
"""

from django.db import models


class Language(models.Model):
    """
    Model for a language that a card could be printed in
    """

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, null=True, blank=True)

    ENGLISH = None

    def __str__(self):
        return self.name

    @staticmethod
    def english() -> "Language":
        """
        Gets the cached english language object (English is the default language, and it used
        quite a lot, so this reduces the number of queries made quite a bit)
        :return:
        """
        if not Language.ENGLISH:
            Language.ENGLISH = Language.objects.get(name="English")

        return Language.ENGLISH
