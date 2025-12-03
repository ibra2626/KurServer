"""
Nginx installer module for KurServer CLI.
"""

import os
import subprocess
from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import get_system_info, get_disk_space, is_package_installed, is_service_running
from ..core.exceptions import SystemRequirementError

logger = get_logger()


def install_nginx_menu(verbose: bool = False) -> None:
    """
    Handle Nginx installation from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Nginx Installation[/bold blue]")
    console.print("This will install and configure Nginx web server on your Ubuntu system.")
    console.print()
    
    # System preparation checks
    if not _check_system_requirements(verbose):
        console.print("[red]System requirements not met. Cannot proceed with installation.[/red]")
        return
    
    # Check if already installed
    if is_package_installed('nginx'):
        if not confirm_action("Nginx is already installed. Do you want to reinstall?"):
            return
    
    # Check for conflicting web servers
    if _check_conflicting_servers():
        if not confirm_action("Conflicting web servers detected. Continue anyway?"):
            console.print("[yellow]Installation cancelled.[/yellow]")
            return
    
    # Get installation preferences
    console.print("[bold]Installation Options:[/bold]")
    
    # Ask about basic configuration
    enable_security = confirm_action("Enable security hardening?", default=True)
    enable_performance = confirm_action("Enable performance optimization?", default=True)
    
    # Ask for confirmation
    if not confirm_action("Do you want to proceed with Nginx installation?"):
        console.print("[yellow]Installation cancelled.[/yellow]")
        return
    
    try:
        # Perform installation with progress
        show_progress(
            "Installing Nginx...",
            _install_nginx,
            verbose, enable_security, enable_performance
        )
        
        console.print("[bold green]✓ Nginx installation completed successfully![/bold green]")
        
        # Test installation
        if _test_nginx_installation(verbose):
            console.print("[bold green]✓ Nginx installation validated successfully![/bold green]")
        else:
            console.print("[yellow]⚠ Nginx installed but validation failed. Please check logs.[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"Nginx installation failed: {e}")


def _check_system_requirements(verbose: bool = False) -> bool:
    """
    Check if system meets requirements for Nginx installation.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if requirements are met, False otherwise
    """
    from ..cli.menu import console
    
    if verbose:
        console.print("[bold]Checking system requirements...[/bold]")
    
    try:
        # Check Ubuntu version
        system_info = get_system_info()
        if system_info.get('distro') != 'ubuntu':
            console.print("[red]Ubuntu Linux is required.[/red]")
            return False
        
        # Check disk space (minimum 1GB free)
        disk_space = get_disk_space('/')
        if disk_space['available'] < 1024 * 1024 * 1024:  # 1GB in bytes
            console.print("[red]Insufficient disk space. At least 1GB free space required.[/red]")
            return False
        
        # Check memory (minimum 512MB)
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        if mem_kb < 512 * 1024:  # 512MB in KB
                            console.print("[red]Insufficient memory. At least 512MB RAM required.[/red]")
                            return False
                        break
        except FileNotFoundError:
            console.print("[yellow]Could not check memory requirements.[/yellow]")
        
        if verbose:
            console.print("[green]✓ System requirements check passed[/green]")
        
        return True
        
    except Exception as e:
        logger.error(f"System requirements check failed: {e}")
        console.print(f"[red]Error checking system requirements: {e}[/red]")
        return False


def _check_conflicting_servers() -> bool:
    """
    Check for conflicting web servers.
    
    Returns:
        bool: True if conflicts found, False otherwise
    """
    from ..cli.menu import console
    
    conflicting_servers = []
    
    # Check for Apache
    if is_package_installed('apache2'):
        conflicting_servers.append('Apache2')
    
    # Check for other common web servers
    if is_package_installed('lighttpd'):
        conflicting_servers.append('Lighttpd')
    
    if is_package_installed('httpd'):
        conflicting_servers.append('HTTPD')
    
    if conflicting_servers:
        console.print(f"[yellow]Warning: Found conflicting web servers: {', '.join(conflicting_servers)}[/yellow]")
        return True
    
    return False


def _install_nginx(verbose: bool = False, enable_security: bool = True, enable_performance: bool = True) -> None:
    """
    Actually install Nginx with configuration options.
    
    Args:
        verbose (bool): Enable verbose output
        enable_security (bool): Enable security hardening
        enable_performance (bool): Enable performance optimization
    """
    # Update package lists
    if verbose:
        logger.info("Updating package lists...")
    
    result = subprocess.run(
        ["sudo", "apt", "update"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to update package lists: {result.stderr}")
    
    # Install Nginx
    if verbose:
        logger.info("Installing Nginx package...")
    
    result = subprocess.run(
        ["sudo", "apt", "install", "-y", "nginx"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to install Nginx: {result.stderr}")
    
    # Backup original configuration if Nginx is already installed
    if is_package_installed('nginx') and os.path.exists('/etc/nginx'):
        if verbose:
            logger.info("Backing up existing Nginx configuration...")
        
        _backup_nginx_config(verbose)
    
    # Apply basic configuration
    if verbose:
        logger.info("Applying basic Nginx configuration...")
    
    _configure_nginx_basic(enable_performance, verbose)
    
    # Apply security hardening if requested
    if enable_security:
        if verbose:
            logger.info("Applying security hardening...")
        
        _configure_nginx_security(verbose)
    
    # Configure log rotation
    if verbose:
        logger.info("Configuring log rotation...")
    
    _configure_log_rotation(verbose)
    
    # Enable and start Nginx service
    if verbose:
        logger.info("Enabling and starting Nginx service...")
    
    # Enable service (only available on systemd)
    if _is_systemd_available():
        subprocess.run(["sudo", "systemctl", "enable", "nginx"], check=True)
        # Start service with systemd
        subprocess.run(["sudo", "systemctl", "start", "nginx"], check=True)
    else:
        if verbose:
            logger.info("Using service command for non-systemd system")
        # Fallback for non-systemd systems
        subprocess.run(["sudo", "service", "nginx", "start"], check=True)
    
    logger.info("Nginx installation completed successfully")


def _backup_nginx_config(verbose: bool = False) -> None:
    """
    Create backup of original Nginx configuration.
    
    Args:
        verbose (bool): Enable verbose output
    """
    import datetime
    
    # Check if nginx directory exists and has content
    if not os.path.exists('/etc/nginx') or not os.listdir('/etc/nginx'):
        if verbose:
            logger.info("No existing Nginx configuration to backup")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"/etc/nginx.backup.{timestamp}"
    
    try:
        # Create backup directory
        subprocess.run(["sudo", "mkdir", "-p", backup_dir], check=True)
        
        # Copy configuration files
        subprocess.run(["sudo", "cp", "-r", "/etc/nginx/*", backup_dir], check=True)
        
        if verbose:
            logger.info(f"Nginx configuration backed up to {backup_dir}")
    
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to backup Nginx configuration: {e}")
        if verbose:
            logger.info("Continuing with installation without backup")


def _configure_nginx_basic(enable_performance: bool = True, verbose: bool = False) -> None:
    """
    Apply basic Nginx configuration with performance optimization.
    
    Args:
        enable_performance (bool): Enable performance optimizations
        verbose (bool): Enable verbose output
    """
    # Create optimized nginx.conf
    nginx_conf = """# Nginx configuration optimized by KurServer CLI

user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
    # multi_accept on;
}

http {
    ##
    # Basic Settings
    ##
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # server_names_hash_bucket_size 64;
    # server_name_in_redirect off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ##
    # SSL Settings
    ##
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    ##
    # Logging Settings
    ##
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    ##
    # Gzip Settings
    ##
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    ##
    # Virtual Host Configs
    ##
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
"""
    
    if enable_performance:
        # Add performance optimizations
        nginx_conf = nginx_conf.replace(
            "    worker_connections 768;",
            """    worker_connections 1024;
    multi_accept on;"""
        )
        
        # Add performance settings to http block
        perf_settings = """
    ##
    # Performance Optimizations
    ##
    client_max_body_size 20M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;
    
    # File cache settings
    open_file_cache max=2000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
"""
        nginx_conf = nginx_conf.replace("    ##\n    # Gzip Settings\n    ##", perf_settings + "    ##\n    # Gzip Settings\n    ##")
    
    # Write configuration to temp file
    with open('/tmp/nginx.conf', 'w') as f:
        f.write(nginx_conf)
    
    # Move to nginx directory
    subprocess.run(["sudo", "mv", "/tmp/nginx.conf", "/etc/nginx/nginx.conf"], check=True)
    
    if verbose:
        logger.info("Basic Nginx configuration applied")


def _configure_nginx_security(verbose: bool = False) -> None:
    """
    Apply security hardening to Nginx configuration.
    
    Args:
        verbose (bool): Enable verbose output
    """
    # Create security configuration with only http-level directives
    security_conf = r"""# Security hardening configuration by KurServer CLI

# Security headers (applied to all servers)
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
"""
    
    # Write security configuration
    with open('/tmp/security.conf', 'w') as f:
        f.write(security_conf)
    
    # Move to nginx conf.d directory
    subprocess.run(["sudo", "mv", "/tmp/security.conf", "/etc/nginx/conf.d/security.conf"], check=True)
    
    if verbose:
        logger.info("Security hardening configuration applied")


def _configure_log_rotation(verbose: bool = False) -> None:
    """
    Configure log rotation for Nginx.
    
    Args:
        verbose (bool): Enable verbose output
    """
    logrotate_conf = """# Nginx log rotation configuration by KurServer CLI

/var/log/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
"""
    
    # Write logrotate configuration
    with open('/tmp/nginx', 'w') as f:
        f.write(logrotate_conf)
    
    # Move to logrotate.d directory
    subprocess.run(["sudo", "mv", "/tmp/nginx", "/etc/logrotate.d/nginx"], check=True)
    
    if verbose:
        logger.info("Log rotation configuration applied")


def _test_nginx_installation(verbose: bool = False) -> bool:
    """
    Test Nginx installation and configuration.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if tests pass, False otherwise
    """
    try:
        # Test configuration syntax
        if verbose:
            logger.info("Testing Nginx configuration syntax...")
        
        result = subprocess.run(
            ["sudo", "nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Nginx configuration test failed: {result.stderr}")
            return False
        
        # Check if service is running
        if verbose:
            logger.info("Checking Nginx service status...")
        
        if not is_service_running('nginx'):
            logger.error("Nginx service is not running")
            return False
        
        # Test basic HTTP response
        if verbose:
            logger.info("Testing HTTP response...")
        
        import urllib.request
        import urllib.error
        
        try:
            response = urllib.request.urlopen('http://localhost', timeout=5)
            if response.getcode() == 200:
                if verbose:
                    logger.info("HTTP response test passed")
                return True
        except urllib.error.URLError as e:
            logger.error(f"HTTP response test failed: {e}")
            return False
        
        return False
        
    except Exception as e:
        logger.error(f"Nginx installation test failed: {e}")
        return False


def nginx_service_manager(action: str, verbose: bool = False) -> bool:
    """
    Manage Nginx service (start, stop, restart, reload, status).
    
    Args:
        action (str): Service action (start, stop, restart, reload, status)
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if operation successful, False otherwise
    """
    from ..cli.menu import console
    
    valid_actions = ['start', 'stop', 'restart', 'reload', 'status']
    
    if action not in valid_actions:
        console.print(f"[red]Invalid action: {action}. Valid actions: {', '.join(valid_actions)}[/red]")
        return False
    
    try:
        if action == 'status':
            # Get service status
            if is_service_running('nginx'):
                console.print("[green]Nginx service is running[/green]")
                
                # Get additional status information
                if _is_systemd_available():
                    result = subprocess.run(
                        ["sudo", "systemctl", "status", "nginx", "--no-pager"],
                        capture_output=True,
                        text=True
                    )
                    
                    if verbose and result.returncode == 0:
                        console.print(result.stdout)
                else:
                    # Fallback for non-systemd systems
                    result = subprocess.run(
                        ["sudo", "service", "nginx", "status"],
                        capture_output=True,
                        text=True
                    )
                    
                    if verbose and result.returncode == 0:
                        console.print(result.stdout)
                
                return True
            else:
                console.print("[red]Nginx service is not running[/red]")
                return False
        else:
            # Perform service action
            if verbose:
                logger.info(f"Performing Nginx service action: {action}")
            
            if _is_systemd_available():
                result = subprocess.run(
                    ["sudo", "systemctl", action, "nginx"],
                    capture_output=True,
                    text=True
                )
            else:
                # Fallback for non-systemd systems
                if action == 'reload':
                    # Use service command for reload
                    result = subprocess.run(
                        ["sudo", "service", "nginx", "reload"],
                        capture_output=True,
                        text=True
                    )
                else:
                    result = subprocess.run(
                        ["sudo", "service", "nginx", action],
                        capture_output=True,
                        text=True
                    )
            
            if result.returncode == 0:
                console.print(f"[green]✓ Nginx service {action} successful[/green]")
                return True
            else:
                console.print(f"[red]✗ Failed to {action} Nginx service: {result.stderr}[/red]")
                return False
    
    except Exception as e:
        console.print(f"[red]✗ Service management error: {e}[/red]")
        logger.error(f"Nginx service management error: {e}")
        return False


def _is_systemd_available() -> bool:
    """
    Check if systemd is available on the system.
    
    Returns:
        bool: True if systemd is available, False otherwise
    """
    try:
        # Check if systemd is the init system
        result = subprocess.run(
            ["ps", "-p", "1", "-o", "comm="],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip() == 'systemd':
            # Additional check: verify systemd is actually functional
            result2 = subprocess.run(
                ["systemctl", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result2.returncode == 0
        
        return False
    
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def validate_nginx_config(verbose: bool = False) -> bool:
    """
    Validate Nginx configuration syntax.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    from ..cli.menu import console
    
    try:
        if verbose:
            logger.info("Validating Nginx configuration...")
        
        result = subprocess.run(
            ["sudo", "nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("[green]✓ Nginx configuration is valid[/green]")
            if verbose:
                console.print(result.stdout)
            return True
        else:
            console.print("[red]✗ Nginx configuration validation failed[/red]")
            console.print(result.stderr)
            return False
    
    except Exception as e:
        console.print(f"[red]✗ Configuration validation error: {e}[/red]")
        logger.error(f"Nginx configuration validation error: {e}")
        return False


def get_nginx_info(verbose: bool = False) -> dict:
    """
    Get comprehensive Nginx information.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Dictionary with Nginx information
    """
    from ..cli.menu import console
    
    info = {
        'installed': is_package_installed('nginx'),
        'running': is_service_running('nginx'),
        'version': None,
        'config_valid': None,
        'sites_count': 0,
        'active_sites': []
    }
    
    if not info['installed']:
        return info
    
    try:
        # Get Nginx version
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
        
        # Validate configuration
        info['config_valid'] = validate_nginx_config(verbose)
        
        # Get enabled sites
        result = subprocess.run(
            ["ls", "/etc/nginx/sites-enabled/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            sites = result.stdout.strip().split('\n')
            info['sites_count'] = len(sites)
            info['active_sites'] = [site for site in sites if site and site != 'default']
        
        if verbose:
            console.print("[bold]Nginx Information:[/bold]")
            console.print(f"  Installed: {'Yes' if info['installed'] else 'No'}")
            console.print(f"  Version: {info['version'] or 'Unknown'}")
            console.print(f"  Running: {'Yes' if info['running'] else 'No'}")
            console.print(f"  Config Valid: {'Yes' if info['config_valid'] else 'No'}")
            console.print(f"  Active Sites: {info['sites_count']}")
            
            if info['active_sites']:
                console.print("  Site List:")
                for site in info['active_sites']:
                    console.print(f"    • {site}")
    
    except Exception as e:
        logger.error(f"Error getting Nginx info: {e}")
    
    return info