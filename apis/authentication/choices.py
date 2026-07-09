from django.db.models import IntegerChoices, TextChoices


class UserStatus(IntegerChoices):
    PENDING = 1, "กำลังยืนยันอีเมล"
    SUSPENDED = 2, "ถูกระงับ"
    ACTIVE = 3, "ใช้งาน"

    @property
    def choices_information(self):
        return {
            "value": self.value,
            "label": self.label,
        }


class UserPermission(TextChoices):
    General = "general", "ผู้ใช้งานทั่วไป"
    Staff = "staff", "เจ้าหน้าที่"
    Admin = "admin", "ผู้ดูแลระบบ"

    @property
    def choices_information(self):
        return {
            "value": self.value,
            "label": self.label,
        }


class ACLPermission(TextChoices):
    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"


class ACLAction(TextChoices):
    PUBLISH = "publish", "Publish"
    SUBSCRIBE = "subscribe", "Subscribe"
    ALL = "all", "All"


class ACLQoS(IntegerChoices):
    QOS_0 = 0, "QoS 0 - At most once"
    QOS_1 = 1, "QoS 1 - At least once"
    QOS_2 = 2, "QoS 2 - Exactly once"

    @classmethod
    def default_qos(cls):
        return [cls.QOS_0, cls.QOS_1]
