import os
from io import StringIO
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from apis.general.management.commands.seeds import Command
from apis.general.management.commands.system_seed import Command as SystemSeedCommand

User = get_user_model()


class SeedsCommandTest(TestCase):
    def setUp(self):
        self.command = Command()
        self.out = StringIO()
    
    @patch('apis.general.management.commands.seeds.call_command')
    @patch.dict(os.environ, {'DJANGO_RUN_SYSTEM_SEED': 'false'})
    def test_seeds_command_skips_system_seed_when_disabled(self, mock_call_command):
        """Test that system_seed command is NOT called when env var is 'false'"""
        self.command.handle(stdout=self.out)
        
        # Verify system_seed was NOT called
        mock_call_command.assert_not_called()
    
    @patch('apis.general.management.commands.seeds.call_command')
    @patch.dict(os.environ, {'DJANGO_RUN_SYSTEM_SEED': 'true'})
    def test_seeds_command_handles_system_seed_error(self, mock_call_command):
        """Test that command handles errors from system_seed"""
        # Mock system_seed to raise an exception
        mock_call_command.side_effect = Exception("System seed error")
        
        # The command should raise the exception
        with self.assertRaises(Exception):
            self.command.handle(stdout=self.out)


class SystemSeedCommandTest(TestCase):
    def setUp(self):
        self.command = SystemSeedCommand()
        self.out = StringIO()
        # Clean up any existing system user and superuser
        User.objects.filter(email="system@mail.com").delete()
        User.objects.filter(is_superuser=True).delete()
    
    def test_seed_system_user_creates_user(self):
        """Test that seed_system_user creates a system user"""
        self.command.seed_system_user()
        
        # Verify system user was created
        system_user = User.objects.filter(email="system@mail.com").first()
        self.assertIsNotNone(system_user)
        self.assertEqual(system_user.username, "system@mail.com")
        self.assertEqual(system_user.first_name, "System")
        self.assertFalse(system_user.is_active)
        self.assertFalse(system_user.has_usable_password())
    
    def test_seed_system_user_does_not_create_duplicate(self):
        """Test that seed_system_user does not create duplicate user"""
        self.command.seed_system_user()
        self.command.seed_system_user()
        
        # Verify only one system user exists
        count = User.objects.filter(email="system@mail.com").count()
        self.assertEqual(count, 1)
    
    @patch('apis.general.management.commands.system_seed.call_command')
    def test_seed_superuser_calls_createsuperuser_when_none_exists(self, mock_call_command):
        """Test that seed_superuser calls createsuperuser when no superuser exists"""
        self.command.seed_superuser()
        
        # Verify createsuperuser was called
        mock_call_command.assert_called_with('createsuperuser', interactive=True)
    
    @patch('apis.general.management.commands.system_seed.call_command')
    def test_seed_superuser_skips_when_exists(self, mock_call_command):
        """Test that seed_superuser skips creation when superuser already exists"""
        # Create a superuser first
        User.objects.create_superuser(username="admin", email="admin@mail.com", password="pass")
        
        self.command.seed_superuser()
        
        # Verify createsuperuser was NOT called
        mock_call_command.assert_not_called()
    
    @patch('apis.general.management.commands.system_seed.call_command')
    def test_handle_runs_both_seed_methods(self, mock_call_command):
        """Test that handle runs both seed_system_user and seed_superuser"""
        self.command.handle(stdout=self.out)
        
        # Verify system user was created
        system_user = User.objects.filter(email="system@mail.com").first()
        self.assertIsNotNone(system_user)
        
        # Verify createsuperuser was called
        mock_call_command.assert_called_with('createsuperuser', interactive=True)
