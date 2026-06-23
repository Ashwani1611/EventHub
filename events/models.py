from django.db import models
from django.conf import settings


class Event(models.Model):

    class Status(models.TextChoices):
        DRAFT       = "draft",      "Draft"
        PUBLISHED   = "published",  "Published"
        CANCELLED   = "cancelled",  "Cancelled"

    organizer       = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        related_name="organized_events"
                      )
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)
    venue           = models.CharField(max_length=255)
    date            = models.DateTimeField()
    total_capacity  = models.PositiveIntegerField()
    price           = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(
                        max_length=10,
                        choices=Status.choices,
                        default=Status.DRAFT
                      )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.title} — {self.venue} ({self.date:%Y-%m-%d})"


class Seat(models.Model):

    class Status(models.TextChoices):
        AVAILABLE   = "available",  "Available"
        LOCKED      = "locked",     "Locked"
        BOOKED      = "booked",     "Booked"

    event       = models.ForeignKey(
                    Event,
                    on_delete=models.CASCADE,
                    related_name="seats"
                  )
    row         = models.CharField(max_length=10)
    number      = models.PositiveIntegerField()
    status      = models.CharField(
                    max_length=10,
                    choices=Status.choices,
                    default=Status.AVAILABLE
                  )
    locked_by   = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name="locked_seats"
                  )
    locked_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("event", "row", "number")
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.event.title} — Row {self.row} Seat {self.number} [{self.status}]"


class Booking(models.Model):

    class Status(models.TextChoices):
        PENDING     = "pending",    "Pending"
        CONFIRMED   = "confirmed",  "Confirmed"
        CANCELLED   = "cancelled",  "Cancelled"

    user                = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name="bookings"
                          )
    seat                = models.OneToOneField(
                            Seat,
                            on_delete=models.CASCADE,
                            related_name="booking"
                          )
    status              = models.CharField(
                            max_length=10,
                            choices=Status.choices,
                            default=Status.PENDING
                          )
    payment_reference   = models.CharField(max_length=255, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} — {self.user.email} — {self.seat}"