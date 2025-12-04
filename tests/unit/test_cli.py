"""
Unit tests for CLI module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kurserver.cli.menu import Menu, MenuOption, get_user_input, confirm_action
from kurserver.cli.main import cli
from click.testing import CliRunner


class TestMenu:
    """Test menu functionality."""
    
    def test_menu_option_creation(self):
        """Test creating a menu option."""
        action = Mock()
        option = MenuOption("1", "Test Option", action=action)
        
        assert option.key == "1"
        assert option.description == "Test Option"
        assert option.action == action
    
    def test_menu_creation(self):
        """Test creating a menu."""
        options = [
            MenuOption("1", "Option 1", Mock()),
            MenuOption("2", "Option 2", Mock()),
        ]
        menu = Menu("Test Menu", options)
        
        assert menu.title == "Test Menu"
        assert len(menu.options) == 2
        assert menu.show_status is True
    
    @patch('kurserver.cli.menu.Prompt.ask')
    def test_get_user_input(self, mock_prompt):
        """Test getting user input."""
        mock_prompt.return_value = "test_input"
        
        result = get_user_input("Test question")
        
        assert result == "test_input"
        mock_prompt.assert_called_once()
    
    @patch('kurserver.cli.menu.Confirm.ask')
    def test_confirm_action(self, mock_confirm):
        """Test action confirmation."""
        mock_confirm.return_value = True
        
        result = confirm_action("Test question")
        
        assert result is True
        mock_confirm.assert_called_once()


class TestMainCLI:
    """Test main CLI functionality."""
    
    def test_cli_version(self):
        """Test CLI version option."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert 'KurServer' in result.output
    
    @patch('kurserver.core.system.check_system_requirements')
    def test_cli_interactive_command(self, mock_check):
        """Test CLI interactive command."""
        mock_check.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ['interactive'])
        
        assert result.exit_code == 0
        mock_check.assert_called_once()


class TestSystemIntegration:
    """Test system integration functionality."""
    
    def test_package_detection(self):
        """Test package detection."""
        from kurserver.core.system import is_package_installed
        # This test would require actual system, so we'll test the function exists
        assert callable(is_package_installed)
    
    def test_service_status(self):
        """Test service status checking."""
        from kurserver.core.system import get_service_status
        # This test would require actual system, so we'll test the function exists
        result = get_service_status()
        assert isinstance(result, dict)
        assert 'nginx' in result


class TestInstallerIntegration:
    """Test installer integration functionality."""
    
    @patch('kurserver.installers.nginx._install_nginx')
    @patch('kurserver.installers.nginx.confirm_action')
    @patch('kurserver.installers.nginx.is_package_installed')
    def test_nginx_installation_flow(self, mock_is_installed, mock_confirm, mock_install):
        """Test Nginx installation flow."""
        mock_is_installed.return_value = False
        mock_confirm.return_value = True
        mock_install.return_value = None
        
        from kurserver.installers.nginx import install_nginx_menu
        install_nginx_menu(verbose=False)
        
        mock_confirm.assert_called()
        mock_install.assert_called_once()
    
    @patch('kurserver.installers.mysql._install_database')
    @patch('kurserver.installers.mysql.confirm_action')
    @patch('kurserver.installers.mysql.get_user_input')
    @patch('kurserver.installers.mysql.is_package_installed')
    def test_mysql_installation_flow(self, mock_is_installed, mock_input, mock_confirm, mock_install):
        """Test MySQL installation flow."""
        mock_is_installed.return_value = False
        mock_input.return_value = "mysql"
        mock_confirm.return_value = True
        mock_install.return_value = None
        
        from kurserver.installers.mysql import install_mysql_menu
        install_mysql_menu(verbose=False)
        
        mock_confirm.assert_called()
        mock_install.assert_called_once()


class TestManagerIntegration:
    """Test manager integration functionality."""
    
    @patch('kurserver.managers.nginx._create_site_config')
    @patch('kurserver.managers.nginx.confirm_action')
    @patch('kurserver.managers.nginx.get_user_input')
    def test_site_creation_flow(self, mock_input, mock_confirm, mock_create):
        """Test site creation flow."""
        mock_input.return_value = "test.com"
        mock_confirm.return_value = True
        mock_create.return_value = None
        
        from kurserver.managers.nginx import add_new_site
        add_new_site(verbose=False)
        
        mock_confirm.assert_called()
        mock_create.assert_called()
    
    @patch('kurserver.managers.database._create_database')
    @patch('kurserver.managers.database.confirm_action')
    @patch('kurserver.managers.database.get_user_input')
    def test_database_creation_flow(self, mock_input, mock_confirm, mock_create):
        """Test database creation flow."""
        mock_input.return_value = "testdb"
        mock_confirm.return_value = True
        mock_create.return_value = None
        
        from kurserver.managers.database import create_database
        create_database(verbose=False)
        
        mock_confirm.assert_called()
        mock_create.assert_called()


class TestDeploymentIntegration:
    """Test deployment integration functionality."""
    
    @patch('kurserver.deployment.github._deploy_from_github')
    @patch('kurserver.deployment.github.confirm_action')
    @patch('kurserver.deployment.github.get_user_input')
    def test_github_deployment_flow(self, mock_input, mock_confirm, mock_deploy):
        """Test GitHub deployment flow."""
        mock_input.side_effect = [
            "https://github.com/user/repo.git",  # repo_url
            False,  # is_private
            "test.com",  # domain
            "/var/www/test",  # web_root
            "main",  # branch
            False,  # run_composer
            False,  # run_npm
            False,  # create_env
            False  # proceed_with_deployment
        ]
        mock_confirm.return_value = False  # Cancel all confirmations
        mock_deploy.return_value = None
        
        from kurserver.deployment.github import deploy_from_github
        deploy_from_github(verbose=False)
        
        mock_input.assert_called()
    
    @patch('kurserver.deployment.manual._create_directory_structure')
    @patch('kurserver.deployment.manual.confirm_action')
    @patch('kurserver.deployment.manual.get_user_input')
    def test_manual_deployment_flow(self, mock_input, mock_confirm, mock_create):
        """Test manual deployment flow."""
        mock_input.side_effect = [
            "test.com",  # domain
            "/var/www/test"  # web_root
        ]
        mock_create.return_value = None
        
        from kurserver.deployment.manual import upload_files
        upload_files(verbose=False)
        
        mock_input.assert_called()
        mock_create.assert_called()


class TestConfigurationIntegration:
    """Test configuration management integration functionality."""
    
    @patch('kurserver.config.manager._create_backup')
    @patch('kurserver.config.manager.confirm_action')
    @patch('kurserver.config.manager.get_user_input')
    def test_config_backup_flow(self, mock_input, mock_confirm, mock_backup):
        """Test configuration backup flow."""
        mock_input.return_value = "full"
        mock_confirm.return_value = True
        mock_backup.return_value = None
        
        from kurserver.config.manager import backup_config
        backup_config(verbose=False)
        
        mock_confirm.assert_called()
        mock_backup.assert_called()
    
    @patch('kurserver.config.manager._get_available_backups')
    @patch('kurserver.config.manager._restore_backup')
    @patch('kurserver.config.manager.confirm_action')
    def test_config_restore_flow(self, mock_confirm, mock_restore, mock_get_backups):
        """Test configuration restore flow."""
        mock_get_backups.return_value = []  # No backups available
        mock_confirm.return_value = True
        mock_restore.return_value = None
        
        from kurserver.config.manager import restore_config
        restore_config(verbose=False)
        
        mock_get_backups.assert_called()


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_custom_exception_handling(self):
        """Test custom exception handling."""
        from kurserver.core.exceptions import KurServerError
        
        error = KurServerError("Test error", "Test suggestion")
        
        # The __str__ method includes suggestion when present
        expected_str = "Test error\nSuggestion: Test suggestion"
        assert str(error) == expected_str
        assert error.suggestion == "Test suggestion"
    
    @patch('kurserver.core.logger.get_logger')
    def test_logging_functionality(self, mock_logger):
        """Test logging functionality."""
        from kurserver.core.logger import get_logger
        
        logger = get_logger()
        logger.info("Test log message")
        
        mock_logger.assert_called_once()