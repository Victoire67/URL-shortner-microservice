from django.db import models


class Tier(models.TextChoices):
    FREE = "FREE", "Free"
    PREMIUM = "PREMIUM", "Premium"
    ADMIN = "ADMIN", "Admin"
