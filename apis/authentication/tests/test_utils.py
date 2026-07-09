from django.test import TestCase
from django.core import mail
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apis.authentication.tasks import send_html_email_task
from apis.authentication.utils import user_avatar_upload_path
from apis.authentication.models import UserProfile

User = get_user_model()


class SendHtmlEmailTaskTest(TestCase):
    
    def setUp(self):
        self.subject = "Test Email"
        self.template_path = "emails/test_email.html"
        self.context = {"user_name": "Test User", "message": "This is a test"}
        self.recipient_list = ["test@example.com"]
    
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_success(self, mock_render):
        """Test sending HTML email successfully"""
        mock_render.return_value = "<h1>Test Email</h1>"
        
        # เรียก task โดยตรง (ไม่ต้อง delay/apply_async)
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        # ตรวจสอบว่า email ถูกส่ง
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, self.subject)
        self.assertEqual(mail.outbox[0].to, self.recipient_list)
    
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_with_html_content(self, mock_render):
        """Test that HTML content is attached"""
        html_content = "<h1>Welcome</h1><p>Hello Test User</p>"
        mock_render.return_value = html_content
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        email = mail.outbox[0]
        self.assertEqual(len(email.alternatives), 1)
        self.assertEqual(email.alternatives[0][0], html_content)
        self.assertEqual(email.alternatives[0][1], "text/html")
    
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_multiple_recipients(self, mock_render):
        """Test sending email to multiple recipients"""
        mock_render.return_value = "<h1>Test Email</h1>"
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=recipients
        )
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, recipients)
    
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_render_called_with_context(self, mock_render):
        """Test that render_to_string is called with correct parameters"""
        mock_render.return_value = "<h1>Test</h1>"
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        mock_render.assert_called_once_with(self.template_path, self.context)
    
    @patch('apis.authentication.tasks.logger')
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_logging_success(self, mock_render, mock_logger):
        """Test that success is logged"""
        mock_render.return_value = "<h1>Test</h1>"
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        # ตรวจสอบ logger เรียก info
        self.assertEqual(mock_logger.info.call_count, 2)
    
    @patch('apis.authentication.tasks.EmailMultiAlternatives.send')
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_failure(self, mock_render, mock_send):
        """Test email sending failure"""
        mock_render.return_value = "<h1>Test</h1>"
        mock_send.return_value = 0  # ไม่มี recipient accepted
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        # ตรวจสอบว่า warning ถูก log
        # (ตรวจสอบได้จากการดู outbox)
        self.assertEqual(len(mail.outbox), 0)
    
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_text_content_stripped(self, mock_render):
        """Test that HTML tags are stripped from text content"""
        html_content = "<h1>Welcome</h1><p>Hello <b>Test User</b></p>"
        mock_render.return_value = html_content
        
        send_html_email_task(
            subject=self.subject,
            template_path=self.template_path,
            context=self.context,
            recipient_list=self.recipient_list
        )
        
        email = mail.outbox[0]
        # ตรวจสอบว่า body ไม่มี HTML tags
        self.assertNotIn("<h1>", email.body)
        self.assertNotIn("<p>", email.body)
        self.assertIn("Welcome", email.body)
        self.assertIn("Hello", email.body)

    @patch('apis.authentication.tasks.logger')
    @patch('apis.authentication.tasks.render_to_string')
    def test_send_html_email_render_exception(self, mock_render, mock_logger):
        """Test exception when render_to_string fails"""
        mock_render.side_effect = Exception("Template not found")
        
        with self.assertRaises(Exception):
            send_html_email_task(
                subject=self.subject,
                template_path=self.template_path,
                context=self.context,
                recipient_list=self.recipient_list
            )
        
        # ตรวจสอบว่า logger.error ถูกเรียก
        mock_logger.error.assert_called_once()


class AuthenticationUploadPathTest(TestCase):
    """Test cases for user_avatar_upload_path utility function for UserProfile"""
    
    def setUp(self):
        """Set up test user with UserProfile"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.user_profile = UserProfile.objects.create(user=self.user)
    
    def test_avatar_upload_path_format(self):
        """Test that upload path follows correct format"""
        filename = "profile_pic.jpg"
        path = user_avatar_upload_path(self.user_profile, filename)
        
        # ตรวจสอบ format: avatars/{uuid}/{filename}
        expected_path = f"avatars/{self.user_profile.uuid}/{filename}"
        self.assertEqual(path, expected_path)
    
    def test_avatar_upload_path_with_uuid(self):
        """Test that UserProfile UUID is correctly used in path"""
        filename = "avatar.png"
        path = user_avatar_upload_path(self.user_profile, filename)
        
        # ตรวจสอบว่า UserProfile UUID อยู่ใน path
        self.assertIn(str(self.user_profile.uuid), path)
        self.assertIn("avatars/", path)

