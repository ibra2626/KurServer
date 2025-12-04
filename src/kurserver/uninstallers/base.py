"""
Base uninstaller class for KurServer CLI components.
"""

import os
import subprocess
import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from ..core.logger import get_logger
from ..utils.backup import BackupManager
from ..utils.package import uninstall_package, remove_unused_dependencies

logger = get_logger()


class BaseUninstaller(ABC):
    """Base class for component uninstallers with backup functionality."""
    
    def __init__(self, component_name: str):
        """
        Initialize uninstaller.
        
        Args:
            component_name (str): Name of the component (nginx, mysql, php)
        """
        self.component_name = component_name
        self.backup_manager = BackupManager(component_name)
        self.backup_dir = f"/var/lib/kurserver/backups/{component_name}"
        self.logger = get_logger()
    
    @abstractmethod
    def get_package_names(self) -> List[str]:
        """
        Get list of packages to uninstall.
        
        Returns:
            List[str]: List of package names
        """
        pass
    
    @abstractmethod
    def get_backup_paths(self) -> List[str]:
        """
        Get list of paths to backup.
        
        Returns:
            List[str]: List of paths to backup
        """
        pass
    
    @abstractmethod
    def get_service_names(self) -> List[str]:
        """
        Get list of services to manage.
        
        Returns:
            List[str]: List of service names
        """
        pass
    
    @abstractmethod
    def pre_uninstall_checks(self, verbose: bool = False) -> bool:
        """
        Perform pre-uninstallation checks.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if checks pass, False otherwise
        """
        pass
    
    @abstractmethod
    def post_uninstall_cleanup(self, verbose: bool = False) -> bool:
        """
        Perform post-uninstallation cleanup.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        pass
    
    def create_backup(self, verbose: bool = False) -> Optional[str]:
        """
        Create backup of configurations and data.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            Optional[str]: Backup path if successful, None otherwise
        """
        try:
            if verbose:
                self.logger.info(f"Creating backup for {self.component_name}...")
            
            backup_paths = self.get_backup_paths()
            backup_path = self.backup_manager.create_backup(
                paths=backup_paths,
                verbose=verbose
            )
            
            if backup_path and verbose:
                self.logger.info(f"Backup created: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def stop_services(self, verbose: bool = False) -> bool:
        """
        Stop component services with enhanced verification.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            services = self.get_service_names()
            
            for service in services:
                if verbose:
                    self.logger.info(f"Stopping service: {service}")
                
                # Enhanced service status check
                service_status = self._get_service_status(service)
                
                if service_status['active']:
                    # Stop service using simple method
                    stop_result = self._stop_service_simple(service, verbose)
                    if not stop_result:
                        self.logger.warning(f"Failed to stop service: {service}, but continuing with uninstallation...")
                    
                    if verbose:
                        self.logger.info(f"Service {service} stop attempt completed")
                elif verbose:
                    self.logger.info(f"Service {service} is not running")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop services: {e}")
            return False
    
    def _get_service_status(self, service_name: str) -> dict:
        """
        Get comprehensive service status.
        
        Args:
            service_name (str): Name of the service
            
        Returns:
            dict: Service status information
        """
        status = {
            'active': False,
            'enabled': False,
            'pid': None,
            'ports': []
        }
        
        try:
            # Check if active
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            status['active'] = result.returncode == 0 and result.stdout.strip() == 'active'
            
            # Check if enabled
            result = subprocess.run(
                ["systemctl", "is-enabled", service_name],
                capture_output=True,
                text=True
            )
            status['enabled'] = result.returncode == 0 and result.stdout.strip() == 'enabled'
            
            # Get PID if active
            if status['active']:
                try:
                    result = subprocess.run(
                        ["systemctl", "show", service_name, "--property=MainPID"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        pid = result.stdout.strip()
                        if pid.isdigit():
                            status['pid'] = int(pid)
                except Exception:
                    pass
            
            # Check for port bindings (for web services)
            if service_name in ['nginx', 'apache2', 'httpd']:
                status['ports'] = self._get_service_ports(service_name)
            
        except Exception as e:
            self.logger.warning(f"Could not get complete service status for {service_name}: {e}")
        
        return status
    
    def _get_service_ports(self, service_name: str) -> list:
        """
        Get ports used by a service.
        
        Args:
            service_name (str): Name of the service
            
        Returns:
            list: List of ports used by the service
        """
        ports = []
        
        try:
            if service_name == 'nginx':
                # Check nginx configuration for listen ports
                try:
                    result = subprocess.run(
                        ["sudo", "nginx", "-T"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'listen:' in line:
                                port = line.split(':')[1].strip().split()[0]
                                if port.isdigit():
                                    ports.append(int(port))
                except Exception:
                    pass
            
            elif service_name in ['apache2', 'httpd']:
                # Check Apache configuration for ports
                try:
                    result = subprocess.run(
                        ["sudo", "apache2ctl", "-S"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'Port' in line and '*' in line:
                                port = line.split()[1]
                                if port.isdigit():
                                    ports.append(int(port))
                except Exception:
                    pass
        
        except Exception as e:
            self.logger.warning(f"Could not get ports for {service_name}: {e}")
        
        return ports
    
    def _stop_service_simple(self, service_name: str, verbose: bool = False) -> bool:
        """
        Simple service stop without force termination.
        
        Args:
            service_name (str): Name of the service
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                self.logger.info(f"Stopping service: {service_name}")
            
            # Try systemctl stop
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "stop", service_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    if verbose:
                        self.logger.info(f"Service {service_name} stopped successfully")
                    return True
                else:
                    if verbose:
                        self.logger.warning(f"Failed to stop service {service_name}: {result.stderr}")
                    return False
            except Exception as e:
                if verbose:
                    self.logger.error(f"Error stopping service {service_name}: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error in simple stop service: {e}")
            return False
    
    def _wait_for_service_stop(self, service_name: str, timeout: int = 10, verbose: bool = False) -> bool:
        """
        Wait for service to actually stop.
        
        Args:
            service_name (str): Name of the service
            timeout (int): Timeout in seconds
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if service stopped, False otherwise
        """
        import time
        
        if verbose:
            self.logger.info(f"Waiting for {service_name} to stop...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            service_status = self._get_service_status(service_name)
            
            if not service_status['active']:
                if verbose:
                    self.logger.info(f"Service {service_name} stopped successfully")
                return True
            
            # Check for zombie processes
            if service_status['pid']:
                try:
                    result = subprocess.run(
                        ["ps", "-p", str(service_status['pid'])],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        # Process is gone
                        if verbose:
                            self.logger.info(f"Service {service_name} process terminated")
                        return True
                except Exception:
                    pass
            
            time.sleep(1)
        
        # Timeout reached
        self.logger.error(f"Timeout waiting for {service_name} to stop")
        return False
    
    def _verify_service_disabled(self, service_name: str, verbose: bool = False) -> bool:
        """
        Verify that a service is properly disabled.
        
        Args:
            service_name (str): Name of the service
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if service is disabled, False otherwise
        """
        try:
            # Check if service is enabled
            result = subprocess.run(
                ["systemctl", "is-enabled", service_name],
                capture_output=True,
                text=True
            )
            
            is_enabled = result.returncode == 0 and result.stdout.strip() == 'enabled'
            
            if verbose:
                if is_enabled:
                    self.logger.warning(f"Service {service_name} is still enabled")
                else:
                    self.logger.info(f"Service {service_name} is properly disabled")
            
            return not is_enabled
            
        except Exception as e:
            if verbose:
                self.logger.warning(f"Could not verify service {service_name} disabled state: {e}")
            return True  # Assume success if we can't verify
    
    def disable_services(self, verbose: bool = False) -> bool:
        """
        Disable component services from auto-start.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            services = self.get_service_names()
            
            for service in services:
                if verbose:
                    self.logger.info(f"Disabling service: {service}")
                
                # Disable service
                subprocess.run(
                    ["sudo", "systemctl", "disable", service],
                    check=True,
                    capture_output=True
                )
                
                if verbose:
                    self.logger.info(f"Service {service} disabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable services: {e}")
            return False
    
    def uninstall_packages(self, verbose: bool = False) -> bool:
        """
        Uninstall component packages.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            packages = self.get_package_names()
            
            for package in packages:
                if verbose:
                    self.logger.info(f"Uninstalling package: {package}")
                
                if not uninstall_package(package, verbose=verbose):
                    self.logger.error(f"Failed to uninstall package: {package}")
                    return False
            
            # Remove unused dependencies
            if verbose:
                self.logger.info("Removing unused dependencies...")
            
            remove_unused_dependencies(verbose=verbose)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall packages: {e}")
            return False
    
    def rollback(self, backup_timestamp: Optional[str] = None, verbose: bool = False) -> bool:
        """
        Rollback from backup.
        
        Args:
            backup_timestamp (Optional[str]): Backup timestamp to restore from
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                self.logger.info(f"Rolling back {self.component_name} from backup...")
            
            return self.backup_manager.restore_backup(
                backup_timestamp=backup_timestamp,
                verbose=verbose
            )
            
        except Exception as e:
            self.logger.error(f"Failed to rollback: {e}")
            return False
    
    def uninstall(self, verbose: bool = False) -> bool:
        """
        Complete uninstallation process.
        
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
                self.logger.error("Failed to create backup, aborting uninstallation")
                return False
            
            # Stop services
            if not self.stop_services(verbose):
                self.logger.error("Failed to stop services")
                return False
            
            # Disable services
            if not self.disable_services(verbose):
                self.logger.error("Failed to disable services")
                return False
            
            # Uninstall packages
            if not self.uninstall_packages(verbose):
                self.logger.error("Failed to uninstall packages")
                return False
            
            # Post-uninstallation cleanup
            if not self.post_uninstall_cleanup(verbose):
                self.logger.error("Failed to perform post-uninstallation cleanup")
                return False
            
            if verbose:
                self.logger.info(f"{self.component_name} uninstalled successfully")
                self.logger.info(f"Backup saved at: {backup_path}")
            
            # Show restart warning
            self.show_restart_warning(self.component_name, verbose)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Uninstallation failed: {e}")
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
                self.logger.info("Displaying restart warning...")
            
            console = __import__('rich.console').console.Console()
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print(f"[yellow]After removing {component_name}, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
            console.print()
            
        except Exception as e:
            self.logger.error(f"Failed to display restart warning: {e}")