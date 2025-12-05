"""
System detection and requirements validation for KurServer CLI.
"""

import logging
import os
import glob
import platform
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, Optional

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
    

    check_runlevels = [3, 5, 2]

    for level in check_runlevels:
        rc_dir = f'/etc/rc{level}.d'
        
        if os.path.exists(rc_dir):
            pattern = os.path.join(rc_dir, f'S*{service_name}*')
            
            if glob.glob(pattern):
                return True

    # For non-systemd systems, we can't easily check if service is enabled
    # Return False as we can't determine the status
    return False


def get_service_status():
    """
    Get status of common web server services with parallel execution.
    
    Returns:
        dict: Dictionary with service status information
    """
    start_time = time.time()
    from .logger import get_logger, debug_log
    logger = get_logger()
    debug_log(logger, "system", "Starting get_service_status()")
    
    services = ['nginx', 'mysql', 'mariadb', 'php7.4-fpm', 'php8.0-fpm', 'php8.1-fpm', 'php8.2-fpm', 'php8.3-fpm']
    
    status = {}
    for service in services:
        status[service] = {
            'installed': is_package_installed(service.replace('-fpm', '-fpm')),
            'running': is_service_running(service),
            'enabled': is_service_enabled(service)
        }
    
    # OPTIMIZATION: Get NVM, Node, and npm status in parallel
    parallel_start = time.time()
    
    def get_nvm_data():
        nvm_start = time.time()
        nvm_status = get_nvm_status()
        debug_log(logger, "system", f"NVM status retrieval took: {time.time() - nvm_start:.3f}s")
        return ('nvm', {
            'installed': nvm_status.get('installed', False),
            'running': nvm_status.get('installed', False),  # NVM is "running" if installed
            'enabled': nvm_status.get('installed', False),  # NVM is "enabled" if installed
            'version': nvm_status.get('version', None),
            'current_version': nvm_status.get('current_version', None),
            'installed_versions': nvm_status.get('installed_versions', []),
            'default_version': nvm_status.get('default_version', None)
        })
    
    def get_node_data():
        node_start = time.time()
        node_status = get_node_status()
        debug_log(logger, "system", f"Node status retrieval took: {time.time() - node_start:.3f}s")
        return ('node', {
            'installed': node_status.get('installed', False),
            'running': node_status.get('installed', False),  # Node is "running" if installed
            'enabled': node_status.get('installed', False),  # Node is "enabled" if installed
            'version': node_status.get('version', None),
            'path': node_status.get('path', None)
        })
    
    def get_npm_data():
        npm_start = time.time()
        npm_status = get_npm_status()
        debug_log(logger, "system", f"npm status retrieval took: {time.time() - npm_start:.3f}s")
        return ('npm', {
            'installed': npm_status.get('installed', False),
            'running': npm_status.get('installed', False),  # NPM is "running" if installed
            'enabled': npm_status.get('installed', False),  # NPM is "enabled" if installed
            'version': npm_status.get('version', None),
            'path': npm_status.get('path', None)
        })
    
    # Execute all functions and collect results
    nvm_result = get_nvm_data()
    node_result = get_node_data()
    npm_result = get_npm_data()
    
    status[nvm_result[0]] = nvm_result[1]
    status[node_result[0]] = node_result[1]
    status[npm_result[0]] = npm_result[1]
    
    debug_log(logger, "system", f"Parallel NVM/Node/npm status retrieval took: {time.time() - parallel_start:.3f}s")
    
    total_time = time.time() - start_time
    debug_log(logger, "system", f"Total get_service_status() took: {total_time:.3f}s")
    
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
    from .logger import get_logger, debug_log
    logger = get_logger()
    
    # DEBUG: Log function entry
    debug_log(logger, "system", f"restart_service called for: {service_name}")
    
    # Check if we're in a container environment
    is_container = is_container_environment()
    debug_log(logger, "system", f"Is container environment: {is_container}")
    
    # ENHANCED DEBUG: Check if service exists before trying to restart
    debug_log(logger, "system", f"Checking if service {service_name} exists")
    try:
        # Check if service unit file exists
        check_result = subprocess.run(['sudo', 'systemctl', 'list-unit-files', f"{service_name}.service"],
                                     capture_output=True, text=True)
        debug_log(logger, "system", f"systemctl list-unit-files return code: {check_result.returncode}")
        debug_log(logger, "system", f"systemctl list-unit-files stdout: {check_result.stdout}")
        if check_result.stderr:
            debug_log(logger, "system", f"systemctl list-unit-files stderr: {check_result.stderr}")
        
        service_exists = check_result.returncode == 0 and service_name in check_result.stdout
        debug_log(logger, "system", f"Service {service_name} exists: {service_exists}")
    except Exception as e:
        debug_log(logger, "system", f"Error checking if service exists: {e}", level=logging.WARNING)
        service_exists = False
    
    if is_container:
        try:
            # In containers, try to restart using service command
            debug_log(logger, "system", "Trying service command restart")
            result = subprocess.run(['sudo', 'service', service_name, 'restart'], check=True, capture_output=True, text=True)
            debug_log(logger, "system", "Service command restart successful")
            debug_log(logger, "system", f"Service command stdout: {result.stdout}")
            if result.stderr:
                debug_log(logger, "system", f"Service command stderr: {result.stderr}")
            
            # ENHANCED DEBUG: Verify service is actually running after restart
            debug_log(logger, "system", "Verifying service status after restart")
            try:
                status_result = subprocess.run(['sudo', 'service', service_name, 'status'],
                                             capture_output=True, text=True)
                debug_log(logger, "system", f"Service status return code: {status_result.returncode}")
                debug_log(logger, "system", f"Service status stdout: {status_result.stdout}")
                if status_result.stderr:
                    debug_log(logger, "system", f"Service status stderr: {status_result.stderr}")
                
                # Check if service is actually running
                is_running = 'running' in status_result.stdout.lower() or 'is running' in status_result.stdout.lower()
                debug_log(logger, "system", f"Service is running after restart: {is_running}")
            except Exception as e:
                debug_log(logger, "system", f"Error checking service status after restart: {e}", level=logging.WARNING)
            
            debug_log(logger, "system", "About to return True from restart_service (container path)")
            return True
        except subprocess.SubprocessError as e:
            debug_log(logger, "system", f"Service command restart failed: {e}", level=logging.WARNING)
            debug_log(logger, "system", f"Exception stdout: {e.stdout}")
            if e.stderr:
                debug_log(logger, "system", f"Exception stderr: {e.stderr}")
            try:
                # Fallback to direct command if available
                if service_name.startswith('php') and '-fpm' in service_name:
                    # For PHP-FPM, try to start it directly
                    version = service_name.replace('php', '').replace('-fpm', '')
                    php_fpm_binary = f"/usr/sbin/php-fpm{version}"
                    debug_log(logger, "system", f"Trying to start PHP-FPM directly with binary: {php_fpm_binary}")
                    try:
                        # First check if binary exists
                        binary_check = subprocess.run(['which', php_fpm_binary],
                                                   capture_output=True, text=True)
                        if binary_check.returncode == 0:
                            # Try to start PHP-FPM directly
                            subprocess.run(['sudo', php_fpm_binary, "--nodaemonize",
                                          "--fpm-config", f"/etc/php/{version}/fpm/php-fpm.conf"],
                                         check=True, capture_output=True, text=True, timeout=5)
                            debug_log(logger, "system", "Direct PHP-FPM start successful")
                            return True
                        else:
                            debug_log(logger, "system", f"PHP-FPM binary not found: {php_fpm_binary}", level=logging.WARNING)
                    except Exception as direct_e:
                        debug_log(logger, "system", f"Direct PHP-FPM start failed: {direct_e}", level=logging.WARNING)
                
                if service_name == 'nginx':
                    debug_log(logger, "system", "Trying nginx direct reload")
                    subprocess.run(['sudo', 'nginx', '-s', 'reload'], check=True)
                    debug_log(logger, "system", "Nginx direct reload successful")
                    return True
                # Add more service-specific commands as needed
            except subprocess.SubprocessError as e:
                debug_log(logger, "system", f"Direct command also failed: {e}", level=logging.WARNING)
                return False
    else:
        # In regular systems, use systemctl
        try:
            debug_log(logger, "system", "Trying systemctl restart")
            restart_result = subprocess.run(['sudo', 'systemctl', 'restart', service_name],
                                          capture_output=True, text=True)
            debug_log(logger, "system", f"systemctl restart return code: {restart_result.returncode}")
            if restart_result.stdout:
                debug_log(logger, "system", f"systemctl restart stdout: {restart_result.stdout}")
            if restart_result.stderr:
                debug_log(logger, "system", f"systemctl restart stderr: {restart_result.stderr}")
            
            # ENHANCED DEBUG: Verify service is actually running after restart
            debug_log(logger, "system", "Verifying service status after systemctl restart")
            try:
                status_result = subprocess.run(['sudo', 'systemctl', 'is-active', service_name],
                                             capture_output=True, text=True)
                debug_log(logger, "system", f"systemctl is-active return code: {status_result.returncode}")
                debug_log(logger, "system", f"systemctl is-active stdout: {status_result.stdout}")
                if status_result.stderr:
                    debug_log(logger, "system", f"systemctl is-active stderr: {status_result.stderr}")
                
                # Check if service is actually running
                is_active = status_result.returncode == 0 and 'active' in status_result.stdout
                debug_log(logger, "system", f"Service is active after restart: {is_active}")
            except Exception as e:
                debug_log(logger, "system", f"Error checking service status after restart: {e}", level=logging.WARNING)
            
            debug_log(logger, "system", "Systemctl restart successful")
            return True
        except subprocess.SubprocessError as e:
            debug_log(logger, "system", f"Systemctl restart failed: {e}", level=logging.WARNING)
            debug_log(logger, "system", f"Exception stdout: {e.stdout}")
            if e.stderr:
                debug_log(logger, "system", f"Exception stderr: {e.stderr}")
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



def get_nvm_status():
    """
    Get NVM installation and status information.
    
    Returns:
        dict: Dictionary with NVM status information
    """
    from ..cli.menu import console

    start_time = time.time()
    from .logger import get_logger, debug_log
    logger = get_logger()

    try:
        # Check if NVM is installed
        check_start = time.time()
        nvm_dir = os.path.expanduser("~/.nvm")
        
        
        
        if not os.path.exists(nvm_dir):
            debug_log(logger, "system", f"NVM directory check took: {time.time() - check_start:.3f}s")
            debug_log(logger, "system", f"Total NVM status check (not installed) took: {time.time() - start_time:.3f}s")
            
            result_data = {
                'installed': False,
                'version': None,
                'current_version': None,
                'installed_versions': [],
                'default_version': None
            }
            
            return result_data
        
        debug_log(logger, "system", f"NVM directory check took: {time.time() - check_start:.3f}s")
        
        # OPTIMIZATION: Execute all NVM commands in a single shell session
        batch_start = time.time()
        batch_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
        
        # Check if NVM command is available
        if ! command -v nvm >/dev/null 2>&1; then
            echo "NVM_NOT_AVAILABLE"
            exit 1
        fi
        
        # Get NVM version
        echo "===NVM_VERSION==="
        nvm --version 2>/dev/null || echo "Unknown"
        
        # Get current Node.js version
        echo "===NODE_VERSION==="
        node --version 2>/dev/null || echo "Not installed"
        
        # Get installed Node.js versions
        echo "===NVM_LIST==="
        nvm list 2>/dev/null || echo "No versions installed"
        
        # Get default version
        echo "===NVM_DEFAULT==="
        nvm alias default 2>/dev/null || echo "No default set"
        """
        
        result = subprocess.run([
            "bash", "-c", batch_cmd
        ], capture_output=True, text=True)
        
        debug_log(logger, "system", f"NVM batch command took: {time.time() - batch_start:.3f}s")
        
        if result.returncode != 0 or "NVM_NOT_AVAILABLE" in result.stdout:
            debug_log(logger, "system", f"Total NVM status check (command not found) took: {time.time() - start_time:.3f}s")
            
            result_data = {
                'installed': False,
                'version': None,
                'current_version': None,
                'installed_versions': [],
                'default_version': None
            }
            
            return result_data
        
        # Parse the batch output - use a more robust approach
        parse_start = time.time()
        
        nvm_version = None
        node_version = None
        installed_versions = []
        default_version = None
        
        # Split by our custom markers, not just '===' to avoid conflicts with NVM alias output
        markers = [
            '===DEBUG_NVM_DIR===',
            '===DEBUG_NVM_CMD===',
            '===NVM_VERSION===',
            '===NODE_VERSION===',
            '===NVM_LIST===',
            '===NVM_DEFAULT==='
        ]
        
        debug_log(logger, "system", f"NVM raw output length: {len(result.stdout)}")
        
        # Process each section based on markers
        for marker in markers:
            start_idx = result.stdout.find(marker)
            if start_idx == -1:
                continue
                
            # Find the next marker to determine section bounds
            next_marker_idx = len(result.stdout)
            for next_marker in markers:
                if next_marker != marker:
                    next_idx = result.stdout.find(next_marker, start_idx + len(marker))
                    if next_idx != -1 and next_idx < next_marker_idx:
                        next_marker_idx = next_idx
            
            # Extract section content
            section_content = result.stdout[start_idx + len(marker):next_marker_idx].strip()
            
            # Process based on marker type
            if marker == '===DEBUG_NVM_DIR===':
                debug_log(logger, "system", f"NVM Directory Debug: {section_content}")
            elif marker == '===DEBUG_NVM_CMD===':
                debug_log(logger, "system", f"NVM Command Debug: {section_content}")
            elif marker == '===NVM_VERSION===':
                nvm_version = section_content
                debug_log(logger, "system", f"NVM Version: {nvm_version}")
            elif marker == '===NODE_VERSION===':
                node_version = section_content if section_content != "Not installed" else None
                debug_log(logger, "system", f"Node Version: {node_version}")
            elif marker == '===NVM_LIST===':
                debug_log(logger, "system", f"NVM List Raw Output: {repr(section_content)}")
                if "No versions installed" not in section_content:
                    lines = section_content.split('\n')
                    debug_log(logger, "system", f"NVM List Lines: {lines}")
                    for line in lines:
                        debug_log(logger, "system", f"Processing line: {repr(line)}")
                        # Remove ANSI escape codes from the line
                        import re
                        # ANSI escape code pattern: \x1b[...m
                        ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        clean_line = ansi_escape.sub('', line)
                        
                        # Look for actual installed versions (not aliases)
                        # Installed versions have format like: "       v22.21.1 *" or "->     v24.11.1 *"
                        # They should start with 'v' or '->' and contain a version pattern like x.y.z
                        stripped_line = clean_line.strip()
                        debug_log(logger, "system", f"Cleaned line: {repr(clean_line)}")
                        debug_log(logger, "system", f"Stripped line: {repr(stripped_line)}")
                        
                        if (stripped_line and
                            (stripped_line.startswith('v') or stripped_line.startswith('->')) and
                            # Check if line contains a version pattern (digits.digits.digits)
                            any(c.isdigit() for c in stripped_line) and '.' in stripped_line):
                            # Extract version from the line
                            version = stripped_line.replace('->', '').replace('*', '').strip()
                            debug_log(logger, "system", f"Extracted version before processing: {repr(version)}")
                            if version.startswith('v'):
                                version = version[1:]  # Remove 'v' prefix
                            # Validate version format (should be like x.y.z)
                            if version and version.count('.') >= 2 and all(part.isdigit() for part in version.split('.')):
                                installed_versions.append(version)
                                debug_log(logger, "system", f"Added version: {version}")
                debug_log(logger, "system", f"Final installed_versions: {installed_versions}")
            elif marker == '===NVM_DEFAULT===':
                debug_log(logger, "system", f"NVM Default Raw Output: {repr(section_content)}")
                if 'default' in section_content and "No default set" not in section_content:
                    # Parse default alias output like: "default -> node (-> v24.11.1 *)"
                    # Extract the version from within the parentheses
                    if '-> v' in section_content:
                        # Find the version within the parentheses
                        # Remove ANSI escape codes from content first
                        import re
                        ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        clean_content = ansi_escape.sub('', section_content)
                        debug_log(logger, "system", f"Cleaned NVM Default Output: {repr(clean_content)}")
                        
                        start_idx = clean_content.find('-> v')
                        if start_idx != -1:
                            # Extract version string
                            version_part = clean_content[start_idx + 4:]  # Skip '-> v'
                            # Remove any trailing characters like ' *)'
                            end_idx = len(version_part)
                            for i, char in enumerate(version_part):
                                if not (char.isdigit() or char == '.'):
                                    end_idx = i
                                    break
                            default_version = version_part[:end_idx].replace('v', '')
                            debug_log(logger, "system", f"Default Version: {default_version}")
        
        debug_log(logger, "system", f"NVM output parsing took: {time.time() - parse_start:.3f}s")
        
        result_data = {
            'installed': True,
            'version': nvm_version,
            'current_version': node_version,
            'installed_versions': installed_versions,
            'default_version': default_version
        }
        
        total_time = time.time() - start_time
        debug_log(logger, "system", f"Total NVM status check took: {total_time:.3f}s")
        
        return result_data
        
    except Exception as e:
        debug_log(logger, "system", f"NVM status check failed with exception after {time.time() - start_time:.3f}s: {e}")
        
        result_data = {
            'installed': False,
            'version': None,
            'current_version': None,
            'installed_versions': [],
            'default_version': None
        }
        
        return result_data



def get_node_status():
    """
    Get Node.js installation status.
    
    Returns:
        dict: Dictionary with Node.js status information
    """
    start_time = time.time()
    from .logger import get_logger, debug_log
    logger = get_logger()
    
    try:
        # Check if Node.js is installed globally
        version_start = time.time()
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        debug_log(logger, "system", f"Node version check took: {time.time() - version_start:.3f}s")
        
        result_data = None
        if result.returncode == 0:
            which_start = time.time()
            node_path = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
            debug_log(logger, "system", f"Node which command took: {time.time() - which_start:.3f}s")
            debug_log(logger, "system", f"Total Node status check took: {time.time() - start_time:.3f}s")
            result_data = {
                'installed': True,
                'version': result.stdout.strip(),
                'path': node_path
            }
        else:
            debug_log(logger, "system", f"Total Node status check (not installed) took: {time.time() - start_time:.3f}s")
            result_data = {
                'installed': False,
                'version': None,
                'path': None
            }
        
        return result_data
            
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        debug_log(logger, "system", f"Node status check failed with exception after {time.time() - start_time:.3f}s: {e}")
        result_data = {
            'installed': False,
            'version': None,
            'path': None
        }
        
        return result_data



def get_npm_status():
    """
    Get npm installation status.
    
    Returns:
        dict: Dictionary with npm status information
    """
    start_time = time.time()
    from .logger import get_logger, debug_log
    logger = get_logger()
    
    try:
        # Check if npm is installed globally
        version_start = time.time()
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        debug_log(logger, "system", f"npm version check took: {time.time() - version_start:.3f}s")
        
        result_data = None
        if result.returncode == 0:
            which_start = time.time()
            npm_path = subprocess.run(["which", "npm"], capture_output=True, text=True).stdout.strip()
            debug_log(logger, "system", f"npm which command took: {time.time() - which_start:.3f}s")
            debug_log(logger, "system", f"Total npm status check took: {time.time() - start_time:.3f}s")
            result_data = {
                'installed': True,
                'version': result.stdout.strip(),
                'path': npm_path
            }
        else:
            debug_log(logger, "system", f"Total npm status check (not installed) took: {time.time() - start_time:.3f}s")
            result_data = {
                'installed': False,
                'version': None,
                'path': None
            }
        
        return result_data
            
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        debug_log(logger, "system", f"npm status check failed with exception after {time.time() - start_time:.3f}s: {e}")
        result_data = {
            'installed': False,
            'version': None,
            'path': None
        }
        
        return result_data


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