"""
Unit tests for installer modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestNginxInstaller:
    """Test Nginx installer functionality."""
    
    @patch('kurserver.installers.nginx._install_nginx')
    @patch('kurserver.installers.nginx.confirm_action')
    @patch('kurserver.installers.nginx.is_package_installed')
    def test_nginx_installation(self, mock_is_installed, mock_confirm, mock_install):
        """Test Nginx installation process."""
        mock_is_installed.return_value = False
        mock_confirm.return_value = True
        mock_install.return_value = None
        
        from kurserver.installers.nginx import install_nginx_menu
        install_nginx_menu(verbose=False)
        
        mock_confirm.assert_called()
        mock_install.assert_called_once()
    
    def test_nginx_configuration(self):
        """Test Nginx configuration generation."""
        from kurserver.installers.nginx import _generate_nginx_config
        result = _generate_nginx_config("test.com", "/var/www/test", False, False, "8.1")
        
        assert "test.com" in result
        assert "/var/www/test" in result


class TestMySQLInstaller:
    """Test MySQL installer functionality."""
    
    @patch('kurserver.installers.mysql._install_database')
    @patch('kurserver.installers.mysql.confirm_action')
    @patch('kurserver.installers.mysql.get_user_input')
    @patch('kurserver.installers.mysql.is_package_installed')
    def test_mysql_installation(self, mock_is_installed, mock_input, mock_confirm, mock_install):
        """Test MySQL installation process."""
        mock_is_installed.return_value = False
        mock_input.return_value = "mysql"
        mock_confirm.return_value = True
        mock_install.return_value = None
        
        from kurserver.installers.mysql import install_mysql_menu
        install_mysql_menu(verbose=False)
        
        mock_confirm.assert_called()
        mock_install.assert_called_once()
    
    @patch('kurserver.installers.mysql._secure_database_installation')
    def test_mysql_security_setup(self, mock_secure):
        """Test MySQL security setup."""
        mock_secure.return_value = None
        
        from kurserver.installers.mysql import _secure_database_installation
        _secure_database_installation("mysql", verbose=False)
        
        mock_secure.assert_called_once_with("mysql", verbose=False)
    
    @patch('kurserver.installers.mysql._apply_performance_tuning')
    def test_mysql_performance_tuning(self, mock_tune):
        """Test MySQL performance tuning."""
        mock_tune.return_value = None
        
        from kurserver.installers.mysql import _apply_performance_tuning
        _apply_performance_tuning("mysql", verbose=False)
        
        mock_tune.assert_called_once_with("mysql", verbose=False)


class TestPHPInstaller:
    """Test PHP installer functionality."""
    
    @patch('kurserver.installers.php._install_php')
    @patch('kurserver.installers.php.confirm_action')
    @patch('kurserver.installers.php.get_user_input')
    @patch('kurserver.installers.php.is_package_installed')
    def test_php_installation(self, mock_is_installed, mock_input, mock_confirm, mock_install):
        """Test PHP installation process."""
        mock_is_installed.return_value = False
        mock_input.return_value = "8.1"
        mock_confirm.return_value = True
        mock_install.return_value = None
        
        from kurserver.installers.php import install_php_menu
        install_php_menu(verbose=False)
        
        mock_confirm.assert_called()
        mock_install.assert_called_once()
    
    @patch('kurserver.installers.php._install_extensions_interactive')
    def test_php_extension_installation(self, mock_extensions):
        """Test PHP extension installation."""
        mock_extensions.return_value = None
        
        from kurserver.installers.php import _install_extensions_interactive
        _install_extensions_interactive("8.1", verbose=False)
        
        mock_extensions.assert_called_once_with("8.1", verbose=False)
    
    @patch('kurserver.installers.php._configure_php_fpm')
    def test_php_fpm_configuration(self, mock_configure):
        """Test PHP-FPM configuration."""
        mock_configure.return_value = None
        
        from kurserver.installers.php import _configure_php_fpm
        _configure_php_fpm("8.1", verbose=False)
        
        mock_configure.assert_called_once_with("8.1", verbose=False)


class TestInstallerIntegration:
    """Test installer integration functionality."""
    
    @patch('kurserver.installers.nginx.confirm_action')
    @patch('kurserver.installers.nginx.is_package_installed')
    def test_package_detection(self, mock_is_installed, mock_confirm):
        """Test package detection in installers."""
        mock_is_installed.return_value = False
        mock_confirm.return_value = False  # Cancel the installation
        
        from kurserver.installers.nginx import install_nginx_menu
        install_nginx_menu(verbose=False)
        
        # Check that is_package_installed was called for nginx
        mock_is_installed.assert_any_call('nginx')
        # Also check for conflicting servers (httpd, apache2, lighttpd)
        mock_is_installed.assert_any_call('httpd')
    
    @patch('subprocess.run')
    def test_system_command_execution(self, mock_subprocess):
        """Test system command execution in installers."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="success")
        
        from kurserver.installers.php import _install_php
        _install_php("8.1", False, verbose=False)
        
        mock_subprocess.assert_called()
    
    @patch('subprocess.run')
    def test_error_logging(self, mock_subprocess):
        """Test error handling in installers."""
        from kurserver.installers.mysql import _install_database
        
        # Mock subprocess.run to raise an exception
        mock_subprocess.side_effect = [Mock(returncode=0), Exception("Command failed")]
        
        # Test that exception is raised when installation fails
        with pytest.raises(Exception, match="Command failed"):
            _install_database("mysql", verbose=False)
        
        # Verify subprocess was called for apt update
        mock_subprocess.assert_called()