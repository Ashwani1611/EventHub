import logging
from abc import ABC, abstractmethod

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification

logger = logging.getLogger(__name__)


class BaseNotificationChannel(ABC):
    """All channels must implement send()."""

    @abstractmethod
    def send(self, recipient, notification_type, title, message) -> Notification:
        raise NotImplementedError


class EmailChannel(BaseNotificationChannel):

    def send(self, recipient, notification_type, title, message) -> Notification:
        # Save record to DB
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            channel=Notification.Channel.EMAIL,
            title=title,
            message=message,
        )

        # TODO: plug in SendGrid / SES here later
        logger.info(f"[EMAIL] To: {recipient.email} | Subject: {title}")

        return notification


class SMSChannel(BaseNotificationChannel):

    def send(self, recipient, notification_type, title, message) -> Notification:
        # Save record to DB
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            channel=Notification.Channel.SMS,
            title=title,
            message=message,
        )

        # TODO: plug in Twilio / AWS SNS here later
        logger.info(f"[SMS] To: {recipient.phone_number} | Message: {message}")

        return notification


class InAppChannel(BaseNotificationChannel):

    def send(self, recipient, notification_type, title, message) -> Notification:
        # Save record to DB
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            channel=Notification.Channel.IN_APP,
            title=title,
            message=message,
        )

        # Push to WebSocket group for this user
        channel_layer = get_channel_layer()
        group_name = f"notifications_{recipient.id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notify",           # maps to `notify()` method in the consumer
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "notification_id": notification.id,
            }
        )

        logger.info(f"[IN_APP] To: {recipient.email} | Title: {title}")

        return notification

class WhatsAppChannel(BaseNotificationChannel):

    def send(self, recipient, notification_type, title, message) -> Notification:
        # Save record to DB
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            channel=Notification.Channel.WHATSAPP,
            title=title,
            message=message,
        )

        # TODO: plug in Meta Cloud API here later
        # Endpoint: https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages
        # Auth: Bearer WHATSAPP_ACCESS_TOKEN
        logger.info(f"[WHATSAPP] To: {recipient.phone_number} | Message: {message}")

        return notification