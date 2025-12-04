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
    services = ['nginx', 'mysql', 'mariadb', 'php7.4-fpm', 'php8.0-fpm', 'php8.1-fpm', 'php8.2-fpm', 'php8.3-fpm']
    
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
    for version in ['7.4', '8.0', '8.1', '8.2', '8.3']:
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


def is_container_environment():
    """
    Check if the current environment is a container (Docker, LXC, etc.).
    
    Returns:
        bool: True if running in a container, False otherwise
    """
    # Check for Docker-specific files
    docker_indicators = [
        '/.dockerenv',
        '/proc/1/cgroup'
    ]
    
    # Check for .dockerenv file
    if os.path.exists('/.dockerenv'):
        return True
    
    # Check cgroup for container indicators
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'lxc' in cgroup_content:
                return True
    except (FileNotFoundError, PermissionError):
        pass
    
    # Check if PID 1 is not systemd
    try:
        result = subprocess.run(
            ['ps', '-p', '1', '-o', 'comm='],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and 'systemd' not in result.stdout:
            return True
    except subprocess.SubprocessError:
        pass
    
    return False


def reload_nginx():
    """
    Reload nginx configuration using appropriate method for the environment.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if we're in a container environment
    if is_container_environment():
        try:
            # In containers, try to reload nginx directly
            subprocess.run(['sudo', 'nginx', '-s', 'reload'], check=True)
            return True
        except subprocess.SubprocessError:
            try:
                # Fallback to service command
                subprocess.run(['sudo', 'service', 'nginx', 'reload'], check=True)
                return True
            except subprocess.SubprocessError:
                return False
    else:
        # In regular systems, use systemctl
        try:
            subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
            return True
        except subprocess.SubprocessError:
            return False


def restart_service(service_name):
    """
    Restart a service using appropriate method for the environment.
    
    Args:
        service_name (str): Name of the service to restart
        
    Returns:
        bool: True if successful, False otherwise
    """
    from .logger import get_logger
    logger = get_logger()
    
    # DEBUG: Log function entry
    logger.info(f"[DEBUG] restart_service called for: {service_name}")
    
    # Check if we're in a container environment
    is_container = is_container_environment()
    logger.info(f"[DEBUG] Is container environment: {is_container}")
    
    # ENHANCED DEBUG: Check if service exists before trying to restart
    logger.info(f"[DEBUG] Checking if service {service_name} exists")
    try:
        # Check if service unit file exists
        check_result = subprocess.run(['sudo', 'systemctl', 'list-unit-files', f"{service_name}.service"],
                                     capture_output=True, text=True)
        logger.info(f"[DEBUG] systemctl list-unit-files return code: {check_result.returncode}")
        logger.info(f"[DEBUG] systemctl list-unit-files stdout: {check_result.stdout}")
        if check_result.stderr:
            logger.info(f"[DEBUG] systemctl list-unit-files stderr: {check_result.stderr}")
        
        service_exists = check_result.returncode == 0 and service_name in check_result.stdout
        logger.info(f"[DEBUG] Service {service_name} exists: {service_exists}")
    except Exception as e:
        logger.warning(f"[DEBUG] Error checking if service exists: {e}")
        service_exists = False
    
    if is_container:
        try:
            # In containers, try to restart using service command
            logger.info(f"[DEBUG] Trying service command restart")
            result = subprocess.run(['sudo', 'service', service_name, 'restart'], check=True, capture_output=True, text=True)
            logger.info(f"[DEBUG] Service command restart successful")
            logger.debug(f"[DEBUG] Service command stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"[DEBUG] Service command stderr: {result.stderr}")
            
            # ENHANCED DEBUG: Verify service is actually running after restart
            logger.info(f"[DEBUG] Verifying service status after restart")
            try:
                status_result = subprocess.run(['sudo', 'service', service_name, 'status'],
                                             capture_output=True, text=True)
                logger.info(f"[DEBUG] Service status return code: {status_result.returncode}")
                logger.info(f"[DEBUG] Service status stdout: {status_result.stdout}")
                if status_result.stderr:
                    logger.info(f"[DEBUG] Service status stderr: {status_result.stderr}")
                
                # Check if service is actually running
                is_running = 'running' in status_result.stdout.lower() or 'is running' in status_result.stdout.lower()
                logger.info(f"[DEBUG] Service is running after restart: {is_running}")
            except Exception as e:
                logger.warning(f"[DEBUG] Error checking service status after restart: {e}")
            
            logger.info(f"[DEBUG] About to return True from restart_service (container path)")
            return True
        except subprocess.SubprocessError as e:
            logger.warning(f"[DEBUG] Service command restart failed: {e}")
            logger.debug(f"[DEBUG] Exception stdout: {e.stdout}")
            if e.stderr:
                logger.debug(f"[DEBUG] Exception stderr: {e.stderr}")
            try:
                # Fallback to direct command if available
                if service_name.startswith('php') and '-fpm' in service_name:
                    # For PHP-FPM, try to start it directly
                    version = service_name.replace('php', '').replace('-fpm', '')
                    php_fpm_binary = f"/usr/sbin/php-fpm{version}"
                    logger.info(f"[DEBUG] Trying to start PHP-FPM directly with binary: {php_fpm_binary}")
                    try:
                        # First check if binary exists
                        binary_check = subprocess.run(['which', php_fpm_binary],
                                                   capture_output=True, text=True)
                        if binary_check.returncode == 0:
                            # Try to start PHP-FPM directly
                            subprocess.run(['sudo', php_fpm_binary, "--nodaemonize",
                                          "--fpm-config", f"/etc/php/{version}/fpm/php-fpm.conf"],
                                         check=True, capture_output=True, text=True, timeout=5)
                            logger.info(f"[DEBUG] Direct PHP-FPM start successful")
                            return True
                        else:
                            logger.warning(f"[DEBUG] PHP-FPM binary not found: {php_fpm_binary}")
                    except Exception as direct_e:
                        logger.warning(f"[DEBUG] Direct PHP-FPM start failed: {direct_e}")
                
                if service_name == 'nginx':
                    logger.info(f"[DEBUG] Trying nginx direct reload")
                    subprocess.run(['sudo', 'nginx', '-s', 'reload'], check=True)
                    logger.info(f"[DEBUG] Nginx direct reload successful")
                    return True
                # Add more service-specific commands as needed
            except subprocess.SubprocessError as e:
                logger.warning(f"[DEBUG] Direct command also failed: {e}")
                return False
    else:
        # In regular systems, use systemctl
        try:
            logger.info(f"[DEBUG] Trying systemctl restart")
            restart_result = subprocess.run(['sudo', 'systemctl', 'restart', service_name],
                                          capture_output=True, text=True)
            logger.info(f"[DEBUG] systemctl restart return code: {restart_result.returncode}")
            if restart_result.stdout:
                logger.info(f"[DEBUG] systemctl restart stdout: {restart_result.stdout}")
            if restart_result.stderr:
                logger.info(f"[DEBUG] systemctl restart stderr: {restart_result.stderr}")
            
            # ENHANCED DEBUG: Verify service is actually running after restart
            logger.info(f"[DEBUG] Verifying service status after systemctl restart")
            try:
                status_result = subprocess.run(['sudo', 'systemctl', 'is-active', service_name],
                                             capture_output=True, text=True)
                logger.info(f"[DEBUG] systemctl is-active return code: {status_result.returncode}")
                logger.info(f"[DEBUG] systemctl is-active stdout: {status_result.stdout}")
                if status_result.stderr:
                    logger.info(f"[DEBUG] systemctl is-active stderr: {status_result.stderr}")
                
                # Check if service is actually running
                is_active = status_result.returncode == 0 and 'active' in status_result.stdout
                logger.info(f"[DEBUG] Service is active after restart: {is_active}")
            except Exception as e:
                logger.warning(f"[DEBUG] Error checking service status after restart: {e}")
            
            logger.info(f"[DEBUG] Systemctl restart successful")
            return True
        except subprocess.SubprocessError as e:
            logger.warning(f"[DEBUG] Systemctl restart failed: {e}")
            logger.debug(f"[DEBUG] Exception stdout: {e.stdout}")
            if e.stderr:
                logger.debug(f"[DEBUG] Exception stderr: {e.stderr}")
            return False


def get_installed_components():
    """
    Get list of currently installed components.
    
    Returns:
        dict: Dictionary with installed components status
    """
    components = {
        'nginx': {
            'installed': is_package_installed('nginx'),
            'running': is_service_running('nginx'),
            'enabled': is_service_enabled('nginx')
        },
        'mysql': {
            'installed': is_package_installed('mysql-server'),
            'running': is_service_running('mysql'),
            'enabled': is_service_enabled('mysql')
        },
        'mariadb': {
            'installed': is_package_installed('mariadb-server'),
            'running': is_service_running('mariadb'),
            'enabled': is_service_enabled('mariadb')
        },
        'php': {}
    }
    
    # Check PHP versions
    for version in ['7.4', '8.0', '8.1', '8.2', '8.3']:
        php_fpm = f"php{version}-fpm"
        components['php'][version] = {
            'installed': is_package_installed(php_fpm),
            'running': is_service_running(php_fpm),
            'enabled': is_service_enabled(php_fpm)
        }
    
    return components


def get_uninstallation_history():
    """
    Get list of available backups for all components.
    
    Returns:
        dict: Dictionary with backup information for each component
    """
    from ..utils.backup import BackupManager
    
    components = ['nginx', 'mysql', 'php']
    history = {}
    
    for component in components:
        try:
            backup_manager = BackupManager(component)
            backups = backup_manager.list_backups()
            history[component] = {
                'backups': backups,
                'total_backups': len(backups),
                'latest_backup': backups[0] if backups else None,
                'total_size': sum(backup.get('size_bytes', 0) for backup in backups)
            }
        except Exception:
            history[component] = {
                'backups': [],
                'total_backups': 0,
                'latest_backup': None,
                'total_size': 0
            }
    
    return history


def can_uninstall_component(component_name):
    """
    Check if a component can be safely uninstalled.
    
    Args:
        component_name (str): Name of the component
        
    Returns:
        dict: Dictionary with uninstallation feasibility information
    """
    components = get_installed_components()
    
    if component_name not in components:
        return {
            'can_uninstall': False,
            'reason': f'Component {component_name} is not supported',
            'dependencies': [],
            'warnings': []
        }
    
    component_info = components[component_name]
    
    # Check if component is installed
    if not component_info.get('installed', False):
        return {
            'can_uninstall': False,
            'reason': f'Component {component_name} is not installed',
            'dependencies': [],
            'warnings': []
        }
    
    # Check for dependencies
    dependencies = []
    warnings = []
    
    if component_name == 'nginx':
        # Check if any PHP sites depend on Nginx
        php_versions = [v for v in ['7.4', '8.0', '8.1', '8.2', '8.3']
                     if components['php'].get(v, {}).get('installed', False)]
        if php_versions:
            warnings.append("PHP-FPM is installed - websites may depend on Nginx configuration")
    
    elif component_name in ['mysql', 'mariadb']:
        # Check if PHP is installed with MySQL extensions
        php_versions = [v for v in ['7.4', '8.0', '8.1', '8.2', '8.3']
                     if components['php'].get(v, {}).get('installed', False)]
        if php_versions:
            for version in php_versions:
                if is_package_installed(f'php{version}-mysql'):
                    dependencies.append(f'PHP {version} with MySQL extension')
                    warnings.append(f"PHP {version} applications may depend on this database")
    
    elif component_name == 'php':
        # This is handled per version in the PHP uninstaller
        pass
    
    # Check if component is currently running
    if component_info.get('running', False):
        warnings.append(f"Component {component_name} is currently running")
    
    return {
        'can_uninstall': True,
        'reason': None,
        'dependencies': dependencies,
        'warnings': warnings,
        'component_info': component_info
    }


def get_backup_size_estimate(component_name):
    """
    Estimate backup size for a component.
    
    Args:
        component_name (str): Name of the component
        
    Returns:
        dict: Dictionary with size estimation information
    """
    import os
    
    # Define paths to check for each component
    backup_paths = {
        'nginx': [
            '/etc/nginx',
            '/var/log/nginx',
            '/etc/ssl/certs',
            '/etc/ssl/private'
        ],
        'mysql': [
            '/etc/mysql',
            '/var/lib/mysql',
            '/var/log/mysql'
        ],
        'mariadb': [
            '/etc/mysql',
            '/var/lib/mysql',
            '/var/log/mysql'
        ],
        'php': []
    }
    
    # For PHP, check all installed versions
    if component_name == 'php':
        components = get_installed_components()
        for version in ['7.4', '8.0', '8.1', '8.2', '8.3']:
            if components['php'].get(version, {}).get('installed', False):
                backup_paths['php'].extend([
                    f'/etc/php/{version}',
                    f'/var/log/php{version}-fpm.log',
                    '/var/lib/php/sessions'
                ])
    
    # Calculate total size
    paths = backup_paths.get(component_name, [])
    total_size = 0
    
    for path in paths:
        if os.path.exists(path):
            if os.path.isfile(path):
                total_size += os.path.getsize(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        try:
                            total_size += os.path.getsize(os.path.join(root, file))
                        except (OSError, PermissionError):
                            # Skip files we can't read
                            pass
    
    return {
        'component': component_name,
        'paths': paths,
        'estimated_size_bytes': total_size,
        'estimated_size_human': _format_size(total_size),
        'paths_exist': [path for path in paths if os.path.exists(path)]
    }


def _format_size(size_bytes):
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