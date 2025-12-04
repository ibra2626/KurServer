"""
Integration tests for unified site management workflows.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from src.kurserver.cli.menu import create_main_menu


class TestUnifiedWorkflows(unittest.TestCase):
    """Test unified workflows end-to-end."""
    
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
    
    def test_unified_menu_structure_integration(self):
        """Test that the unified menu structure is properly integrated."""
        menu = create_main_menu()
        
        # Verify main menu has correct number of options (9 instead of 10)
        self.assertEqual(len(menu.options), 9)
        
        # Check option keys are sequential starting from 1
        expected_keys = [str(i) for i in range(1, 10)]  # 1-9
        actual_keys = [opt.key for opt in menu.options]
        self.assertEqual(actual_keys, expected_keys)
        
        # Verify specific options exist
        option_map = {opt.key: opt.description for opt in menu.options}
        
        # Should have unified site management
        self.assertEqual(option_map["4"], "Site Management")
        
        # Should have GitHub settings (moved from deployment)
        self.assertEqual(option_map["6"], "GitHub settings")
        
        # Should NOT have redundant options
        self.assertNotIn("6", [opt.key for opt in menu.options if opt.description == "GitHub deployment"])
        self.assertNotIn("7", [opt.key for opt in menu.options if opt.description == "Update site from GitHub"])
    
    @patch('src.kurserver.managers.nginx.is_package_installed')
    @patch('src.kurserver.managers.nginx.Menu')
    def test_site_management_menu_integration(self, mock_menu, mock_installed):
        """Test that site management menu is properly integrated."""
        mock_installed.return_value = True
        
        from src.kurserver.managers.nginx import site_management_menu
        site_management_menu()
        
        # Verify menu was called
        mock_menu.assert_called_once()
        args, kwargs = mock_menu.call_args
        
        # Check menu title
        self.assertEqual(kwargs['title'], "Site Management")
        
        # Check options count (7 instead of 8)
        options = args[0]
        self.assertEqual(len(options), 7)
        
        # Verify specific options
        option_map = {opt.key: opt.description for opt in options}
        self.assertEqual(option_map["1"], "Add new website")
        self.assertEqual(option_map["3"], "Update existing site")  # Updated from "Update deployment"
        
        # Should NOT have old option
        self.assertNotIn("7", [opt.key for opt in options if opt.description == "Update deployment"])
    
    @patch('src.kurserver.managers.github_settings.Menu')
    def test_github_settings_integration(self, mock_menu):
        """Test that GitHub settings menu is properly integrated."""
        from src.kurserver.managers.github_settings import github_settings_menu
        github_settings_menu()
        
        # Verify menu was called
        mock_menu.assert_called_once()
        args, kwargs = mock_menu.call_args
        
        # Check menu title
        self.assertEqual(kwargs['title'], "GitHub Settings")
        
        # Check options count (4)
        options = args[0]
        self.assertEqual(len(options), 4)
        
        # Verify specific options
        option_map = {opt.key: opt.description for opt in options}
        self.assertEqual(option_map["1"], "Configure GitHub access token")
        self.assertEqual(option_map["2"], "List all deployments")
        self.assertEqual(option_map["3"], "Remove deployment configuration")
        self.assertEqual(option_map["4"], "Test GitHub connection")
    
    def test_github_token_persistence(self):
        """Test that GitHub token configuration persists correctly."""
        from src.kurserver.managers.github_settings import _store_github_token, _get_stored_github_token
        
        # Store a token
        test_token = "ghp_test_token_12345"
        _store_github_token(test_token)
        
        # Verify file was created
        config_file = os.path.join(self.config_dir, "config.json")
        self.assertTrue(os.path.exists(config_file))
        
        # Verify file permissions
        file_stat = os.stat(config_file)
        # Check that file has restricted permissions (0o600)
        self.assertEqual(oct(file_stat.st_mode)[-3:], "600")
        
        # Verify content
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config['github_token'], test_token)
        
        # Verify retrieval
        retrieved_token = _get_stored_github_token()
        self.assertEqual(retrieved_token, test_token)
    
    def test_deployment_info_persistence(self):
        """Test that deployment information persists correctly."""
        from src.kurserver.deployment.github import _save_deployment_info, _get_deployments
        
        # Save deployment info
        domain = "test.example.com"
        repo_url = "https://github.com/user/repo.git"
        branch = "main"
        web_root = "/var/www/test.example.com"
        is_private = True
        
        _save_deployment_info(domain, repo_url, branch, web_root, is_private)
        
        # Verify file was created
        deployments_file = os.path.join(self.config_dir, "deployments", "github.json")
        self.assertTrue(os.path.exists(deployments_file))
        
        # Verify content
        deployments = _get_deployments()
        self.assertIn(domain, deployments)
        
        deployment = deployments[domain]
        self.assertEqual(deployment['repo_url'], repo_url)
        self.assertEqual(deployment['branch'], branch)
        self.assertEqual(deployment['web_root'], web_root)
        self.assertEqual(deployment['private'], is_private)
        self.assertIn('last_updated', deployment)
    
    @patch('src.kurserver.managers.github_settings.get_user_input')
    @patch('src.kurserver.managers.github_settings.confirm_action')
    @patch('src.kurserver.managers.github_settings._validate_github_token')
    def test_github_token_validation_flow(self, mock_validate, mock_confirm, mock_input):
        """Test GitHub token validation flow."""
        from src.kurserver.managers.github_settings import configure_github_token
        
        # Setup mocks
        mock_input.return_value = "test_token"
        mock_validate.return_value = True
        mock_confirm.return_value = True
        
        # Call function
        configure_github_token()
        
        # Verify flow
        mock_input.assert_called_with("Enter GitHub personal access token", password=True)
        mock_validate.assert_called_with("test_token")
        mock_confirm.assert_called()
    
    @patch('subprocess.run')
    def test_git_safe_directory_fix(self, mock_run):
        """Test that Git safe directory is set to fix ownership issues."""
        from src.kurserver.deployment.github import _update_deployment
        
        # Setup deployment
        deployment = {
            'web_root': '/var/www/test.com',
            'repo_url': 'https://github.com/user/repo.git',
            'branch': 'main',
            'private': False
        }
        
        # Call update function
        _update_deployment(deployment, "pull", verbose=False)
        
        # Verify that git config was called
        git_calls = [call for call in mock_run.call_args_list 
                    if len(call[0][0]) > 1 and call[0][0][1] == 'config']
        
        self.assertTrue(len(git_calls) > 0, "Git config should be called to set safe directory")
        
        # Check that safe directory was set
        safe_dir_calls = [call for call in git_calls 
                        if len(call[0][0]) > 3 and 'safe.directory' in call[0][0]]
        self.assertTrue(len(safe_dir_calls) > 0, "Safe directory should be configured")


if __name__ == '__main__':
    unittest.main()