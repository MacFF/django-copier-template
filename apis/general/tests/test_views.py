import json
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import path, include, reverse
from rest_framework.test import URLPatternsTestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class ChoicesAPIViewTest(APITestCase):
    """Test cases for ChoicesAPIView API endpoint"""
    
    # urlpatterns = [
    #     path("api/", include("apis.general.urls")),
    # ]
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse("choices")
        self.admin_user = User.objects.create_user(
            username="admin",
            password="admin123",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            is_staff=True,
            is_superuser=False,
        )
    
    def test_get_choice_without_model_key(self):
        """Test request without 'model' key"""
        self.client.force_authenticate(user=self.admin_user)
        data = [
            {
                "key": "status"
                # missing 'model' key
            }
        ]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertIn("`model` key is required", response.data["message"])
    
    @patch('{{project_slug}}.base.choice_controllers.get_choices_setting')
    @patch('{{project_slug}}.base.choice_controllers.perform_import_controller')
    def test_empty_request_data(self, mock_controller, mock_settings):
        """Test with empty request data"""
        data = []
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})
