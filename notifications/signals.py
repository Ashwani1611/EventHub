import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .tasks import send_notification_task
from .models import Notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender="events.Booking")
def on_booking_created(sender, instance, created, **kwargs):
    """Fires when a Booking is saved for the first time."""
    if not created:
        return

    user = instance.user

    # In-app notification
    send_notification_task.delay(
        user_id=user.id,
        notification_type=Notification.NotificationType.BOOKING_CONFIRMED,
        title="Booking Confirmed",
        message=f"Your booking for '{instance.event.title}' has been confirmed.",
        channel="in_app",
    )

    # Email notification
    send_notification_task.delay(
        user_id=user.id,
        notification_type=Notification.NotificationType.BOOKING_CONFIRMED,
        title="Booking Confirmed",
        message=f"Your booking for '{instance.event.title}' has been confirmed.",
        channel="email",
    )

    logger.info(f"Booking created signal fired for user={user.email}")


@receiver(post_save, sender="events.Booking")
def on_booking_cancelled(sender, instance, created, **kwargs):
    """Fires when an existing Booking is updated to cancelled status."""
    if created:
        return

    if not hasattr(instance, '_status_changed_to_cancelled'):
        return

    user = instance.user

    send_notification_task.delay(
        user_id=user.id,
        notification_type=Notification.NotificationType.BOOKING_CANCELLED,
        title="Booking Cancelled",
        message=f"Your booking for '{instance.event.title}' has been cancelled.",
        channel="in_app",
    )

    logger.info(f"Booking cancelled signal fired for user={user.email}")