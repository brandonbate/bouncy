from django.urls import re_path

from bouncy import consumers

from channels.routing import ProtocolTypeRouter, ChannelNameRouter, URLRouter

from bouncy.consumers import PrintConsumer

application = ProtocolTypeRouter({
    "channel": ChannelNameRouter({
        "testing-print": PrintConsumer,
    }),
})

websocket_urlpatterns = [
    re_path(r"ws/play/$", consumers.GameConsumer.as_asgi()),
]

