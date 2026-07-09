import secrets

from django.conf import settings
from django_redis import get_redis_connection
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed

from apis.authentication.models import DeviceToken

User = get_user_model()


class CustomLoginView(TokenObtainPairView):
    """
    API endpoint สำหรับ login ทั่วไป (มี expiration time)
    Regular login endpoint with token expiration
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return Response(
                {"message": _("อีเมลหรือรหัสผ่านไม่ถูกต้อง")}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class EMQXTokenGenerateView(APIView):
    """
    API endpoint สำหรับขอ EMQX JWT token ที่ไม่มีวันหมดอายุ
    ต้อง login ก่อน (ส่ง Authorization: Bearer <access_token> ใน header)
    จากนั้นระบบจะสร้าง EMQX token จาก user ที่ login อยู่
    
    Generate non-expiring EMQX JWT tokens for the currently authenticated user
    Requires: Authorization: Bearer <access_token> header
    
    Usage:
    POST /api/v1/auth/emqx-token/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        user = request.user
        mqtt_topic = "swd/phangan/#"
        _, token = DeviceToken.generate_token_instance(mqtt_topic, user)

        return Response(
            {
                "mqtt_topic": mqtt_topic,
                "token": str(token),
            },
            status=status.HTTP_200_OK,
        )


class EMQXAuthWebhookView(APIView):
    """
    EMQX Authentication Webhook endpoint
    EMQX broker ยิง request มาเช็คว่า token ถูกต้องหรือไม่ตอน client connect
    
    EMQX ส่ง request ตาม format:
    POST /api/v1/emqx/auth/
    {
        "username": "user@example.com",
        "password": "token_string"  # หรือ clientid
    }
    
    Response ต้องเป็น:
    - 200 OK: authentication สำเร็จ
    - 401 Unauthorized: authentication ล้มเหลว
    """
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """ตรวจสอบ EMQX token"""
        username = request.data.get('username')
        token = request.data.get('password')  # EMQX sends token as password
        print(f"username: {username}, token: {token}")
        if not username or not token:
            return Response(
                {"result": "deny", "message": _("Missing username or token.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        device_token_obj = DeviceToken.objects.filter(token=token).first()

        if not device_token_obj:
            return Response(
                {"result": "deny", "message": _("Ivalid token or password.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        device_token_obj.last_used_at = timezone.now()
        device_token_obj.save()
        
        return Response(
            {
                "result": "allow",
                "is_superuser": device_token_obj.is_superuser,
                "acl": [],  # query from Model TokenACL
            },
            status=status.HTTP_200_OK,
        )


class WSTicketView(APIView):
    """
    ออก Short-lived One-Time Ticket สำหรับ WebSocket connection
    Ticket มี TTL 30 วินาที และใช้ได้ครั้งเดียว

    Requires: Authorization: Bearer <access_token>

    POST /api/v1/ws-ticket/
    Response:
    {
        "ticket": "<random_hex_token>",
        "ttl": 30
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        ttl: int = getattr(settings, "WS_TICKET_TTL", 30)
        ticket = secrets.token_hex(32)
        key = f"ws_ticket:{ticket}"

        redis = get_redis_connection("token")
        redis.set(key, str(request.user.pk), ex=ttl)

        return Response(
            {"ticket": ticket, "ttl": ttl},
            status=status.HTTP_201_CREATED,
        )


