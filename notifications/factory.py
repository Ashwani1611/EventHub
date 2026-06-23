from .strategies import (
    EmailChannel,
    InAppChannel,
    SMSChannel,
    WhatsAppChannel,
)


class NotificationChannelFactory:

    _channels = {
        "email":     EmailChannel,
        "in_app":    InAppChannel,
        "sms":       SMSChannel,
        "whatsapp":  WhatsAppChannel,
    }

    @classmethod
    def get_channel(cls, channel: str):
        channel_class = cls._channels.get(channel)

        if channel_class is None:
            raise ValueError(
                f"Unknown notification channel: '{channel}'. "
                f"Available channels: {list(cls._channels.keys())}"
            )

        return channel_class()
    