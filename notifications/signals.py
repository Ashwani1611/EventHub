import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .tasks import send_notification_task
from .models import Notification

logger = logging.getLogger(__name__)


@receiver(pre_save, sender="events.Booking")
def capture_previous_status(sender, instance, **kwargs):
    """
    Stashes the booking's pre-save status on the instance so the
    post_save receiver below can tell whether status actually changed
    (and to what) in this save call.
    """
    if instance.pk:
        try:
            instance._previous_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None  # new booking, nothing to compare


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
        message=f"Your booking for '{instance.seat.event.title}' has been confirmed.",
        channel="in_app",
    )

    # Email notification
    send_notification_task.delay(
        user_id=user.id,
        notification_type=Notification.NotificationType.BOOKING_CONFIRMED,
        title="Booking Confirmed",
        message=f"Your booking for '{instance.seat.event.title}' has been confirmed.",
        channel="email",
    )

    logger.info(f"Booking created signal fired for user={user.email}")


@receiver(post_save, sender="events.Booking")
def on_booking_cancelled(sender, instance, created, **kwargs):
    """Fires when an existing Booking transitions to cancelled status."""
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)

    if previous_status == instance.status:
        return  # status didn't change in this save

    if instance.status != instance.Status.CANCELLED:  # adjust to your actual status enum
        return

    user = instance.user

    send_notification_task.delay(
        user_id=user.id,
        notification_type=Notification.NotificationType.BOOKING_CANCELLED,
        title="Booking Cancelled",
        message=f"Your booking for '{instance.seat.event.title}' has been cancelled.",
        channel="in_app",
    )

    logger.info(f"Booking cancelled signal fired for user={user.email}")