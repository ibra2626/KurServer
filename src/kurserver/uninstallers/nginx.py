"""
Nginx uninstaller for KurServer CLI.
"""

import os
import subprocess
from typing import List

from .base import BaseUninstaller
from ..core.system import is_package_installed
from ..utils.package import purge_package_config
# Removed process termination imports as per requirement
from ..core.logger import get_logger

logger = get_logger()


class NginxUninstaller(BaseUninstaller):
    """Nginx uninstaller with backup functionality."""
    
    def __init__(self):
        """Initialize Nginx uninstaller."""
        super().__init__("nginx")
    
    def get_package_names(self) -> List[str]:
        """
        Get list of packages to uninstall.
        
        Returns:
            List[str]: List of package names
        """
        return ["nginx", "nginx-common", "nginx-core"]
    
    def get_backup_paths(self) -> List[str]:
        """
        Get list of paths to backup.
        
        Returns:
            List[str]: List of paths to backup
        """
        paths = []
        
        # Nginx configuration
        if os.path.exists("/etc/nginx"):
            paths.append("/etc/nginx")
        
        # Sites configuration
        if os.path.exists("/etc/nginx/sites-enabled"):
            paths.append("/etc/nginx/sites-enabled")
        
        if os.path.exists("/etc/nginx/sites-available"):
            paths.append("/etc/nginx/sites-available")
        
        # SSL certificates
        if os.path.exists("/etc/ssl/certs"):
            paths.append("/etc/ssl/certs")
        
        if os.path.exists("/etc/ssl/private"):
            paths.append("/etc/ssl/private")
        
        # Log files
        if os.path.exists("/var/log/nginx"):
            paths.append("/var/log/nginx")
        
        # Custom configurations
        if os.path.exists("/etc/nginx/conf.d"):
            paths.append("/etc/nginx/conf.d")
        
        return paths
    
    def get_service_names(self) -> List[str]:
        """
        Get list of services to manage.
        
        Returns:
            List[str]: List of service names
        """
        return ["nginx"]
    
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
                logger.info("Performing Nginx pre-uninstallation checks...")
            
            # Check if Nginx is installed
            if not is_package_installed('nginx'):
                logger.warning("Nginx is not installed")
                return False
            
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
            
            # Check available disk space (minimum 100MB)
            try:
                stat = os.statvfs("/")
                available_space = stat.f_bavail * stat.f_frsize
                
                if available_space < total_size + 100 * 1024 * 1024:  # 100MB buffer
                    logger.error("Insufficient disk space for backup")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")
            
            if verbose:
                logger.info("Nginx pre-uninstallation checks passed")
            
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
                logger.info("Performing Nginx post-uninstallation cleanup...")
            
            # Remove Nginx user if it exists and is not used by other packages
            try:
                # Check if www-data user is used by other processes
                result = subprocess.run(
                    ["sudo", "lsof", "-u", "www-data"],
                    capture_output=True,
                    text=True
                )
                
                # If only nginx processes are using www-data, we can clean up
                if result.returncode == 0 and "nginx" in result.stdout:
                    # Remove nginx-specific configurations
                    nginx_configs = [
                        "/etc/nginx",
                        "/var/log/nginx",
                        "/var/cache/nginx",
                        "/var/lib/nginx"
                    ]
                    
                    for config_path in nginx_configs:
                        if os.path.exists(config_path):
                            if verbose:
                                logger.info(f"Removing {config_path}")
                            
                            subprocess.run(
                                ["sudo", "rm", "-rf", config_path],
                                capture_output=True
                            )
                
            except Exception as e:
                logger.warning(f"Could not clean up nginx user configurations: {e}")
            
            # Clean up any remaining package configurations
            for package in self.get_package_names():
                purge_package_config(package, verbose)
            
            if verbose:
                logger.info("Nginx post-uninstallation cleanup completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Post-uninstallation cleanup failed: {e}")
            return False
    
    def get_nginx_info(self, verbose: bool = False) -> dict:
        """
        Get comprehensive Nginx information before uninstallation.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            dict: Dictionary with Nginx information
        """
        info = {
            'installed': is_package_installed('nginx'),
            'version': None,
            'sites_count': 0,
            'active_sites': [],
            'config_files': [],
            'ssl_certificates': []
        }
        
        if not info['installed']:
            return info
        
        try:
            # Get Nginx version
            try:
                result = subprocess.run(
                    ["nginx", "-v"],
                    capture_output=True,
                    text=True
                )
                
                if result.stderr:
                    # Nginx outputs version to stderr
                    version_line = result.stderr.strip()
                    if 'nginx/' in version_line:
                        info['version'] = version_line.split('nginx/')[1].split(' ')[0]
            except Exception:
                pass
            
            # Get enabled sites
            sites_enabled_dir = "/etc/nginx/sites-enabled"
            if os.path.exists(sites_enabled_dir):
                sites = os.listdir(sites_enabled_dir)
                info['sites_count'] = len(sites)
                info['active_sites'] = [site for site in sites if site != 'default']
            
            # Get configuration files
            config_dir = "/etc/nginx"
            if os.path.exists(config_dir):
                for root, dirs, files in os.walk(config_dir):
                    for file in files:
                        if file.endswith('.conf'):
                            info['config_files'].append(os.path.join(root, file))
            
            # Get SSL certificates
            ssl_certs_dir = "/etc/ssl/certs"
            if os.path.exists(ssl_certs_dir):
                for file in os.listdir(ssl_certs_dir):
                    if file.endswith('.crt') or file.endswith('.pem'):
                        info['ssl_certificates'].append(os.path.join(ssl_certs_dir, file))
            
            if verbose:
                logger.info(f"Nginx info: {info}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting Nginx info: {e}")
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
                logger.info("Creating detailed Nginx backup...")
            
            # Get Nginx information
            nginx_info = self.get_nginx_info(verbose)
            
            # Create standard backup
            backup_path = self.create_backup(verbose)
            
            if not backup_path:
                return False
            
            # Create additional info file
            import json
            info_path = backup_path.replace('.tar.gz', '_info.json')
            
            with open(info_path, 'w') as f:
                json.dump(nginx_info, f, indent=2)
            
            # Add info file to backup
            import tarfile
            with tarfile.open(backup_path, "a:gz") as tar:
                tar.add(info_path, arcname="nginx_info.json")
            
            # Remove temporary info file
            os.remove(info_path)
            
            if verbose:
                logger.info(f"Detailed Nginx backup created: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create detailed backup: {e}")
            return False
    
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
            console.print("[yellow]After removing Nginx, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
            console.print()
            
        except Exception as e:
            logger.error(f"Failed to display restart warning: {e}")
    
    def uninstall(self, verbose: bool = False) -> bool:
        """
        Complete uninstallation process with enhanced process termination.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Pre-uninstallation checks
            if not self.pre_uninstall_checks(verbose):
                return False
            
            # Create backup
            backup_path = self.create_backup(verbose)
            if not backup_path:
                logger.error("Failed to create backup, aborting uninstallation")
                return False
            
            # Stop services using base class method
            if not self.stop_services(verbose):
                logger.warning("Standard service stop had issues, but continuing with uninstallation...")
            
            # Disable services
            if not self.disable_services(verbose):
                logger.error("Failed to disable services")
                return False
            
            # Uninstall packages
            if not self.uninstall_packages(verbose):
                logger.error("Failed to uninstall packages")
                return False
            
            # Post-uninstallation cleanup
            if not self.post_uninstall_cleanup(verbose):
                logger.error("Failed to perform post-uninstallation cleanup")
                return False
            
            # Final verification that ports are clear
            if verbose:
                logger.info("Performing final verification that ports are clear...")
            
            common_ports = [80, 443, 8080]
            for port in common_ports:
                from ..utils.process import get_processes_using_port
                processes = get_processes_using_port(port)
                if processes:
                    logger.warning(f"Port {port} is still in use after uninstallation:")
                    for proc in processes:
                        logger.warning(f"  PID {proc['pid']} ({proc['process_name']}) on {proc['address']}")
                elif verbose:
                    logger.info(f"Port {port} is clear")
            
            if verbose:
                logger.info(f"{self.component_name} uninstalled successfully")
                logger.info(f"Backup saved at: {backup_path}")
            
            # Show restart warning
            self.show_restart_warning(self.component_name, verbose)
            
            return True
            
        except Exception as e:
            logger.error(f"Uninstallation failed: {e}")
            return False