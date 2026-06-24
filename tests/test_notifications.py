# tests/test_notifications.py

import pytest
from notifications.models import Notification
from notifications.factory import NotificationChannelFactory


@pytest.mark.django_db
def test_factory_resolves_all_channels():
    for channel in ["email", "sms", "in_app", "whatsapp"]:
        instance = NotificationChannelFactory.get_channel(channel)
        assert instance is not None


@pytest.mark.django_db
def test_factory_raises_on_unknown_channel():
    with pytest.raises(ValueError):
        NotificationChannelFactory.get_channel("telegram")


@pytest.mark.django_db
def test_in_app_channel_creates_notification(user):
    channel = NotificationChannelFactory.get_channel("in_app")

    # Patch group_send so we don't need a real Redis channel layer in tests
    from unittest.mock import patch
    with patch("notifications.strategies.async_to_sync") as mock:
        mock.return_value = lambda *args, **kwargs: None
        notification = channel.send(
            recipient=user,
            notification_type=Notification.NotificationType.GENERAL,
            title="Test",
            message="Test message",
        )

    assert notification.id is not None
    assert notification.recipient == user
    assert notification.channel == Notification.Channel.IN_APP