from django.db import models
from django.conf import settings


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        BOOKING_CONFIRMED   = "booking_confirmed",  "Booking Confirmed"
        BOOKING_CANCELLED   = "booking_cancelled",  "Booking Cancelled"
        PAYMENT_SUCCESS     = "payment_success",    "Payment Successful"
        PAYMENT_FAILED      = "payment_failed",     "Payment Failed"
        EVENT_UPDATED       = "event_updated",      "Event Updated"
        EVENT_CANCELLED     = "event_cancelled",    "Event Cancelled"
        GENERAL             = "general",            "General"

    class Channel(models.TextChoices):
        EMAIL   = "email",  "Email"
        IN_APP  = "in_app", "In-App"
        SMS     = "sms",    "SMS"
        WHATSAPP  = "whatsapp",  "WhatsApp"

    recipient           = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name="notifications"
                          )
    notification_type   = models.CharField(max_length=30, choices=NotificationType.choices)
    channel             = models.CharField(max_length=10, choices=Channel.choices)
    title               = models.CharField(max_length=255)
    message             = models.TextField()
    is_read             = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.notification_type} → {self.recipient.email}"