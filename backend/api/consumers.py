"""
WebSocket consumer — MonitorPage'ке real-time детекция маалыматын жиберет.

Байланыш: ws://localhost:8000/ws/monitor/?token=<JWT>
Клиент group "monitor_updates"га кирет жана push маалыматтарды алат.
"""
import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser


MONITOR_GROUP = "monitor_updates"


async def _get_user_from_token(token_str: str):
    try:
        UntypedToken(token_str)
        from rest_framework_simplejwt.backends import TokenBackend
        from django.conf import settings as djsettings
        data = TokenBackend(
            algorithm="HS256",
            signing_key=djsettings.SECRET_KEY,
        ).decode(token_str, verify=True)
        user = await User.objects.aget(id=data["user_id"])
        return user
    except Exception:
        return AnonymousUser()


class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        qs    = parse_qs(self.scope["query_string"].decode())
        token = (qs.get("token") or [""])[0]

        if token:
            user = await _get_user_from_token(token)
            if user and not isinstance(user, AnonymousUser) and user.is_active:
                self.scope["user"] = user

        # Токен жок болсо дагы Monitor окуй алат (public)
        await self.channel_layer.group_add(MONITOR_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(MONITOR_GROUP, self.channel_name)

    # Клиенттен келген маалыматты кабыл алуу (азырча колдонулбайт)
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # group_send аркылуу жиберилген event
    async def detection_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
