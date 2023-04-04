from django.urls import re_path
from bouncy import consumers

websocket_urlpatterns = [
    re_path(r"ws/bouncy/$", consumers.GameConsumer.as_asgi()),
]

