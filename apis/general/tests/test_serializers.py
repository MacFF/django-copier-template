from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase

from apis.general.models import AuditLog, RelatedValueAuditLog
from apis.general.serializers import AuditLogSerializer

User = get_user_model()


class AuditLogSerializerTest(APITestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email="test@test.com"
        )

        self.user_content_type = ContentType.objects.get_for_model(User)
        
        self.audit_log = AuditLog.objects.create(
            actor=self.actor,
            action="CREATE",
            template_message="User {user__username} was created",
            # content_type=self.user_content_type,
            object_id=self.actor.id,
            object_type=self.user_content_type,
            # object=self.actor,
        )
        
        # สร้าง RelatedValueAuditLog ถ้าต้องการ
        self.related_value = RelatedValueAuditLog.objects.create(
            log=self.audit_log,
            text_format="user__username",
            object=self.actor
        )

    def test_audit_log_serializer_basic(self):
        """Test basic serialization of AuditLog"""
        serializer = AuditLogSerializer(self.audit_log)
        data = serializer.data
        
        self.assertEqual(data["action"], "CREATE")
        self.assertEqual(data["actor"], "Test User")
        self.assertNotIn("template_message", data)

    def test_audit_log_serializer_message_formatting(self):
        """Test message formatting with template"""
        serializer = AuditLogSerializer(self.audit_log)
        data = serializer.data
        
        expected_message = "User testuser was created"
        self.assertEqual(data["message"], expected_message)

    def test_audit_log_serializer_message_without_related_values(self):
        """Test message when no related values exist"""
        audit_log = AuditLog.objects.create(
            actor=self.actor,
            action="UPDATE",
            template_message="User was updated",
            object_id=self.actor.id,
            object_type=self.user_content_type,
        )
        
        serializer = AuditLogSerializer(audit_log)
        data = serializer.data
        
        self.assertEqual(data["message"], "User was updated")

    def test_audit_log_serializer_multiple_format_fields(self):
        """Test message with multiple format fields"""
        audit_log = AuditLog.objects.create(
            actor=self.actor,
            action="CREATE",
            template_message="User {user__username} ({user__email}) was created",
            # content_type_id=1,
            # object_id="1"
            object_id=self.actor.id,
            object_type=self.user_content_type,
        )
        
        RelatedValueAuditLog.objects.create(
            log=audit_log,
            text_format="user__username",
            object=self.actor
        )
        RelatedValueAuditLog.objects.create(
            log=audit_log,
            text_format="user__email",
            object=self.actor
        )
        
        serializer = AuditLogSerializer(audit_log)
        data = serializer.data
        
        expected_message = "User testuser (test@test.com) was created"
        self.assertEqual(data["message"], expected_message)

    def test_audit_log_serializer_all_fields(self):
        """Test that all expected fields are present"""
        serializer = AuditLogSerializer(self.audit_log)
        data = serializer.data
        
        expected_fields = ["id", "actor", "action", "message", "object_type", "object_id", "timestamp"]
        for field in expected_fields:
            self.assertIn(field, data)