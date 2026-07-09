from django.db.models import TextChoices


class AuditLogTool(TextChoices):
    """
    Categorization by Feature or App
    """
    AUTH = "auth"


class AuditLogAction(TextChoices):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
