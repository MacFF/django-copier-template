from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model

from apis.general.choices import AuditLogAction, AuditLogTool


User = get_user_model()


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        blank=False,
        null=True,
        related_name="actor_historylogs",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    template_message = models.TextField(blank=False, null=False)

    object_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveBigIntegerField(blank=False, null=True)
    object = GenericForeignKey("object_type", "object_id")

    tool = models.CharField(choices=AuditLogTool)
    action = models.CharField(choices=AuditLogAction)
    changes = models.JSONField(null=True)


class RelatedValueAuditLog(models.Model):
    log = models.ForeignKey(AuditLog, on_delete=models.PROTECT, related_name="audit_log")

    text_format = models.TextField(blank=False, null=False)

    object_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, blank=False, null=True)
    object_id = models.PositiveBigIntegerField(blank=False, null=True)
    object = GenericForeignKey("object_type", "object_id")

    default_value = models.TextField(default="")
