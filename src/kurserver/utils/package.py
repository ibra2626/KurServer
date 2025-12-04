"""
Package management utilities for KurServer CLI.
"""

import subprocess
from ..core.logger import get_logger

logger = get_logger()


def fix_dpkg_interruption(verbose: bool = False) -> bool:
    """
    Fix dpkg interruption by running dpkg --configure -a.
    
    This function checks for and fixes dpkg interruptions that can occur
    when package installations are interrupted or when there are pending
    package configuration operations.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful or no fix needed, False if failed
    """
    if verbose:
        logger.info("Checking for dpkg interruptions...")
    
    try:
        # Check if dpkg needs configuration
        result = subprocess.run(
            ["sudo", "dpkg", "--configure", "-a"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info("dpkg configuration completed successfully")
            return True
        else:
            logger.error(f"dpkg configuration failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"dpkg configuration failed with exception: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during dpkg configuration: {e}")
        return False


def update_package_lists(verbose: bool = False) -> bool:
    """
    Update package lists after fixing any dpkg interruptions.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    # First fix any dpkg interruptions
    if not fix_dpkg_interruption(verbose):
        return False
    
    # Update package lists
    if verbose:
        logger.info("Updating package lists...")
    
    try:
        result = subprocess.run(
            ["sudo", "apt", "update"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info("Package lists updated successfully")
            return True
        else:
            logger.error(f"Failed to update package lists: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating package lists: {e}")
        return False


def install_package(package_name: str, verbose: bool = False) -> bool:
    """
    Install a package using apt package manager.

    Args:
        package_name (str): Name of the package to install
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    # First update package lists
    if not update_package_lists(verbose):
        return False

    if verbose:
        logger.info(f"Installing package: {package_name}")

    try:
        result = subprocess.run(
            ["sudo", "apt", "install", "-y", package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info(f"Package {package_name} installed successfully")
            return True
        else:
            logger.error(f"Failed to install package {package_name}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing package {package_name}: {e}")
        return False


def is_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed on the system.

    Args:
        package_name (str): Name of the package to check
        
    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["dpkg", "-l", package_name],
            capture_output=True,
            text=True
        )
        
        # Check if package is installed (return code 0 and contains "ii" in output)
        return result.returncode == 0 and "ii" in result.stdout
        
    except Exception:
        return False


def uninstall_package(package_name: str, verbose: bool = False) -> bool:
    """
    Uninstall a package using apt package manager.
    
    Args:
        package_name (str): Name of package to uninstall
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    if verbose:
        logger.info(f"Uninstalling package: {package_name}")
    
    try:
        # Check if package is installed
        if not is_package_installed(package_name):
            if verbose:
                logger.info(f"Package {package_name} is not installed")
            return True
        
        # Uninstall package
        result = subprocess.run(
            ["sudo", "apt", "remove", "-y", package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info(f"Package {package_name} uninstalled successfully")
            return True
        else:
            logger.error(f"Failed to uninstall package {package_name}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error uninstalling package {package_name}: {e}")
        return False


def purge_package_config(package_name: str, verbose: bool = False) -> bool:
    """
    Purge package configuration files.
    
    Args:
        package_name (str): Name of package to purge
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    if verbose:
        logger.info(f"Purging configuration for package: {package_name}")
    
    try:
        result = subprocess.run(
            ["sudo", "apt", "purge", "-y", package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info(f"Package {package_name} configuration purged successfully")
            return True
        else:
            logger.error(f"Failed to purge package {package_name}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error purging package {package_name}: {e}")
        return False


def remove_unused_dependencies(verbose: bool = False) -> bool:
    """
    Remove unused dependencies.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    if verbose:
        logger.info("Removing unused dependencies...")
    
    try:
        result = subprocess.run(
            ["sudo", "apt", "autoremove", "-y"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info("Unused dependencies removed successfully")
            return True
        else:
            logger.error(f"Failed to remove unused dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error removing unused dependencies: {e}")
        return False


def clean_package_cache(verbose: bool = False) -> bool:
    """
    Clean package cache.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    if verbose:
        logger.info("Cleaning package cache...")
    
    try:
        result = subprocess.run(
            ["sudo", "apt", "clean"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if verbose:
                logger.info("Package cache cleaned successfully")
            return True
        else:
            logger.error(f"Failed to clean package cache: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error cleaning package cache: {e}")
        return False