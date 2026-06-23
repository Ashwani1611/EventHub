import logging
from celery import shared_task
from django.contrib.auth import get_user_model

from .factory import NotificationChannelFactory

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, user_id, notification_type, title, message, channel):
    """
    Asynchronous task to send a notification via the specified channel.

    Retries up to 3 times with a 60 second delay if anything fails.
    """
    try:
        user = User.objects.get(id=user_id)
        channel_instance = NotificationChannelFactory.get_channel(channel)
        channel_instance.send(
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
        )
        logger.info(
            f"Notification sent | user={user.email} | "
            f"type={notification_type} | channel={channel}"
        )

    except User.DoesNotExist:
        # Don't retry if user doesn't exist — it's a permanent failure
        logger.error(f"User with id={user_id} not found. Notification dropped.")

    except Exception as exc:
        logger.error(
            f"Notification failed | user_id={user_id} | "
            f"channel={channel} | error={exc}"
        )
        raise self.retry(exc=exc)