"""
Backup management utilities for KurServer CLI.
"""

import os
import json
import tarfile
import subprocess
import datetime
from typing import List, Dict, Optional

from ..core.logger import get_logger

logger = get_logger()


class BackupManager:
    """Manages backup creation, restoration, and cleanup."""
    
    def __init__(self, component_name: str):
        """
        Initialize backup manager.
        
        Args:
            component_name (str): Name of the component
        """
        self.component_name = component_name
        self.backup_root = "/var/lib/kurserver/backups"
        self.backup_dir = f"{self.backup_root}/{component_name}"
        self.logger = get_logger()
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, paths: List[str], verbose: bool = False) -> Optional[str]:
        """
        Create timestamped backup of specified paths.
        
        Args:
            paths (List[str]): List of paths to backup
            verbose (bool): Enable verbose output
            
        Returns:
            Optional[str]: Backup path if successful, None otherwise
        """
        try:
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{timestamp}_{self.component_name}_backup.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if verbose:
                self.logger.info(f"Creating backup: {backup_filename}")
            
            # Create tar.gz archive
            with tarfile.open(backup_path, "w:gz") as tar:
                for path in paths:
                    if os.path.exists(path):
                        if verbose:
                            self.logger.info(f"Adding to backup: {path}")
                        
                        if os.path.isfile(path):
                            tar.add(path, arcname=os.path.basename(path))
                        else:
                            tar.add(path, arcname=os.path.basename(path))
                    elif verbose:
                        self.logger.warning(f"Path not found, skipping: {path}")
            
            # Create manifest
            manifest = {
                "component": self.component_name,
                "timestamp": timestamp,
                "backup_file": backup_filename,
                "contents": paths,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            manifest_path = os.path.join(self.backup_dir, f"{timestamp}_manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Set appropriate permissions
            os.chmod(backup_path, 0o644)
            os.chmod(manifest_path, 0o644)
            
            if verbose:
                self.logger.info(f"Backup created successfully: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def list_backups(self, verbose: bool = False) -> List[Dict]:
        """
        List available backups.
        
        Args:
            verbose (bool): Enable verbose output
            
        Returns:
            List[Dict]: List of backup information
        """
        try:
            backups = []
            
            if not os.path.exists(self.backup_dir):
                return backups
            
            # Look for manifest files
            for filename in os.listdir(self.backup_dir):
                if filename.endswith("_manifest.json"):
                    manifest_path = os.path.join(self.backup_dir, filename)
                    
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        
                        # Check if backup file exists
                        backup_file = os.path.join(self.backup_dir, manifest["backup_file"])
                        if os.path.exists(backup_file):
                            # Get file size
                            size = os.path.getsize(backup_file)
                            manifest["size"] = self._format_size(size)
                            manifest["size_bytes"] = size
                            backups.append(manifest)
                            
                    except Exception as e:
                        if verbose:
                            self.logger.warning(f"Failed to read manifest {filename}: {e}")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def restore_backup(self, backup_timestamp: Optional[str] = None, verbose: bool = False) -> bool:
        """
        Restore from backup.
        
        Args:
            backup_timestamp (Optional[str]): Backup timestamp to restore from
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find backup
            if backup_timestamp:
                manifest_path = os.path.join(self.backup_dir, f"{backup_timestamp}_manifest.json")
            else:
                # Use latest backup
                backups = self.list_backups(verbose)
                if not backups:
                    self.logger.error("No backups found")
                    return False
                
                latest_backup = backups[0]
                manifest_path = os.path.join(self.backup_dir, f"{latest_backup['timestamp']}_manifest.json")
            
            if not os.path.exists(manifest_path):
                self.logger.error(f"Backup manifest not found: {manifest_path}")
                return False
            
            # Read manifest
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            backup_file = os.path.join(self.backup_dir, manifest["backup_file"])
            
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            if verbose:
                self.logger.info(f"Restoring from backup: {manifest['backup_file']}")
            
            # Extract backup
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path="/")
            
            if verbose:
                self.logger.info("Backup restored successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def delete_backup(self, backup_timestamp: str, verbose: bool = False) -> bool:
        """
        Delete specific backup.
        
        Args:
            backup_timestamp (str): Backup timestamp to delete
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find backup files
            manifest_path = os.path.join(self.backup_dir, f"{backup_timestamp}_manifest.json")
            
            if not os.path.exists(manifest_path):
                self.logger.error(f"Backup manifest not found: {backup_timestamp}")
                return False
            
            # Read manifest to get backup filename
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            backup_file = os.path.join(self.backup_dir, manifest["backup_file"])
            
            # Delete files
            if os.path.exists(backup_file):
                os.remove(backup_file)
                if verbose:
                    self.logger.info(f"Deleted backup file: {manifest['backup_file']}")
            
            os.remove(manifest_path)
            if verbose:
                self.logger.info(f"Deleted manifest: {backup_timestamp}_manifest.json")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete backup: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30, verbose: bool = False) -> bool:
        """
        Clean up old backups.
        
        Args:
            days_to_keep (int): Number of days to keep backups
            verbose (bool): Enable verbose output
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                self.logger.info(f"Cleaning up backups older than {days_to_keep} days")
            
            backups = self.list_backups(verbose)
            if not backups:
                if verbose:
                    self.logger.info("No backups to clean up")
                return True
            
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            
            deleted_count = 0
            for backup in backups:
                backup_date = datetime.datetime.fromisoformat(backup["created_at"])
                
                if backup_date < cutoff_date:
                    if self.delete_backup(backup["timestamp"], verbose):
                        deleted_count += 1
            
            if verbose:
                self.logger.info(f"Cleaned up {deleted_count} old backups")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return False
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human readable format.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"