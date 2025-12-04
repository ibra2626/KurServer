"""
PHP-FPM uninstaller for KurServer CLI.
"""

import os
import subprocess
import json
from typing import List, Optional

from .base import BaseUninstaller
from ..core.system import is_package_installed
from ..utils.package import purge_package_config
from ..core.logger import get_logger

logger = get_logger()


class PHPUninstaller(BaseUninstaller):
    """PHP-FPM uninstaller with configuration backup functionality."""
    
    def __init__(self, version: str):
        """
        Initialize PHP uninstaller.
        
        Args:
            version (str): PHP version (e.g., "8.1", "8.2")
        """
        super().__init__(f"php{version}")
        self.version = version
        self.php_package = f"php{version}-fpm"
    
    def get_package_names(self) -> List[str]:
        """
        Get list of packages to uninstall.
        
        Returns:
            List[str]: List of package names
        """
        packages = [self.php_package]
        
        # Add common PHP extensions for this version
        common_extensions = [
            f"php{self.version}-mysql",
            f"php{self.version}-xml",
            f"php{self.version}-mbstring",
            f"php{self.version}-curl",
            f"php{self.version}-zip",
            f"php{self.version}-gd",
            f"php{self.version}-intl",
            f"php{self.version}-bcmath",
            f"php{self.version}-json",
            f"php{self.version}-opcache",
            f"php{self.version}-cli",
            f"php{self.version}-common"
        ]
        
        # Check which extensions are actually installed
        for ext in common_extensions:
            if is_package_installed(ext):
                packages.append(ext)
        
        return packages
    
    def get_backup_paths(self) -> List[str]:
        """
        Get list of paths to backup.
        
        Returns:
            List[str]: List of paths to backup
        """
        paths = []
        
        # PHP configuration
        php_config_dir = f"/etc/php/{self.version}"
        if os.path.exists(php_config_dir):
            paths.append(php_config_dir)
        
        # PHP-FPM configuration
        fpm_config_dir = f"/etc/php/{self.version}/fpm"
        if os.path.exists(fpm_config_dir):
            paths.append(fpm_config_dir)
        
        # PHP-FPM pool configuration
        pool_dir = f"/etc/php/{self.version}/fpm/pool.d"
        if os.path.exists(pool_dir):
            paths.append(pool_dir)
        
        # PHP mods configuration
        mods_dir = f"/etc/php/{self.version}/mods-available"
        if os.path.exists(mods_dir):
            paths.append(mods_dir)
        
        # PHP-FPM log files
        log_file = f"/var/log/php{self.version}-fpm.log"
        if os.path.exists(log_file):
            paths.append(log_file)
        
        # PHP session directory
        session_dir = "/var/lib/php/sessions"
        if os.path.exists(session_dir):
            paths.append(session_dir)
        
        # PHP-FPM socket
        socket_dir = "/run/php"
        if os.path.exists(socket_dir):
            paths.append(socket_dir)
        
        return paths
    
    def get_service_names(self) -> List[str]:
        """
        Get list of services to manage.
        
        Returns:
            List[str]: List of service names
        """
        return [self.php_package]
    
    def pre_uninstall_checks(self, verbose: bool = False) -> bool:
        """
        Perform pre-uninstallation checks.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if checks pass, False otherwise
        """
        try:
            if verbose:
                logger.info(f"Performing PHP {self.version} pre-uninstallation checks...")
            
            # Check if PHP-FPM is installed
            if not is_package_installed(self.php_package):
                logger.warning(f"PHP {self.version}-FPM is not installed")
                return False
            
            # Check if other PHP versions are installed
            other_versions = []
            for version in ["7.4", "8.0", "8.1", "8.2", "8.3"]:
                if version != self.version and is_package_installed(f"php{version}-fpm"):
                    other_versions.append(version)
            
            if other_versions and verbose:
                logger.info(f"Other PHP versions installed: {', '.join(other_versions)}")
            
            # Check disk space for backup
            backup_paths = self.get_backup_paths()
            total_size = 0
            
            for path in backup_paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        total_size += os.path.getsize(path)
                    elif os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                total_size += os.path.getsize(os.path.join(root, file))
            
            # Check available disk space (minimum 200MB for PHP backup)
            try:
                stat = os.statvfs("/")
                available_space = stat.f_bavail * stat.f_frsize
                
                if available_space < total_size + 200 * 1024 * 1024:  # 200MB buffer
                    logger.error("Insufficient disk space for backup")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")
            
            if verbose:
                logger.info(f"PHP {self.version} pre-uninstallation checks passed")
            
            return True
            
        except Exception as e:
            logger.error(f"Pre-uninstallation checks failed: {e}")
            return False
    
    def post_uninstall_cleanup(self, verbose: bool = False) -> bool:
        """
        Perform post-uninstallation cleanup.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            if verbose:
                logger.info(f"Performing PHP {self.version} post-uninstallation cleanup...")
            
            # Clean up any remaining package configurations
            for package in self.get_package_names():
                purge_package_config(package, verbose)
            
            # Remove remaining PHP directories
            cleanup_dirs = [
                f"/etc/php/{self.version}",
                f"/var/log/php{self.version}-fpm.log",
                f"/run/php/php{self.version}-fpm.sock",
                f"/var/lib/php/modules/{self.version}"
            ]
            
            for dir_path in cleanup_dirs:
                if os.path.exists(dir_path):
                    if verbose:
                        logger.info(f"Removing {dir_path}")
                    
                    subprocess.run(
                        ["sudo", "rm", "-rf", dir_path],
                        capture_output=True
                    )
            
            # Clean up PHP session files for this version
            session_dir = "/var/lib/php/sessions"
            if os.path.exists(session_dir):
                try:
                    for file in os.listdir(session_dir):
                        if file.startswith(f"sess_php{self.version}"):
                            session_file = os.path.join(session_dir, file)
                            if verbose:
                                logger.info(f"Removing session file: {session_file}")
                            
                            subprocess.run(
                                ["sudo", "rm", "-f", session_file],
                                capture_output=True
                            )
                except Exception as e:
                    logger.warning(f"Could not clean up session files: {e}")
            
            if verbose:
                logger.info(f"PHP {self.version} post-uninstallation cleanup completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Post-uninstallation cleanup failed: {e}")
            return False
    
    def get_php_info(self, verbose: bool = False) -> dict:
        """
        Get comprehensive PHP information before uninstallation.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            dict: Dictionary with PHP information
        """
        info = {
            'version': self.version,
            'installed': is_package_installed(self.php_package),
            'extensions': [],
            'config_files': [],
            'fpm_config': {},
            'service_status': 'unknown',
            'socket_path': f"/run/php/php{self.version}-fpm.sock"
        }
        
        if not info['installed']:
            return info
        
        try:
            # Get PHP version
            try:
                result = subprocess.run([
                    f"php{self.version}", "-v"
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    if "PHP " in version_line:
                        info['full_version'] = version_line.split('PHP ')[1]
                        
            except Exception:
                pass
            
            # Get installed extensions
            try:
                result = subprocess.run([
                    f"php{self.version}", "-m"
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    extensions = [ext.strip() for ext in result.stdout.strip().split('\n') if ext.strip()]
                    info['extensions'] = extensions
                    
            except Exception:
                pass
            
            # Get configuration files
            config_dir = f"/etc/php/{self.version}"
            if os.path.exists(config_dir):
                for root, dirs, files in os.walk(config_dir):
                    for file in files:
                        if file.endswith('.ini') or file.endswith('.conf'):
                            info['config_files'].append(os.path.join(root, file))
            
            # Get FPM configuration
            fpm_config_file = f"/etc/php/{self.version}/fpm/php-fpm.conf"
            if os.path.exists(fpm_config_file):
                try:
                    with open(fpm_config_file, 'r') as f:
                        content = f.read()
                        
                    # Parse some key FPM settings
                    import re
                    for line in content.split('\n'):
                        line = line.strip()
                        if '=' in line and not line.startswith(';'):
                            key, value = line.split('=', 1)
                            info['fpm_config'][key.strip()] = value.strip()
                            
                except Exception:
                    pass
            
            # Get service status
            try:
                result = subprocess.run([
                    "systemctl", "is-active", self.php_package
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    info['service_status'] = 'active'
                else:
                    info['service_status'] = 'inactive'
                    
            except Exception:
                pass
            
            if verbose:
                logger.info(f"PHP {self.version} info: {info}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PHP {self.version} info: {e}")
            return info
    
    def create_detailed_backup(self, verbose: bool = False) -> bool:
        """
        Create detailed backup with additional information.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                logger.info(f"Creating detailed PHP {self.version} backup...")
            
            # Get PHP information
            php_info = self.get_php_info(verbose)
            
            # Create standard backup
            backup_path = self.create_backup(verbose)
            
            if not backup_path:
                return False
            
            # Create additional info file
            info_path = backup_path.replace('.tar.gz', '_info.json')
            
            with open(info_path, 'w') as f:
                json.dump(php_info, f, indent=2)
            
            # Add info file to backup
            import tarfile
            with tarfile.open(backup_path, "a:gz") as tar:
                tar.add(info_path, arcname="php_info.json")
            
            # Remove temporary info file
            os.remove(info_path)
            
            if verbose:
                logger.info(f"Detailed PHP {self.version} backup created: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create detailed backup: {e}")
            return False
    
    def get_installed_extensions(self, verbose: bool = False) -> List[str]:
        """
        Get list of installed extensions for this PHP version.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            List[str]: List of installed extensions
        """
        try:
            if verbose:
                logger.info(f"Getting installed extensions for PHP {self.version}...")
            
            result = subprocess.run([
                f"php{self.version}", "-m"
            ], 
            capture_output=True,
            text=True
            )
            
            if result.returncode == 0:
                extensions = [ext.strip() for ext in result.stdout.strip().split('\n') if ext.strip()]
                
                if verbose:
                    logger.info(f"Found {len(extensions)} extensions")
                
                return extensions
            else:
                logger.error(f"Failed to get extensions: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting extensions: {e}")
            return []
    
    def show_restart_warning(self, component_name: str, verbose: bool = False) -> None:
        """
        Show warning to restart operating system after component removal.
        
        Args:
            component_name (str): Name of the component being uninstalled
            verbose (bool): Enable verbose output
        """
        try:
            if verbose:
                logger.info("Displaying restart warning...")
            
            console = __import__('rich.console').console.Console()
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print(f"[yellow]After removing PHP {self.version}-FPM, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
            console.print()
            
        except Exception as e:
            logger.error(f"Failed to display restart warning: {e}")