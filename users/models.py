from django.db import models
from django.contrib.auth.models import AbstractUser
from .choices import Tier
# Create your models here.


class User(AbstractUser):

    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)
    tier = models.CharField(
        max_length=10, choices=Tier.choices, default=Tier.FREE)
