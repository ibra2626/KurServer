"""
Test cases for unified site management system.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import json

from src.kurserver.managers.nginx import site_management_menu
from src.kurserver.managers.github_settings import github_settings_menu
from src.kurserver.cli.menu import create_main_menu


class TestUnifiedSiteManagement(unittest.TestCase):
    """Test unified site management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, ".kurserver")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Mock config directory
        self.config_patcher = patch('os.path.expanduser')
        self.mock_expanduser = self.config_patcher.start()
        self.mock_expanduser.return_value = self.config_dir
    
    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_menu_structure(self):
        """Test that main menu has correct structure after unification."""
        menu = create_main_menu()
        
        # Check that redundant options are removed
        option_keys = [opt.key for opt in menu.options]
        
        # Should NOT have these old options
        self.assertNotIn("6", option_keys)  # Old "GitHub deployment"
        self.assertNotIn("7", option_keys)  # Old "Update site from GitHub"
        
        # Should have these new options
        self.assertIn("4", option_keys)  # "Site Management"
        self.assertIn("6", option_keys)  # "GitHub settings"
        
        # Check descriptions
        option_descriptions = {opt.key: opt.description for opt in menu.options}
        self.assertEqual(option_descriptions["4"], "Site Management")
        self.assertEqual(option_descriptions["6"], "GitHub settings")
    
    @patch('src.kurserver.managers.nginx.is_package_installed')
    @patch('src.kurserver.managers.nginx.Menu')
    def test_site_management_menu_structure(self, mock_menu, mock_installed):
        """Test that site management menu has correct structure."""
        mock_installed.return_value = True
        
        # Call the function
        site_management_menu()
        
        # Check that Menu was called with correct options
        mock_menu.assert_called_once()
        args, kwargs = mock_menu.call_args
        
        # Check menu title
        self.assertEqual(kwargs['title'], "Site Management")
        
        # Check that we have 7 options (no longer 8)
        options = args[0]  # First positional argument should be options list
        self.assertEqual(len(options), 7)
        
        # Check option descriptions
        option_keys = [opt.key for opt in options]
        self.assertIn("1", option_keys)  # "Add new website"
        self.assertIn("3", option_keys)  # "Update existing site" (changed from "Update deployment")
        self.assertNotIn("7", option_keys)  # Old "Update deployment" should be gone
    
    @patch('src.kurserver.managers.github_settings.Menu')
    def test_github_settings_menu_structure(self, mock_menu):
        """Test that GitHub settings menu has correct structure."""
        
        # Call the function
        github_settings_menu()
        
        # Check that Menu was called with correct options
        mock_menu.assert_called_once()
        args, kwargs = mock_menu.call_args
        
        # Check menu title
        self.assertEqual(kwargs['title'], "GitHub Settings")
        
        # Check that we have 4 options
        options = args[0]
        self.assertEqual(len(options), 4)
        
        # Check option descriptions
        option_descriptions = {opt.key: opt.description for opt in options}
        self.assertEqual(option_descriptions["1"], "Configure GitHub access token")
        self.assertEqual(option_descriptions["2"], "List all deployments")
        self.assertEqual(option_descriptions["3"], "Remove deployment configuration")
        self.assertEqual(option_descriptions["4"], "Test GitHub connection")
    
    @patch('src.kurserver.managers.github_settings._get_stored_github_token')
    @patch('src.kurserver.managers.github_settings._validate_github_token')
    @patch('src.kurserver.managers.github_settings._store_github_token')
    @patch('src.kurserver.managers.github_settings.get_user_input')
    @patch('src.kurserver.managers.github_settings.confirm_action')
    def test_configure_github_token_new(self, mock_confirm, mock_input, 
                                     mock_store, mock_validate, mock_get):
        """Test configuring a new GitHub token."""
        # Setup mocks
        mock_get.return_value = None  # No existing token
        mock_input.return_value = "test_token_123"
        mock_validate.return_value = True
        mock_confirm.return_value = True
        
        # Call the function
        from src.kurserver.managers.github_settings import configure_github_token
        configure_github_token()
        
        # Verify interactions
        mock_get.assert_called_once()
        mock_input.assert_called_with("Enter GitHub personal access token", password=True)
        mock_validate.assert_called_once_with("test_token_123")
        mock_store.assert_called_once_with("test_token_123")
    
    def test_github_token_storage(self):
        """Test that GitHub token is stored correctly."""
        from src.kurserver.managers.github_settings import _store_github_token, _get_stored_github_token
        
        # Store a token
        test_token = "ghp_test_token_12345"
        _store_github_token(test_token)
        
        # Retrieve it
        retrieved_token = _get_stored_github_token()
        self.assertEqual(retrieved_token, test_token)
        
        # Check file exists and has correct content
        config_file = os.path.join(self.config_dir, "config.json")
        self.assertTrue(os.path.exists(config_file))
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config['github_token'], test_token)
    
    @patch('src.kurserver.deployment.github._get_deployments')
    def test_remove_deployment(self, mock_get_deployments):
        """Test removing deployment configuration."""
        from src.kurserver.deployment.github import _remove_deployment, _save_deployment_info
        
        # Setup mock deployments
        mock_deployments = {
            'example.com': {
                'repo_url': 'https://github.com/user/example.git',
                'branch': 'main',
                'web_root': '/var/www/example.com',
                'private': False
            },
            'test.com': {
                'repo_url': 'https://github.com/user/test.git',
                'branch': 'main',
                'web_root': '/var/www/test.com',
                'private': False
            }
        }
        mock_get_deployments.return_value = mock_deployments
        
        # Save initial deployments
        from src.kurserver.deployment.github import _get_deployments
        deployments_file = os.path.join(self.config_dir, "deployments", "github.json")
        os.makedirs(os.path.dirname(deployments_file), exist_ok=True)
        
        with open(deployments_file, 'w') as f:
            json.dump(mock_deployments, f, indent=2)
        
        # Remove one deployment
        _remove_deployment('example.com')
        
        # Check that deployment was removed
        with open(deployments_file, 'r') as f:
            updated_deployments = json.load(f)
        
        self.assertNotIn('example.com', updated_deployments)
        self.assertIn('test.com', updated_deployments)


if __name__ == '__main__':
    unittest.main()