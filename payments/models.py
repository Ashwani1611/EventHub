from django.db import models
from django.conf import settings

from events.models import Booking


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"      # Razorpay order created, awaiting checkout
        PAID = "PAID", "Paid"                # Payment captured + signature verified
        FAILED = "FAILED", "Failed"          # Checkout failed or signature mismatch
        REFUNDED = "REFUNDED", "Refunded"

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment #{self.id} — Booking #{self.booking_id} [{self.status}]"


class WebhookEvent(models.Model):
    """
    Records every Razorpay webhook event ID we've already processed.
    Razorpay can (and does) deliver the same webhook more than once —
    this table is the idempotency guard so we never double-process
    a payment.captured / payment.failed event.
    """
    event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} — {self.event_id}"