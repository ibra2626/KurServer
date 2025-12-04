"""
MySQL/MariaDB uninstaller for KurServer CLI.
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


class MySQLUninstaller(BaseUninstaller):
    """MySQL/MariaDB uninstaller with database backup functionality."""
    
    def __init__(self):
        """Initialize MySQL uninstaller."""
        super().__init__("mysql")
        
        # Detect which database is installed
        if is_package_installed('mysql-server'):
            self.db_type = 'mysql'
            self.service_name = 'mysql'
            self.packages = ['mysql-server', 'mysql-client', 'mysql-common', 'mysql-server-core-*']
        elif is_package_installed('mariadb-server'):
            self.db_type = 'mariadb'
            self.service_name = 'mariadb'
            self.packages = ['mariadb-server', 'mariadb-client', 'mariadb-common', 'mariadb-server-core-*']
        else:
            raise Exception("Neither MySQL nor MariaDB is installed")
    
    def get_package_names(self) -> List[str]:
        """
        Get list of packages to uninstall.
        
        Returns:
            List[str]: List of package names
        """
        return self.packages
    
    def get_backup_paths(self) -> List[str]:
        """
        Get list of paths to backup.
        
        Returns:
            List[str]: List of paths to backup
        """
        paths = []
        
        # Database configuration
        if os.path.exists("/etc/mysql"):
            paths.append("/etc/mysql")
        
        # Database data
        if os.path.exists("/var/lib/mysql"):
            paths.append("/var/lib/mysql")
        
        # Log files
        if os.path.exists("/var/log/mysql"):
            paths.append("/var/log/mysql")
        
        # Custom configurations
        if os.path.exists("/etc/mysql/conf.d"):
            paths.append("/etc/mysql/conf.d")
        
        return paths
    
    def get_service_names(self) -> List[str]:
        """
        Get list of services to manage.
        
        Returns:
            List[str]: List of service names
        """
        return [self.service_name]
    
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
                logger.info(f"Performing {self.db_type} pre-uninstallation checks...")
            
            # Check if database is installed
            if not is_package_installed(f'{self.db_type}-server'):
                logger.warning(f"{self.db_type.title()} is not installed")
                return False
            
            # Check if service is running
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", self.service_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    if verbose:
                        logger.info(f"{self.db_type.title()} service is running")
                else:
                    if verbose:
                        logger.info(f"{self.db_type.title()} service is not running")
                        
            except Exception as e:
                logger.warning(f"Could not check service status: {e}")
            
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
            
            # Check available disk space (minimum 500MB for database backup)
            try:
                stat = os.statvfs("/")
                available_space = stat.f_bavail * stat.f_frsize
                
                if available_space < total_size + 500 * 1024 * 1024:  # 500MB buffer
                    logger.error("Insufficient disk space for database backup")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")
            
            if verbose:
                logger.info(f"{self.db_type.title()} pre-uninstallation checks passed")
            
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
                logger.info(f"Performing {self.db_type} post-uninstallation cleanup...")
            
            # Remove database user if it exists
            try:
                # Check if mysql user exists
                result = subprocess.run(
                    ["id", "mysql"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    if verbose:
                        logger.info("Removing mysql user")
                    
                    subprocess.run(
                        ["sudo", "userdel", "mysql"],
                        capture_output=True
                    )
                    
            except Exception as e:
                logger.warning(f"Could not remove mysql user: {e}")
            
            # Clean up any remaining package configurations
            for package in self.get_package_names():
                purge_package_config(package, verbose)
            
            # Remove remaining directories
            cleanup_dirs = [
                "/var/lib/mysql",
                "/var/log/mysql",
                "/etc/mysql",
                "/run/mysqld"
            ]
            
            for dir_path in cleanup_dirs:
                if os.path.exists(dir_path):
                    if verbose:
                        logger.info(f"Removing directory: {dir_path}")
                    
                    subprocess.run(
                        ["sudo", "rm", "-rf", dir_path],
                        capture_output=True
                    )
            
            if verbose:
                logger.info(f"{self.db_type.title()} post-uninstallation cleanup completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Post-uninstallation cleanup failed: {e}")
            return False
    
    def backup_databases(self, verbose: bool = False) -> bool:
        """
        Create backup of all databases.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                logger.info(f"Creating {self.db_type} database backup...")
            
            # Create backup directory
            backup_dir = f"/tmp/{self.db_type}_backup_{os.getpid()}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Get list of databases
            try:
                result = subprocess.run(
                    ["sudo", f"{self.db_type}", "-u", "root", "-e", "SHOW DATABASES;"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to get database list: {result.stderr}")
                    return False
                
                databases = [db.strip() for db in result.stdout.strip().split('\n') if db.strip() and db.strip() != 'Database']
                
            except Exception as e:
                logger.error(f"Error getting database list: {e}")
                return False
            
            # Backup each database
            for database in databases:
                if verbose:
                    logger.info(f"Backing up database: {database}")
                
                backup_file = os.path.join(backup_dir, f"{database}.sql")
                
                try:
                    result = subprocess.run([
                        "sudo", f"{self.db_type}dump", 
                        "-u", "root",
                        "--single-transaction",
                        "--routines",
                        "--triggers",
                        database
                    ], 
                    capture_output=True,
                    text=True,
                    check=True
                    )
                    
                    with open(backup_file, 'w') as f:
                        f.write(result.stdout)
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to backup database {database}: {e}")
                    return False
            
            # Create database list file
            with open(os.path.join(backup_dir, "database_list.txt"), 'w') as f:
                f.write('\n'.join(databases))
            
            # Create backup info
            backup_info = {
                'db_type': self.db_type,
                'databases': databases,
                'backup_time': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
                'total_databases': len(databases)
            }
            
            with open(os.path.join(backup_dir, "backup_info.json"), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            if verbose:
                logger.info(f"Database backup completed: {backup_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
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
                logger.info(f"Creating backup for {self.db_type}...")
            
            # First backup databases
            if not self.backup_databases(verbose):
                logger.error("Failed to backup databases")
                return None
            
            # Get standard backup paths
            backup_paths = self.get_backup_paths()
            
            # Add database backup directory
            backup_paths.append(f"/tmp/{self.db_type}_backup_{os.getpid()}")
            
            # Create backup
            backup_path = self.backup_manager.create_backup(
                paths=backup_paths,
                verbose=verbose
            )
            
            # Clean up temporary backup directory
            temp_backup_dir = f"/tmp/{self.db_type}_backup_{os.getpid()}"
            if os.path.exists(temp_backup_dir):
                subprocess.run(["sudo", "rm", "-rf", temp_backup_dir])
            
            if backup_path and verbose:
                logger.info(f"Backup created: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def get_database_info(self, verbose: bool = False) -> dict:
        """
        Get comprehensive database information before uninstallation.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            dict: Dictionary with database information
        """
        info = {
            'db_type': self.db_type,
            'installed': is_package_installed(f'{self.db_type}-server'),
            'version': None,
            'databases': [],
            'users': [],
            'total_size': 0,
            'data_directory': '/var/lib/mysql'
        }
        
        if not info['installed']:
            return info
        
        try:
            # Get database version
            try:
                result = subprocess.run([
                    f"{self.db_type}", "--version"
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    version_line = result.stdout.strip() or result.stderr.strip()
                    if self.db_type in version_line.lower():
                        # Extract version number
                        import re
                        match = re.search(r'(\d+\.\d+\.\d+)', version_line)
                        if match:
                            info['version'] = match.group(1)
            except Exception:
                pass
            
            # Get list of databases
            try:
                result = subprocess.run([
                    "sudo", f"{self.db_type}", "-u", "root", "-e", "SHOW DATABASES;"
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    databases = [db.strip() for db in result.stdout.strip().split('\n') if db.strip() and db.strip() != 'Database']
                    info['databases'] = databases
                    
            except Exception:
                pass
            
            # Get database users
            try:
                result = subprocess.run([
                    "sudo", f"{self.db_type}", "-u", "root", "-e", "SELECT User FROM mysql.user;"
                ], 
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    users = [user.strip() for user in result.stdout.strip().split('\n') if user.strip() and user.strip() != 'User']
                    info['users'] = list(set(users))  # Remove duplicates
                    
            except Exception:
                pass
            
            # Get database size
            try:
                if os.path.exists(info['data_directory']):
                    total_size = 0
                    for root, dirs, files in os.walk(info['data_directory']):
                        for file in files:
                            total_size += os.path.getsize(os.path.join(root, file))
                    info['total_size'] = total_size
                    
            except Exception:
                pass
            
            if verbose:
                logger.info(f"{self.db_type.title()} info: {info}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting {self.db_type} info: {e}")
            return info
    
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
            console.print(f"[yellow]After removing {self.db_type}, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
            console.print()
            
        except Exception as e:
            logger.error(f"Failed to display restart warning: {e}")