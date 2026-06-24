import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class SeatMapConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # ── 1. Auth via session (populated by AuthMiddlewareStack) ─────────
        # No token parsing needed. AuthMiddlewareStack in asgi.py reads the
        # Django session cookie and sets scope["user"] automatically.
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            # Must accept before closing — ASGI spec requires it
            await self.accept()
            await self.close(code=4001)
            logger.warning("WebSocket rejected — unauthenticated connection")
            return

        # ── 2. Validate event exists ────────────────────────────────────────
        self.event_id = self.scope["url_route"]["kwargs"]["event_id"]
        event_exists = await self._event_exists(self.event_id)

        if not event_exists:
            await self.accept()
            await self.close(code=4004)
            logger.warning(f"WebSocket rejected — event {self.event_id} not found")
            return

        # ── 3. Join seat-map group ──────────────────────────────────────────
        self.group_name = f"event_{self.event_id}_seats"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WS connected | user={self.user.id} event={self.event_id}")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WS disconnected | group={self.group_name} code={close_code}")

    async def receive(self, text_data):
        # Seat map is server→client only; we don't expect messages from clients.
        # Log and discard safely rather than letting JSONDecodeError crash the consumer.
        try:
            data = json.loads(text_data)
            logger.info(f"WS unexpected client message: {data}")
        except json.JSONDecodeError:
            logger.warning("WS received invalid JSON — ignored")

    async def seat_update(self, event):
        """
        Called by channel layer when broadcast_seat_update() sends
        group_send() with type='seat_update'.
        """
        await self.send(text_data=json.dumps({
            "seat_id": event["seat_id"],
            "status":  event["status"],
        }))

    # ── DB helpers ──────────────────────────────────────────────────────────

    @database_sync_to_async
    def _event_exists(self, event_id):
        from events.models import Event
        try:
            Event.objects.get(id=event_id)
            return True
        except Event.DoesNotExist:
            return False