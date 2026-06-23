import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            # Reject unauthenticated connections
            await self.close()
            return

        # Each user gets their own group
        self.group_name = f"notifications_{user.id}"

        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected | user={user.email}")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected | group={self.group_name}")

    async def receive(self, text_data):
        """
        Handle messages sent from the frontend over WebSocket.
        For now we just acknowledge — frontend will mostly just listen.
        """
        data = json.loads(text_data)
        logger.info(f"WebSocket message received: {data}")

    async def notify(self, event):
        """
        Called by channel layer when InAppChannel does group_send().
        The 'type': 'notify' in group_send maps to this method.
        """
        await self.send(text_data=json.dumps({
            "notification_id":   event["notification_id"],
            "notification_type": event["notification_type"],
            "title":             event["title"],
            "message":           event["message"],
        }))