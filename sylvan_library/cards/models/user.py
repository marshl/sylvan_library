from django.contrib.auth import get_user_model
from django.db import models


class UserProps(models.Model):
    """
    Additional properties for the Django User model
    """

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    unused_cards_seed = models.IntegerField(default=0)

    @staticmethod
    def add_to_user(user: get_user_model()) -> "UserProps":
        """
        Adds a new UserProps instance to the given user
        (user.userpops existence should be checked every time a value from it is used,
        and this function should be called it if doesn't exist)
        :param user: The user to add the props to
        """
        props = UserProps(user=user)
        props.full_clean()
        props.save()
        return props
