"""
Unit tests for uninstaller modules."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from kurserver.uninstallers.base import BaseUninstaller
from kurserver.uninstallers.nginx import NginxUninstaller
from kurserver.uninstallers.mysql import MySQLUninstaller
from kurserver.uninstallers.php import PHPUninstaller
from kurserver.utils.backup import BackupManager


class TestBaseUninstaller(unittest.TestCase):
    """Test cases for BaseUninstaller class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing
        class TestUninstaller(BaseUninstaller):
            def get_package_names(self):
                return ['test-package']
            
            def get_backup_paths(self):
                return ['/tmp/test-config']
            
            def get_service_names(self):
                return ['test-service']
            
            def pre_uninstall_checks(self, verbose=False):
                return True
            
            def post_uninstall_cleanup(self, verbose=False):
                return True
        
        self.uninstaller = TestUninstaller('test-component')
    
    def test_init(self):
        """Test uninstaller initialization."""
        self.assertEqual(self.uninstaller.component_name, 'test-component')
        self.assertEqual(self.uninstaller.backup_dir, '/var/lib/kurserver/backups/test-component')
        self.assertIsNotNone(self.uninstaller.backup_manager)
        self.assertIsNotNone(self.uninstaller.logger)
    
    @patch('kurserver.uninstallers.base.BackupManager.create_backup')
    def test_create_backup_success(self, mock_create_backup):
        """Test successful backup creation."""
        mock_create_backup.return_value = '/tmp/test_backup.tar.gz'
        
        result = self.uninstaller.create_backup(verbose=True)
        
        self.assertEqual(result, '/tmp/test_backup.tar.gz')
        mock_create_backup.assert_called_once()
    
    @patch('kurserver.uninstallers.base.subprocess.run')
    def test_stop_services_success(self, mock_run):
        """Test successful service stopping."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'active'
        
        result = self.uninstaller.stop_services(verbose=True)
        
        self.assertTrue(result)
        mock_run.assert_any_call()
    
    @patch('kurserver.uninstallers.base.subprocess.run')
    def test_stop_services_not_running(self, mock_run):
        """Test stopping service that's not running."""
        mock_run.return_value.returncode = 1  # Not active
        
        result = self.uninstaller.stop_services(verbose=True)
        
        self.assertTrue(result)
    
    @patch('kurserver.uninstallers.base.subprocess.run')
    def test_disable_services_success(self, mock_run):
        """Test successful service disabling."""
        mock_run.return_value.returncode = 0
        
        result = self.uninstaller.disable_services(verbose=True)
        
        self.assertTrue(result)
        mock_run.assert_any_call()


class TestNginxUninstaller(unittest.TestCase):
    """Test cases for NginxUninstaller class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.uninstaller = NginxUninstaller()
    
    def test_init(self):
        """Test Nginx uninstaller initialization."""
        self.assertEqual(self.uninstaller.component_name, 'nginx')
    
    def test_get_package_names(self):
        """Test getting package names."""
        packages = self.uninstaller.get_package_names()
        expected_packages = ['nginx', 'nginx-common', 'nginx-core']
        self.assertEqual(set(packages), set(expected_packages))
    
    @patch('os.path.exists')
    def test_get_backup_paths(self, mock_exists):
        """Test getting backup paths."""
        mock_exists.return_value = True
        
        paths = self.uninstaller.get_backup_paths()
        
        expected_paths = [
            '/etc/nginx',
            '/etc/nginx/sites-enabled',
            '/etc/nginx/sites-available',
            '/etc/ssl/certs',
            '/etc/ssl/private',
            '/var/log/nginx',
            '/etc/nginx/conf.d'
        ]
        self.assertEqual(set(paths), set(expected_paths))
    
    def test_get_service_names(self):
        """Test getting service names."""
        services = self.uninstaller.get_service_names()
        self.assertEqual(services, ['nginx'])


class TestMySQLUninstaller(unittest.TestCase):
    """Test cases for MySQLUninstaller class."""
    
    @patch('kurserver.uninstallers.mysql.is_package_installed')
    def test_init_mysql(self, mock_is_installed):
        """Test MySQL uninstaller initialization."""
        mock_is_installed.side_effect = lambda pkg: pkg == 'mysql-server'
        
        uninstaller = MySQLUninstaller()
        
        self.assertEqual(uninstaller.component_name, 'mysql')
        self.assertEqual(uninstaller.db_type, 'mysql')
        self.assertEqual(uninstaller.service_name, 'mysql')
    
    @patch('kurserver.uninstallers.mysql.is_package_installed')
    def test_init_mariadb(self, mock_is_installed):
        """Test MariaDB uninstaller initialization."""
        mock_is_installed.side_effect = lambda pkg: pkg == 'mariadb-server'
        
        uninstaller = MySQLUninstaller()
        
        self.assertEqual(uninstaller.component_name, 'mysql')
        self.assertEqual(uninstaller.db_type, 'mariadb')
        self.assertEqual(uninstaller.service_name, 'mariadb')
    
    @patch('kurserver.uninstallers.mysql.is_package_installed')
    def test_init_no_database(self, mock_is_installed):
        """Test initialization when no database is installed."""
        mock_is_installed.return_value = False
        
        with self.assertRaises(Exception):
            MySQLUninstaller()


class TestPHPUninstaller(unittest.TestCase):
    """Test cases for PHPUninstaller class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.version = '8.1'
        self.uninstaller = PHPUninstaller(self.version)
    
    def test_init(self):
        """Test PHP uninstaller initialization."""
        self.assertEqual(self.uninstaller.component_name, f'php{self.version}')
        self.assertEqual(self.uninstaller.version, self.version)
        self.assertEqual(self.uninstaller.php_package, f'php{self.version}-fpm')
    
    def test_get_package_names(self):
        """Test getting package names."""
        packages = self.uninstaller.get_package_names()
        
        # Should include the main package
        self.assertIn(f'php{self.version}-fpm', packages)
        
        # Should include common extensions
        expected_extensions = [
            f'php{self.version}-mysql',
            f'php{self.version}-xml',
            f'php{self.version}-mbstring',
            f'php{self.version}-curl',
            f'php{self.version}-zip',
            f'php{self.version}-gd',
            f'php{self.version}-intl',
            f'php{self.version}-bcmath',
            f'php{self.version}-json',
            f'php{self.version}-opcache',
            f'php{self.version}-cli',
            f'php{self.version}-common'
        ]
        
        for ext in expected_extensions:
            self.assertIn(ext, packages)
    
    @patch('os.path.exists')
    def test_get_backup_paths(self, mock_exists):
        """Test getting backup paths."""
        mock_exists.return_value = True
        
        paths = self.uninstaller.get_backup_paths()
        
        expected_paths = [
            f'/etc/php/{self.version}',
            f'/etc/php/{self.version}/fpm',
            f'/etc/php/{self.version}/fpm/pool.d',
            f'/etc/php/{self.version}/mods-available',
            f'/var/log/php{self.version}-fpm.log',
            '/var/lib/php/sessions',
            '/run/php'
        ]
        self.assertEqual(set(paths), set(expected_paths))
    
    def test_get_service_names(self):
        """Test getting service names."""
        services = self.uninstaller.get_service_names()
        self.assertEqual(services, [f'php{self.version}-fpm'])


class TestBackupManager(unittest.TestCase):
    """Test cases for BackupManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.component = 'test-component'
        self.backup_manager = BackupManager(self.component)
    
    def test_init(self):
        """Test backup manager initialization."""
        self.assertEqual(self.backup_manager.component_name, self.component)
        self.assertEqual(self.backup_manager.backup_root, '/var/lib/kurserver/backups')
        self.assertEqual(self.backup_manager.backup_dir, f'/var/lib/kurserver/backups/{self.component}')
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('tarfile.open')
    @patch('builtins.open')
    @patch('json.dump')
    @patch('os.chmod')
    def test_create_backup_success(self, mock_chmod, mock_json_dump, mock_open, mock_tarfile, mock_exists, mock_makedirs):
        """Test successful backup creation."""
        mock_exists.return_value = True
        mock_makedirs.return_value = None
        
        # Mock tarfile
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar
        
        result = self.backup_manager.create_backup(['/tmp/test'], verbose=True)
        
        self.assertIsNotNone(result)  # Should return backup path
        mock_makedirs.assert_called_once_with(f'/var/lib/kurserver/backups/{self.component}', exist_ok=True)
        mock_tarfile.assert_called_once()
        mock_json_dump.assert_called_once()
        mock_chmod.assert_called()


class TestSystemIntegration(unittest.TestCase):
    """Test cases for system integration with uninstallation."""
    
    @patch('kurserver.core.system.is_package_installed')
    def test_get_installed_components(self, mock_is_installed):
        """Test getting installed components."""
        from kurserver.core.system import get_installed_components
        
        # Mock different components as installed
        mock_is_installed.side_effect = lambda pkg: pkg in ['nginx', 'mysql-server', 'php8.1-fpm']
        
        components = get_installed_components()
        
        self.assertTrue(components['nginx']['installed'])
        self.assertTrue(components['mysql']['installed'])
        self.assertTrue(components['php']['8.1']['installed'])
        self.assertFalse(components['php']['7.4']['installed'])
    
    @patch('kurserver.core.system.is_package_installed')
    def test_can_uninstall_component(self, mock_is_installed):
        """Test component uninstallation feasibility."""
        from kurserver.core.system import can_uninstall_component
        
        mock_is_installed.side_effect = lambda pkg: pkg in ['nginx', 'php8.1-fpm']
        
        # Test uninstalling nginx when PHP is installed
        result = can_uninstall_component('nginx')
        self.assertTrue(result['can_uninstall'])
        self.assertIn('PHP-FPM is installed', result['warnings'])
        
        # Test uninstalling non-existent component
        result = can_uninstall_component('nonexistent')
        self.assertFalse(result['can_uninstall'])
        self.assertIn('not supported', result['reason'])


if __name__ == '__main__':
    unittest.main()