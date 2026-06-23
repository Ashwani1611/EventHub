from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ATTENDEE = 'attendee', 'Attendee'
    ORGANIZER = 'organizer', 'Organizer'
    ADMIN = 'admin', 'Admin'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDEE
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"