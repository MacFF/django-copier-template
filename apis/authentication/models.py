import uuid
import secrets
import hashlib

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.fields.generated import GeneratedField
from django.contrib.postgres.fields import ArrayField
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from safedelete.config import SOFT_DELETE_CASCADE
from safedelete.managers import SafeDeleteManager
from safedelete.models import SafeDeleteModel

from apis.authentication.choices import ACLAction, ACLPermission, ACLQoS, UserPermission, UserStatus
from apis.authentication.utils import user_avatar_upload_path
from {{project_slug}}.base.models import BaseModel


class FamilyRefreshToken(models.Model):
    family = models.UUIDField()
    is_blacklisted = models.BooleanField(default=False)
    blacklisted_at = models.DateTimeField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Family Refresh Token"
        verbose_name_plural = "Family Refresh Tokens"


class SafeDeleteUserManager(SafeDeleteManager, UserManager):
    """Manager for User model with safe delete functionality."""
    pass


class User(SafeDeleteModel, AbstractUser):
    _safedelete_policy = SOFT_DELETE_CASCADE

    national_id = models.CharField(max_length=13, unique=True, blank=True, null=True)
    prefix = models.CharField(max_length=10, blank=True, null=True)
    en_prefix = models.CharField(max_length=10, blank=True, null=True)
    en_first_name = models.CharField(max_length=100, blank=True, null=True)
    en_last_name = models.CharField(max_length=100, blank=True, null=True)
    home_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)
    status = models.IntegerField(choices=UserStatus, default=UserStatus.PENDING)
    permission = models.CharField(choices=UserPermission, default=UserPermission.General)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        related_name="updated_by_user",
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        related_name="created_by_user",
        blank=True,
        null=True,
    )

    objects = SafeDeleteUserManager()
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["id"]
        verbose_name = "User"
        verbose_name_plural = verbose_name

    def get_full_name(self):
        self.prefix = self.prefix if self.prefix not in ["ไม่ระบุ", "Other"] else None
        return f"{self.prefix + ' ' if self.prefix else ''}{self.first_name} {self.last_name}"

    def __str__(self):
        return self.get_full_name()

    @property
    def full_name(self):
        return self.get_full_name()


class UserProfile(SafeDeleteModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to=user_avatar_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.full_name}"
    

class DeviceToken(BaseModel):
    mqtt_topic = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"

    @classmethod
    def generate_token_instance(cls, mqtt_topic, user):
        """
        สร้าง token ใหม่สำหรับ device
        คืนค่า (instance, plain_token) — plain_token แสดงครั้งเดียวเท่านั้น
        """
        plain_token = secrets.token_urlsafe(32)

        instance = cls.objects.create(
            mqtt_topic=mqtt_topic,
            token=plain_token,
            created_by=user,
            updated_by=user,
        )
        return instance, plain_token
    

class TokenACL(models.Model):
    """
    ACL rules สำหรับ DeviceToken
    กำหนดสิทธิ์ว่า token นี้ publish/subscribe topic อะไรได้บ้าง

    EMQX ACL Webhook Response format:
    {
        "result": "allow",
        "actions": ["publish", "subscribe"],
        "qos": [0, 1, 2],
        "retain": true
    }
    """
    device_token = models.ForeignKey(DeviceToken, on_delete=models.CASCADE, related_name="acl_rules",)
    permission = models.CharField(max_length=10, choices=ACLPermission, default=ACLPermission.ALLOW,)
    action = models.CharField(
        max_length=10,
        choices=ACLAction,
        default=ACLAction.ALL,
    )
    topic = models.CharField(
        max_length=255,
        help_text="MQTT topic เช่น swd/sensor/+/data หรือใช้ wildcard + และ #",
    )
    qos = ArrayField(
        base_field=models.IntegerField(choices=ACLQoS),
        default=ACLQoS.default_qos,
    )
    retain = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Token ACL"
        verbose_name_plural = "Token ACLs"
        unique_together = [["device_token", "action", "topic"]]

    def __str__(self):
        return f"{self.device_token} | {self.action} | {self.topic} | {self.permission}"
