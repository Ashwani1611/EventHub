"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""
# config/asgi.py

"""
ASGI config for config project.
"""
"""
ASGI config for config project.
"""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()  # initialize before importing anything model-related

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from notifications.routing import websocket_urlpatterns as notification_patterns
from events.routing import websocket_urlpatterns as events_patterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(notification_patterns + events_patterns)
    ),
})