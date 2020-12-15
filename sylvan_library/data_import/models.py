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


#
#
# class DeleteCardFace(models.Model):
#     scryfall_oracle_id = models.CharField(max_length=36)
#     name = models.CharField(max_length=200)
#
#     face_name = models.CharField(max_length=200)
#     side = models.CharField(max_length=1, blank=True, null=True)
#


# class CreateCardPrinting(models.Model):
#     card_scryfall_oracle_id = models.CharField(max_length=36)
#     name = models.CharField(max_length=200)
#     uuid = models.CharField(max_length=36)
#
#     field_data = models.JSONField()


class UpdateCardPrinting(models.Model):
    update_mode = UPDATE_MODE_FIELD
    card_scryfall_oracle_id = models.CharField(max_length=36)
    card_name = models.CharField(max_length=200)
    uuid = models.CharField(max_length=36, unique=True)
    set_code = models.CharField(max_length=10)

    field_data = models.JSONField()

    def __str__(self) -> str:
        return f"{self.update_mode} {self.card_name} in {self.set_code}({self.uuid})"


# class DeleteCardPrinting(models.Model):
#     card_scryfall_oracle_id = models.CharField(max_length=36)
#     card_name = models.CharField(max_length=200)
#     uuid = models.CharField(max_length=36)


# class CreateCardFacePrinting(models.Model):
#     card_scryfall_oracle_id = models.CharField(max_length=36)
#     card_name = models.CharField(max_length=200)
#     printing_uuid = models.CharField(max_length=36)
#     card_face_name = models.CharField(max_length=200)
#     side = models.CharField(max_length=1, blank=True, null=True)


class UpdateCardFacePrinting(models.Model):
    update_mode = UPDATE_MODE_FIELD
    card_scryfall_oracle_id = models.CharField(max_length=36)
    card_name = models.CharField(max_length=200)
    printing_uuid = models.CharField(max_length=36)
    card_face_name = models.CharField(max_length=200)
    side = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        unique_together = ("printing_uuid", "side")

    def __str__(self) -> str:
        name = f"{self.update_mode} {self.card_name} ({self.printing_uuid})"
        if self.side:
            name += f" ({self.card_face_name} {self.side})"
        return name


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
