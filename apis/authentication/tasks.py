import logging

from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from {{project_slug}}.celery_redis import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_html_email_task(self, subject, template_path, context, recipient_list):
    logger.info(f"Starting to send email to {recipient_list} with subject: {subject}")
    
    try:
        html_content = render_to_string(template_path, context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            to=recipient_list,
        )
        msg.attach_alternative(html_content, "text/html")
        
        result = msg.send()
        
        if result:
            logger.info(f"Email successfully sent to {recipient_list}")
        else:
            logger.warning(f"Email to {recipient_list} was not sent (Zero recipients accepted)")
            
    except Exception as exc:
        logger.error(f"Error sending email to {recipient_list}: {exc}", exc_info=True)
        # Retry when Error (Ex. SMTP Timeout)
        raise self.retry(exc=exc)
