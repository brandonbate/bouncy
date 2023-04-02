"""
ASGI config for supertictactoe project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, ChannelNameRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from super_bouncy.routing import websocket_urlpatterns


from bouncy.consumers import PrintConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'super_bouncy.settings')

django_asgi_app = get_asgi_application()

import super_bouncy.routing

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
        #"channel": ChannelNameRouter({"testing-print": PrintConsumer})
    }
)
