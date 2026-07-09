from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apis.authentication.choices import UserPermission, UserStatus
from apis.authentication.models import UserProfile
from {{project_slug}}.base.models import BaseModel

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="pass1234",
            first_name="Somchai",
            last_name="Sukjai",
            national_id="1234567890123",
            prefix="นาย",
            status=UserStatus.ACTIVE,  # หรือค่าที่มีใน Enum
            permission=UserPermission.General,  # หรือค่าที่มีใน Enum
        )

    def test_user_str_fullname(self):
        self.assertEqual(str(self.user), "นาย Somchai Sukjai")
        self.assertEqual(self.user.full_name, "นาย Somchai Sukjai")

    def test_user_get_full_name_with_other_prefix(self):
        self.user.prefix = "Other"
        self.user.first_name = "A"
        self.user.last_name = "B"
        self.user.save()
        self.assertEqual(self.user.get_full_name(), "A B")

    def test_user_unique_national_id(self):
        with self.assertRaises(ValidationError):
            dup = User(
                username="testuser2",
                national_id="1234567890123",
                password="pass2222",
            )
            dup.full_clean()  # force validate unique
            dup.save()


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            password="pass1234",
            first_name="Som",
            last_name="Chai",
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "Profile of Som Chai")

    def test_profile_user_relation(self):
        self.assertEqual(self.user.profile, self.profile)
        self.assertEqual(self.profile.user, self.user)

    def test_profile_uuid_auto_created(self):
        self.assertIsNotNone(self.profile.uuid)