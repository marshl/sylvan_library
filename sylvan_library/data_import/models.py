from django.db import models


class UpdateMode(models.TextChoices):
    UPDATE = "UPDATE", "Update"
    CREATE = "CREATE", "Create"
    DELETE = "DELETE", "Delete"


# class CreateCard(models.Model):
#     # See cards.Card
#     scryfall_oracle_id = models.CharField(max_length=36, unique=True)
#     name = models.CharField(max_length=200)
#
#     field_data = models.JSONField()
#
#     def __str__(self) -> str:
#         return f"{self.name} ({self.scryfall_oracle_id})"

UPDATE_MODE_FIELD = models.CharField(max_length=10, choices=UpdateMode.choices)


class UpdateCard(models.Model):
    update_mode = UPDATE_MODE_FIELD
    scryfall_oracle_id = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=200)
    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.name} ({self.scryfall_oracle_id})"


# class DeleteCard(models.Model):
#     scryfall_oracle_id = models.CharField(max_length=36, unique=True)
#     name = models.CharField(max_length=200)


# class CreateCardFace(models.Model):
#     scryfall_oracle_id = models.CharField(max_length=36)
#     name = models.CharField(max_length=200)
#
#     face_name = models.CharField(max_length=200)
#     side = models.CharField(max_length=1, blank=True, null=True)
#
#     field_data = models.JSONField()
#
#     class Meta:
#         unique_together = (("scryfall_oracle_id", "side"),)


class UpdateCardFace(models.Model):
    update_mode = UPDATE_MODE_FIELD
    scryfall_oracle_id = models.CharField(max_length=36)
    name = models.CharField(max_length=200)

    face_name = models.CharField(max_length=200)
    side = models.CharField(max_length=1, blank=True, null=True)

    field_data = models.JSONField()

    class Meta:
        unique_together = (("scryfall_oracle_id", "side"),)

    def __str__(self) -> str:
        name = f"{self.update_mode} {self.name} ({self.scryfall_oracle_id})"
        if self.side:
            name += f" ({self.face_name} {self.side})"
        return name


class UpdateCardPrinting(models.Model):
    update_mode = UPDATE_MODE_FIELD
    card_scryfall_oracle_id = models.CharField(max_length=36)
    card_name = models.CharField(max_length=200)
    scryfall_id = models.CharField(max_length=36, unique=True)
    set_code = models.CharField(max_length=10)

    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.card_name} in {self.set_code} ({self.scryfall_id})"


class UpdateCardFacePrinting(models.Model):
    update_mode = UPDATE_MODE_FIELD
    scryfall_id = models.CharField(max_length=36)
    scryfall_oracle_id = models.CharField(max_length=36)
    card_name = models.CharField(max_length=200)
    printing_uuid = models.CharField(max_length=36)
    card_face_name = models.CharField(max_length=200)
    side = models.CharField(max_length=1, blank=True, null=True)
    field_data = models.JSONField()

    class Meta:
        unique_together = ("printing_uuid", "side")

    def __str__(self) -> str:
        name = f"{self.update_mode} face printing {self.card_face_name} ({self.printing_uuid})"
        if self.side:
            name += f" ({self.card_face_name} {self.side})"
        return name


class UpdateCardLocalisation(models.Model):
    """
    Class for updating CardLocalisation models
    """

    update_mode = UPDATE_MODE_FIELD
    language_code = models.CharField(max_length=100)
    printing_scryfall_id = models.CharField(max_length=36)
    card_name = models.CharField(max_length=200)

    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} localisation {self.language_code} {self.printing_scryfall_id} ({self.card_name})"

    class Meta:
        unique_together = ("language_code", "printing_scryfall_id")


class UpdateCardFaceLocalisation(models.Model):
    update_mode = UPDATE_MODE_FIELD
    language_code = models.CharField(max_length=100)
    printing_scryfall_id = models.CharField(max_length=36)
    face_name = models.CharField(max_length=200)
    face_printing_uuid = models.CharField(max_length=36)

    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.language_code} face localisation {self.printing_scryfall_id} ({self.face_name})"


# class CreateSet(models.Model):
#     set_code = models.CharField(max_length=20)
#     field_data = models.JSONField()
#
#     def __str__(self) -> str:
#         return f"Create {self.set_code}"


class UpdateSet(models.Model):
    update_mode = UPDATE_MODE_FIELD
    set_code = models.CharField(max_length=20, unique=True)
    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.set_code}"


#
# class DeleteSet(models.Model):
#     set_code = models.CharField(max_length=20)
#
#     def __str__(self) -> str:
#         return f"Delete {self.set_code}"

#
# class CreateBlock(models.Model):
#     name = models.CharField(max_length=100)
#     release_date = models.DateField()
#
#     def __str__(self) -> str:
#         return f"Create {self.name} - {self.release_date}"


class UpdateBlock(models.Model):
    update_mode = UPDATE_MODE_FIELD
    name = models.CharField(max_length=100, unique=True)
    release_date = models.DateField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.name} - {self.release_date}"


class UpdateCardRuling(models.Model):
    update_mode = UPDATE_MODE_FIELD
    card_name = models.CharField(max_length=100)
    scryfall_oracle_id = models.CharField(max_length=36)
    ruling_date = models.DateField()
    ruling_text = models.CharField(max_length=4000)

    def __str__(self) -> str:
        return f"{self.update_mode} {self.card_name}: {self.ruling_text}"

    class Meta:
        unique_together = (("scryfall_oracle_id", "ruling_text"),)


class UpdateCardLegality(models.Model):
    update_mode = UPDATE_MODE_FIELD
    card_name = models.CharField(max_length=100)
    scryfall_oracle_id = models.CharField(max_length=36)
    format_name = models.CharField(max_length=100)
    restriction = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.update_mode} {self.card_name} is {self.restriction} in {self.format_name}"

    class Meta:
        unique_together = (("scryfall_oracle_id", "format_name"),)
        verbose_name_plural = "Update card legalities"
