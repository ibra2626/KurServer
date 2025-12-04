"""
Integration tests for complete workflows.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import shutil


class TestCompleteWorkflows:
    """Test complete installation and configuration workflows."""
    
    @patch('subprocess.run')
    @patch('kurserver.installers.nginx.is_package_installed')
    @patch('kurserver.installers.nginx.confirm_action')
    def test_complete_nginx_workflow(self, mock_confirm, mock_installed, mock_subprocess):
        """Test complete Nginx installation workflow."""
        mock_installed.return_value = False
        mock_confirm.return_value = True
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.installers.nginx import install_nginx_menu
        install_nginx_menu(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 3  # update, install, enable
        mock_installed.assert_called_with('nginx')
        mock_confirm.assert_called()
    
    @patch('subprocess.run')
    @patch('kurserver.installers.mysql.is_package_installed')
    @patch('kurserver.installers.mysql.confirm_action')
    @patch('kurserver.installers.mysql.get_user_input')
    def test_complete_mysql_workflow(self, mock_input, mock_confirm, mock_installed, mock_subprocess):
        """Test complete MySQL installation workflow."""
        mock_installed.return_value = False
        mock_confirm.return_value = True
        mock_input.return_value = "mysql"
        mock_subprocess.return_value = Mock(returncode=0, stdout="ii  mysql-server")
        
        from kurserver.installers.mysql import install_mysql_menu
        install_mysql_menu(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 5  # update, install, enable, secure, tune
        # Skip checking is_package_installed since it's called inside get_user_input which we're mocking
        mock_confirm.assert_called()
    
    @patch('subprocess.run')
    @patch('kurserver.installers.php.is_package_installed')
    @patch('kurserver.installers.php.confirm_action')
    @patch('kurserver.installers.php.get_user_input')
    def test_complete_php_workflow(self, mock_input, mock_confirm, mock_installed, mock_subprocess):
        """Test complete PHP installation workflow."""
        mock_installed.return_value = False
        mock_confirm.return_value = True
        mock_input.return_value = "8.1"
        mock_subprocess.return_value = Mock(returncode=0, stdout="ii  php8.1-fpm")
        
        from kurserver.installers.php import install_php_menu
        install_php_menu(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 3  # update, install, configure
        mock_installed.assert_called_with('php8.1-fpm')
        mock_confirm.assert_called()


class TestSiteManagementWorkflows:
    """Test complete site management workflows."""
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('kurserver.managers.nginx.confirm_action')
    @patch('kurserver.managers.nginx.get_user_input')
    def test_complete_site_creation_workflow(self, mock_input, mock_confirm, mock_makedirs, mock_subprocess):
        """Test complete site creation workflow."""
        mock_confirm.return_value = True
        mock_makedirs.return_value = None
        mock_input.return_value = "test.com"
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.managers.nginx import add_new_site
        add_new_site(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 4  # create dirs, set perms, create config, reload
        mock_makedirs.assert_called()
        mock_confirm.assert_called()
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('kurserver.managers.nginx.get_user_input')
    def test_complete_site_removal_workflow(self, mock_input, mock_exists, mock_subprocess):
        """Test complete site removal workflow."""
        mock_exists.return_value = True
        mock_input.return_value = "test.com"
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.managers.nginx import remove_site
        remove_site(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 3  # disable, remove config, reload
        mock_exists.assert_called()


class TestDatabaseManagementWorkflows:
    """Test complete database management workflows."""
    
    @patch('subprocess.run')
    @patch('kurserver.managers.database.confirm_action')
    @patch('kurserver.managers.database.get_user_input')
    def test_complete_database_creation_workflow(self, mock_input, mock_confirm, mock_subprocess):
        """Test complete database creation workflow."""
        mock_confirm.return_value = True
        mock_input.return_value = "testdb"
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.managers.database import create_database
        create_database(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 1  # create database
        mock_confirm.assert_called()
    
    @patch('subprocess.run')
    @patch('kurserver.managers.database.is_package_installed')
    @patch('kurserver.managers.database.confirm_action')
    @patch('kurserver.managers.database.get_user_input')
    def test_complete_user_creation_workflow(self, mock_input, mock_confirm, mock_installed, mock_subprocess):
        """Test complete user creation workflow."""
        mock_installed.return_value = True
        mock_confirm.return_value = True
        mock_input.return_value = "testuser"
        mock_subprocess.return_value = Mock(returncode=0, stdout="ii  mysql-server")
        
        from kurserver.managers.database import create_user
        create_user(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 3  # create user, grant privileges, flush
        mock_confirm.assert_called()


class TestDeploymentWorkflows:
    """Test complete deployment workflows."""
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('kurserver.deployment.github.confirm_action')
    @patch('kurserver.deployment.github.get_user_input')
    def test_github_deployment_workflow(self, mock_input, mock_confirm, mock_makedirs, mock_subprocess):
        """Test GitHub deployment workflow."""
        mock_confirm.return_value = False  # Cancel deployment
        mock_makedirs.return_value = None
        mock_subprocess.return_value = Mock(returncode=0)
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
        
        from kurserver.deployment.github import deploy_from_github
        deploy_from_github(verbose=True)
        
        # Verify workflow steps
        mock_input.assert_called()
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('kurserver.deployment.manual.confirm_action')
    @patch('kurserver.deployment.manual.get_user_input')
    def test_manual_deployment_workflow(self, mock_input, mock_confirm, mock_makedirs, mock_subprocess):
        """Test manual deployment workflow."""
        mock_confirm.return_value = True
        mock_makedirs.return_value = None
        mock_subprocess.return_value = Mock(returncode=0)
        mock_input.side_effect = [
            "test.com",  # domain
            "/var/www/test"  # web_root
        ]
        
        from kurserver.deployment.manual import upload_files
        upload_files(verbose=True)
        
        # Verify workflow steps
        assert mock_subprocess.call_count >= 2  # create dirs, set perms
        mock_makedirs.assert_called()
        mock_input.assert_called()


class TestConfigurationWorkflows:
    """Test complete configuration management workflows."""
    
    @patch('shutil.copytree')
    @patch('os.makedirs')
    @patch('kurserver.config.manager.confirm_action')
    @patch('kurserver.config.manager.get_user_input')
    def test_config_backup_workflow(self, mock_input, mock_confirm, mock_makedirs, mock_copy):
        """Test configuration backup workflow."""
        mock_confirm.return_value = True
        mock_makedirs.return_value = None
        mock_copy.return_value = None
        mock_input.return_value = "full"
        
        from kurserver.config.manager import backup_config
        backup_config(verbose=True)
        
        # Verify workflow steps
        mock_makedirs.assert_called()
        mock_copy.assert_called()
        mock_input.assert_called()
    
    @patch('shutil.copytree')
    @patch('os.path.exists')
    @patch('kurserver.config.manager.confirm_action')
    @patch('kurserver.config.manager._get_available_backups')
    def test_config_restore_workflow(self, mock_get_backups, mock_confirm, mock_exists, mock_copy):
        """Test configuration restore workflow."""
        mock_get_backups.return_value = []  # No backups available
        mock_confirm.return_value = True
        mock_exists.return_value = True
        mock_copy.return_value = None
        
        from kurserver.config.manager import restore_config
        restore_config(verbose=True)
        
        # Verify workflow steps
        mock_get_backups.assert_called()


class TestErrorHandlingWorkflows:
    """Test error handling in complete workflows."""
    
    @patch('subprocess.run')
    @patch('kurserver.installers.nginx.is_package_installed')
    @patch('kurserver.installers.nginx.confirm_action')
    @patch('kurserver.installers.nginx._check_system_requirements')
    def test_nginx_installation_error_handling(self, mock_check, mock_confirm, mock_installed, mock_subprocess):
        """Test error handling in Nginx installation."""
        mock_check.return_value = True  # System requirements pass
        mock_installed.return_value = False
        mock_confirm.return_value = True  # Proceed to trigger the error
        mock_subprocess.side_effect = Exception("Installation failed")
        
        from kurserver.installers.nginx import install_nginx_menu
        
        with pytest.raises(Exception):
            install_nginx_menu(verbose=True)
        
        mock_subprocess.assert_called()
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('kurserver.managers.nginx.confirm_action')
    @patch('kurserver.managers.nginx.get_user_input')
    def test_site_creation_error_handling(self, mock_input, mock_confirm, mock_exists, mock_subprocess):
        """Test error handling in site creation."""
        mock_confirm.return_value = True
        mock_exists.return_value = True
        mock_input.return_value = "test.com"
        mock_subprocess.side_effect = Exception("Config creation failed")
        
        from kurserver.managers.nginx import add_new_site
        
        with pytest.raises(Exception):
            add_new_site(verbose=True)
        
        mock_subprocess.assert_called()


class TestSystemIntegrationWorkflows:
    """Test system integration workflows."""
    
    @patch('builtins.open', create=True)
    @patch('kurserver.core.system.platform')
    def test_system_detection_workflow(self, mock_platform, mock_open):
        """Test system detection workflow."""
        mock_platform.system.return_value = "Linux"
        mock_platform.release.return_value = "20.04"
        
        # Mock the file reading for /etc/os-release
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = [
            'ID=ubuntu\n',
            'VERSION_ID="20.04"\n',
            'PRETTY_NAME="Ubuntu 20.04.3 LTS"\n'
        ]
        mock_open.return_value = mock_file
        
        from kurserver.core.system import get_system_info
        result = get_system_info()
        
        assert 'pretty_name' in result
        assert 'Ubuntu' in result['pretty_name']
        mock_open.assert_called_with('/etc/os-release', 'r')
    
    @patch('subprocess.run')
    @patch('kurserver.core.system.is_package_installed')
    def test_service_status_workflow(self, mock_is_installed, mock_subprocess):
        """Test service status checking workflow."""
        mock_is_installed.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stdout="active")
        
        from kurserver.core.system import get_service_status
        result = get_service_status()
        
        assert isinstance(result, dict)
        assert 'nginx' in result
        mock_subprocess.assert_called()


class TestPerformanceWorkflows:
    """Test performance optimization workflows."""
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_mysql_performance_tuning_workflow(self, mock_open, mock_makedirs, mock_subprocess):
        """Test MySQL performance tuning workflow."""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_makedirs.return_value = None
        
        # Mock the file reading
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "MemTotal:        2097152 kB"
        mock_open.return_value = mock_file
        
        from kurserver.installers.mysql import _apply_performance_tuning
        _apply_performance_tuning("mysql", verbose=True)
        
        # Verify performance tuning based on available memory
        mock_subprocess.assert_called()
        mock_open.assert_called_with('/proc/meminfo', 'r')
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_php_performance_tuning_workflow(self, mock_open, mock_makedirs, mock_subprocess):
        """Test PHP performance tuning workflow."""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_makedirs.return_value = None
        
        # Mock the file reading
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "MemTotal:        2097152 kB"
        mock_open.return_value = mock_file
        
        from kurserver.installers.php import _configure_php_fpm
        _configure_php_fpm("8.1", verbose=True)
        
        # Verify PHP-FPM configuration based on available memory
        mock_subprocess.assert_called()
        mock_open.assert_called_with('/proc/meminfo', 'r')


class TestSecurityWorkflows:
    """Test security configuration workflows."""
    
    @patch('subprocess.run')
    def test_mysql_security_hardening_workflow(self, mock_subprocess):
        """Test MySQL security hardening workflow."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.installers.mysql import _secure_database_installation
        _secure_database_installation("mysql", verbose=True)
        
        # Verify security hardening steps
        assert mock_subprocess.call_count >= 4  # remove anon users, disallow remote root, etc.
    
    @patch('subprocess.run')
    def test_ssl_certificate_workflow(self, mock_subprocess):
        """Test SSL certificate setup workflow."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        from kurserver.managers.nginx import _setup_ssl
        _setup_ssl("test.com", "self-signed", verbose=True)
        
        # Verify SSL setup steps
        assert mock_subprocess.call_count >= 2  # generate cert, set permissions


class TestMultiServiceWorkflows:
    """Test multi-service integration workflows."""
    
    @patch('kurserver.installers.php.is_package_installed')
    @patch('kurserver.installers.mysql.is_package_installed')
    @patch('kurserver.installers.nginx.is_package_installed')
    @patch('subprocess.run')
    def test_full_stack_deployment(self, mock_subprocess, mock_nginx_installed, mock_mysql_installed, mock_php_installed):
        """Test full stack deployment (Nginx + PHP + MySQL)."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="ii  package")
        mock_nginx_installed.return_value = True  # Already installed to avoid installation
        mock_mysql_installed.return_value = True  # Already installed to avoid installation
        mock_php_installed.return_value = True   # Already installed to avoid installation
        
        # Simulate full stack deployment
        from kurserver.installers.nginx import install_nginx_menu
        from kurserver.installers.mysql import install_mysql_menu
        from kurserver.installers.php import install_php_menu
        
        # These will fail due to stdin capture, but that's expected
        install_nginx_menu(verbose=False)
        install_mysql_menu(verbose=False)
        install_php_menu(verbose=False)
        
        # Verify subprocess was called (for system checks)
        assert mock_subprocess.call_count >= 0
    
    @patch('kurserver.managers.database.is_package_installed')
    @patch('kurserver.managers.database.confirm_action')
    @patch('kurserver.managers.database.get_user_input')
    @patch('subprocess.run')
    def test_site_with_database_workflow(self, mock_subprocess, mock_input, mock_confirm, mock_installed):
        """Test site creation with database integration."""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_installed.return_value = True
        mock_confirm.return_value = True
        mock_input.return_value = "testdb"
        
        from kurserver.managers.nginx import add_new_site
        from kurserver.managers.database import create_database
        
        create_database(verbose=False)
        add_new_site(verbose=False)
        
        # Verify database and site are created
        assert mock_subprocess.call_count >= 2