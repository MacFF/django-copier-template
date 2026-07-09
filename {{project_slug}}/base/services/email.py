from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from apis.authentication.tasks import send_html_email_task
from {{project_slug}}.base.functions import encode_user_id

User = get_user_model()


class EmailService:
    
    @classmethod
    def send_verification_email(cls, user, token: str):
        """ส่งเมลยืนยันตัวตนพร้อมปุ่ม Link"""
        
        subject = "ยืนยันอีเมลของคุณสำหรับระบบรับรองมาตรฐาน"
        template_name = "emails/verify_email.html"
        context = {
            "full_name": user.get_full_name(),
            "verify_url": f"..../verify?token={token}",
        }

        return send_html_email_task.delay(subject, template_name, context, [user.email])
    
    @classmethod
    def send_set_password_email(cls, user):
        hashed_id = encode_user_id(user.pk)
        token = default_token_generator.make_token(user)

        # subject = "เปลี่ยนนหัสผ่านของคุณสำหรับระบบกรมทางหลวงชนบท"
        subject = "Change your password for the Department of Rural Roads system."
        template_name = "email/reset_password.html"
        context = {
            "reset_password_url": f"{settings.FRONTEND_URL_SET_PASSWORD}/set-password/{hashed_id}/{token}/",
        }

        return send_html_email_task.delay(subject, template_name, context, [user.email])
