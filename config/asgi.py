"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""
# config/asgi.py

import os

# ── MUST be first, before any Django/Channels imports ──────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

from notifications.routing import websocket_urlpatterns as notification_patterns
from events.routing import websocket_urlpatterns as events_patterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(                        # ← plain URLRouter, no AuthMiddlewareStack
        notification_patterns + events_patterns    # notifications WS + events WS
    ),
})