import json

from django.urls import include, path, reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase
from unittest.mock import patch

from apis.authentication.choices import UserStatus, UserPermission
from apis.authentication.models import UserProfile
from {{project_slug}}.base.functions import encode_user_id, get_system_user

User = get_user_model()


class UserAPITestCase(APITestCase):
    def setUp(self):
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username="superadmin",
            password="superadmin123",
            email="superadmin@test.com",
            first_name="Super",
            last_name="Admin",
        )

        # Create system user
        self.system_user = User.objects.create_user(
                username="system@mail.com",
                email="system@mail.com",
                first_name="System",
                is_active=False,
            )

        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            password="admin123",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            is_staff=True,
            is_superuser=False,
            status=UserStatus.ACTIVE,
            permission=UserPermission.Admin,
        )

        self.normal_user = User.objects.create_user(
            username="normal",
            password="normal123",
            first_name="Normal",
            last_name="User",
            email="normal@test.com",
            status=UserStatus.ACTIVE,
            permission=UserPermission.General,
        )

        self.pending_user = User.objects.create_user(
            username="pending",
            password="pending123",
            first_name="Pending",
            last_name="User",
            email="pending@test.com",
            status=UserStatus.PENDING,
            permission=UserPermission.General,
        )

        self.suspended_user = User.objects.create_user(
            username="suspended",
            password="suspended123",
            first_name="Suspended",
            last_name="User",
            email="suspended@test.com",
            status=UserStatus.SUSPENDED,
            permission=UserPermission.General,
            is_active=False,
        )

        # Create profiles
        UserProfile.objects.create(user=self.admin_user)
        UserProfile.objects.create(user=self.normal_user)
        UserProfile.objects.create(user=self.pending_user)
        UserProfile.objects.create(user=self.suspended_user)

        # Tokens for pending user
        self.pending_token = default_token_generator.make_token(self.pending_user)
        self.pending_hashed_id = encode_user_id(self.pending_user.pk)

        # Invalid token
        self.invalid_token = "invalid-token-123"


class VerifyPasswordTokenAPITest(UserAPITestCase):
    def test_verify_valid_token(self):
        """Test verifying a valid password reset token"""
        url = reverse('verify-password-token', kwargs={
            'hashed_id': self.pending_hashed_id,
            'token': self.pending_token
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['message'], "Token is usable.")

    def test_verify_invalid_token(self):
        """Test verifying an invalid password reset token"""
        url = reverse('verify-password-token', kwargs={
            'hashed_id': self.pending_hashed_id,
            'token': self.invalid_token
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['message'], "Token is invalid or expired.")

    def test_verify_nonexistent_user(self):
        """Test verifying token for nonexistent user"""
        fake_hashed_id = encode_user_id(99999)
        url = reverse('verify-password-token', kwargs={
            'hashed_id': fake_hashed_id,
            'token': self.pending_token
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "User not found.")


class ResendEmailSetPasswordAPITest(UserAPITestCase):
    @patch('apis.authentication.views.user.EmailService.send_set_password_email')
    def test_resend_email_success(self, mock_send_email):
        """Test resending set password email for pending user"""
        url = reverse('resend-email-set-password', kwargs={
            'hashed_id': self.pending_hashed_id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "A new set-password email has been sent.")
        mock_send_email.assert_called_once_with(user=self.pending_user)

    def test_resend_email_non_pending_user(self):
        """Test resending email fails for non-pending user"""
        active_hashed_id = encode_user_id(self.normal_user.pk)
        url = reverse('resend-email-set-password', kwargs={
            'hashed_id': active_hashed_id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Only pending users can receive this email.")

    def test_resend_email_nonexistent_user(self):
        """Test resending email for nonexistent user"""
        fake_hashed_id = encode_user_id(99999)
        url = reverse('resend-email-set-password', kwargs={
            'hashed_id': fake_hashed_id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "User not found.")


class SetPasswordAPITest(UserAPITestCase):
    def test_set_password_success(self):
        """Test setting password with valid token"""
        url = reverse('set-password', kwargs={
            'hashed_id': self.pending_hashed_id,
            'token': self.pending_token
        })
        data = {
            'password': 'Swd_12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Password set successfully.")

        # Verify password was set
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.check_password("Swd_12345"))

    def test_set_password_invalid_token(self):
        """Test setting password with invalid token"""
        url = reverse('set-password', kwargs={
            'hashed_id': self.pending_hashed_id,
            'token': self.invalid_token
        })
        data = {
            'password': 'newpassword123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Invalid or expired token.")

    def test_set_password_nonexistent_user(self):
        """Test setting password for nonexistent user"""
        fake_hashed_id = encode_user_id(99999)
        url = reverse('set-password', kwargs={
            'hashed_id': fake_hashed_id,
            'token': self.pending_token
        })
        data = {
            'password': 'newpassword123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_set_password_invalid_data(self):
        """Test setting password with invalid data"""
        url = reverse('set-password', kwargs={
            'hashed_id': self.pending_hashed_id,
            'token': self.pending_token
        })
        data = {
            'password': 'short',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserViewSetTest(UserAPITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api/", include("apis.authentication.urls")),
    ]

    def test_list_users_authenticated(self):
        """Test listing users when authenticated"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("v1:user-auth-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not include system user or superuser
        list_user_id = [user["id"] for user in response.data["results"]]
        self.assertNotIn(self.system_user.pk, list_user_id)
        self.assertNotIn(self.superuser.pk, list_user_id)

    def test_list_users_unauthenticated(self):
        """Test listing users when not authenticated"""
        url = reverse("v1:user-auth-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_authenticated(self):
        """Test retrieving user detail when authenticated"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("v1:user-auth-detail", kwargs={"pk": self.normal_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.normal_user.pk)

    def test_retrieve_nonexistent_user(self):
        """Test retrieving nonexistent user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("v1:user-auth-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_user_authenticated(self):
        """Test deleting user when authenticated"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-detail', kwargs={'pk': self.normal_user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify user is soft deleted
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.deleted)

    def test_me_authenticated(self):
        """Test getting current user info"""
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('v1:user-auth-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.normal_user.pk)

    @patch("apis.authentication.views.user.EmailService.send_set_password_email")
    def test_register_success(self, mock_send_email):
        """Test registering new user"""
        print(f"mock_send_email: {mock_send_email}")
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'prefix': 'นาย',
            'permission': UserPermission.General,
        }
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser@test.com")
        mock_send_email.assert_called_once()

    def test_register_duplicate_username(self):
        """Test registering with duplicate username"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-register')
        data = {
            'username': 'normal',  # Already exists
            'email': 'newemail@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'national_id': '2222222222222',
            'prefix': 'นาย',
            'permission': UserPermission.General,
        }
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suspend_user_success(self):
        """Test suspending active user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-suspend', kwargs={'pk': self.normal_user.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "User was suspended.")
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.status, UserStatus.SUSPENDED)
        self.assertFalse(self.normal_user.is_active)

    def test_suspend_already_suspended_user(self):
        """Test suspending already suspended user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-suspend', kwargs={'pk': self.suspended_user.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "User is already suspended.")

    def test_activate_user_success(self):
        """Test activating suspended user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-active', kwargs={'pk': self.suspended_user.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "User was active.")
        self.suspended_user.refresh_from_db()
        self.assertEqual(self.suspended_user.status, UserStatus.ACTIVE)
        self.assertTrue(self.suspended_user.is_active)

    @patch('apis.authentication.views.user.EmailService.send_set_password_email')
    def test_send_verification_email_success(self, mock_send_email):
        """Test sending verification email to pending user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-send-verification-email', kwargs={'pk': self.pending_user.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "The email has been successfully sent.")
        mock_send_email.assert_called_once_with(user=self.pending_user)

    def test_send_verification_email_non_pending_user(self):
        """Test sending verification email to non-pending user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('v1:user-auth-send-verification-email', kwargs={'pk': self.normal_user.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Emails can only be sent to user status pending.")


class CustomLoginViewTest(UserAPITestCase):
    """Test cases for CustomLoginView"""
    
    def test_login_success(self):
        """Test successful login"""
        url = reverse("auth_login")
        data = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
    
    def test_login_with_invalid_username(self):
        """Test login with invalid username"""
        url = reverse("auth_login")
        data = {
            "username": "nonexistent",
            "password": "admin123"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_with_invalid_password(self):
        """Test login with invalid password"""
        url = reverse("auth_login")
        data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_with_missing_username(self):
        """Test login without username"""
        url = reverse("auth_login")
        data = {
            "password": "admin123"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
    
    def test_login_with_missing_password(self):
        """Test login without password"""
        url = reverse("auth_login")
        data = {
            "username": "admin"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
    
    def test_login_with_inactive_user(self):
        """Test login with inactive user"""
        url = reverse("auth_login")
        data = {
            "username": "system@mail.com",
            "password": "system123"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_returns_tokens_with_correct_fields(self):
        """Test that login returns tokens with required fields"""
        url = reverse("auth_login")
        data = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # ตรวจสอบว่า access token มี payload
        self.assertIn("access", response.data)
        access_token = response.data["access"]
        self.assertIsNotNone(access_token)
        
        # ตรวจสอบว่า refresh token มี payload
        self.assertIn("refresh", response.data)
        refresh_token = response.data["refresh"]
        self.assertIsNotNone(refresh_token)
    
    def test_login_multiple_times_different_tokens(self):
        """Test that multiple logins generate different tokens"""
        url = reverse("auth_login")
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response1 = self.client.post(url, data, format="json")
        response2 = self.client.post(url, data, format="json")
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # แต่ละครั้งควรได้ token ต่างกัน
        self.assertNotEqual(
            response1.data["access"],
            response2.data["access"],
            "Different login attempts should generate different access tokens"
        )
