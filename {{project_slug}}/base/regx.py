import re
from django.utils.translation import gettext_lazy as _

class RegexPatterns:
    PASSWORD = {
        "regex": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[._@$!%*?&#])[A-Za-z\d._@$!%*?&#]{8,}$',
        "message": _("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร ประกอบด้วยตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และอักขระพิเศษ (._@$!%%*?&#)")
    }
    THAI_NATIONAL_ID = {
        "regex": r'(\d{13})|(\d{1}\-?\d{4}\-?\d{5}\-?\d{2}\-?\d{1})',
        "message": _("หมายเลขบัตรประชาชนไม่ถูกต้อง")
    }


def password_regex_validate(value: str):
    """
    Returns a RegexValidator for password validation.
    """
    return re.match(RegexPatterns.PASSWORD["regex"], value)
