"""
System detection and requirements validation for KurServer CLI.
"""

import os
import platform
import subprocess
from pathlib import Path

from .exceptions import SystemRequirementError, PermissionError


def get_system_info():
    """
    Get comprehensive system information.
    
    Returns:
        dict: System information including OS, version, and architecture
    """
    try:
        # Get basic system information
        system_info = {
            'platform': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
        }
        
        # Get Ubuntu-specific information if available
        if platform.system() == 'Linux':
            try:
                # Try to read Ubuntu version
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            system_info['distro'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('VERSION_ID='):
                            system_info['version_id'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('PRETTY_NAME='):
                            system_info['pretty_name'] = line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                pass
        
        return system_info
    except Exception as e:
        raise SystemRequirementError(f"Failed to get system information: {e}")


def is_ubuntu():
    """
    Check if the system is running Ubuntu.
    
    Returns:
        bool: True if running on Ubuntu, False otherwise
    """
    try:
        system_info = get_system_info()
        return system_info.get('distro') == 'ubuntu'
    except Exception:
        return False


def get_ubuntu_version():
    """
    Get Ubuntu version information.
    
    Returns:
        tuple: (major, minor) version numbers, or None if not Ubuntu
    """
    try:
        system_info = get_system_info()
        if system_info.get('distro') != 'ubuntu':
            return None
        
        version_id = system_info.get('version_id')
        if version_id:
            # Parse version like "20.04" or "22.04"
            version_parts = version_id.split('.')
            if len(version_parts) >= 2:
                return int(version_parts[0]), int(version_parts[1])
        
        return None
    except Exception:
        return None


def check_sudo_access():
    """
    Check if the current user has sudo access.
    
    Returns:
        bool: True if sudo access is available, False otherwise
    """
    try:
        # Try to run a simple command with sudo -n (non-interactive)
        result = subprocess.run(
            ['sudo', '-n', 'true'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def check_system_requirements():
    """
    Validate that the system meets all requirements for KurServer CLI.
    
    Raises:
        SystemRequirementError: If system requirements are not met
        PermissionError: If insufficient permissions
    """
    # Check if running on Ubuntu
    if not is_ubuntu():
        raise SystemRequirementError(
            "Ubuntu Linux is required",
            f"Current system: {platform.system()} {platform.release()}"
        )
    
    # Check Ubuntu version (minimum 18.04)
    ubuntu_version = get_ubuntu_version()
    if ubuntu_version:
        major, minor = ubuntu_version
        if major < 18 or (major == 18 and minor < 4):
            raise SystemRequirementError(
                "Ubuntu 18.04 or later is required",
                f"Current version: {major}.{minor}"
            )
    
    # Check sudo access
    if not check_sudo_access():
        raise PermissionError("System package installation and service management")


def is_package_installed(package_name):
    """
    Check if a package is installed using dpkg.
    
    Args:
        package_name (str): Name of the package to check
        
    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['dpkg', '-l', package_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and 'ii' in result.stdout
    except subprocess.SubprocessError:
        return False


def is_service_running(service_name):
    """
    Check if a service is currently running.
    
    Args:
        service_name (str): Name of the service to check
        
    Returns:
        bool: True if service is running, False otherwise
    """
    try:
        # Try systemd first
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip() == 'active'
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        # Fallback to service command
        result = subprocess.run(
            ['service', service_name, 'status'],
            capture_output=True,
            text=True,
            timeout=3
        )
        # Check if output contains "running" or "is running"
        return 'running' in result.stdout.lower() or 'is running' in result.stdout.lower()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Final fallback: check if process is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', service_name],
            capture_output=True,
            text=True,
            timeout=3
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def is_service_enabled(service_name):
    """
    Check if a service is enabled to start on boot.
    
    Args:
        service_name (str): Name of the service to check
        
    Returns:
        bool: True if service is enabled, False otherwise
    """
    try:
        # Try systemd first
        result = subprocess.run(
            ['systemctl', 'is-enabled', service_name],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip() == 'enabled'
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # For non-systemd systems, we can't easily check if service is enabled
    # Return False as we can't determine the status
    return False


def get_service_status():
    """
    Get status of common web server services.
    
    Returns:
        dict: Dictionary with service status information
    """
    services = ['nginx', 'mysql', 'mariadb', 'php7.4-fpm', 'php8.0-fpm', 'php8.1-fpm', 'php8.2-fpm']
    
    status = {}
    for service in services:
        status[service] = {
            'installed': is_package_installed(service.replace('-fpm', '-fpm')),
            'running': is_service_running(service),
            'enabled': is_service_enabled(service)
        }
    
    return status


def get_available_php_versions():
    """
    Get list of available PHP versions.
    
    Returns:
        list: List of available PHP version strings
    """
    versions = []
    
    # Check for common PHP versions
    for version in ['7.4', '8.0', '8.1', '8.2']:
        if is_package_installed(f"php{version}-fpm"):
            versions.append(version)
    
    return versions


def get_disk_space(path='/'):
    """
    Get available disk space for a given path.
    
    Args:
        path (str): Path to check disk space for
        
    Returns:
        dict: Dictionary with disk space information
    """
    try:
        stat = os.statvfs(path)
        
        total = stat.f_frsize * stat.f_blocks
        available = stat.f_frsize * stat.f_bavail
        used = total - available
        
        return {
            'total': total,
            'available': available,
            'used': used,
            'percent_used': (used / total) * 100 if total > 0 else 0
        }
    except Exception:
        return {
            'total': 0,
            'available': 0,
            'used': 0,
            'percent_used': 0
        }