"""
PHP-FPM installer module for KurServer CLI.
"""

from ..core.logger import get_logger, debug_log
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import is_package_installed, restart_service
from ..core.exceptions import PackageInstallationError

logger = get_logger()


def install_php_menu(verbose: bool = False) -> None:
    """
    Handle PHP-FPM installation from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]PHP-FPM Installation[/bold blue]")
    console.print("This will install and configure PHP-FPM on your Ubuntu system.")
    console.print()
    
    # Ask which PHP version to install
    php_choice = get_user_input(
        "Which PHP version would you like to install?",
        choices=["7.4", "8.0", "8.1", "8.2", "8.3"],
        default="8.3"
    )
    
    # Check if already installed
    php_package = f"php{php_choice}-fpm"
    if is_package_installed(php_package):
        if not confirm_action(f"PHP {php_choice} is already installed. Do you want to reinstall?"):
            return
    
    # Ask about extensions
    console.print(f"[bold]PHP {php_choice} Installation Options:[/bold]")
    install_extensions = confirm_action("Do you want to install PHP extensions?")
    
    # Ask for confirmation
    if not confirm_action(f"Do you want to proceed with PHP {php_choice} installation?"):
        console.print("[yellow]Installation cancelled.[/yellow]")
        return
    
    try:
        # Perform installation with progress
        show_progress(
            f"Installing PHP {php_choice}...",
            _install_php,
            php_choice,
            install_extensions,
            verbose
        )
        
        console.print(f"[bold green]✓ PHP {php_choice} installation completed successfully![/bold green]")
        
        # Configure PHP-FPM
        try:
            show_progress(
                "Configuring PHP-FPM...",
                _configure_php_fpm,
                php_choice,
                verbose
            )
            console.print("[green]✓ PHP-FPM configured![/green]")
        except Exception as e:
            console.print(f"[red]✗ PHP-FPM configuration failed:[/red] {e}")
            if "not installed properly" in str(e):
                console.print(f"[yellow]This usually means PHP {php_choice} installation was incomplete.[/yellow]")
                console.print(f"[yellow]Please check if PHP {php_choice}-FPM is properly installed.[/yellow]")
            logger.error(f"PHP-FPM configuration failed: {e}")
            # Don't re-raise the exception, just continue with a warning
            console.print("[yellow]Continuing with installation...[/yellow]")
        
        # Install extensions if requested
        if install_extensions:
            console.print("[bold]Installing PHP extensions...[/bold]")
            try:
                _install_extensions_interactive(php_choice, verbose)
                console.print("[green]✓ PHP extensions installed![/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to install PHP extensions:[/red] {e}")
                logger.error(f"PHP extensions installation failed: {e}")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"PHP {php_choice} installation failed: {e}")


def _install_php(version: str, install_extensions: bool, verbose: bool = False) -> None:
    """
    Actually install PHP-FPM.
    
    Args:
        version (str): PHP version to install
        install_extensions (bool): Whether to install common extensions
        verbose (bool): Enable verbose output
    """
    import subprocess
    from ..utils.package import update_package_lists, fix_dpkg_interruption
    
    # First try to fix any dpkg interruptions
    if not fix_dpkg_interruption(verbose):
        raise Exception("Failed to fix dpkg interruptions")
    
    # Update package lists
    if not update_package_lists(verbose):
        raise Exception("Failed to update package lists")
    
    # Add PPA for older PHP versions if needed
    if version in ["7.4", "8.0", "8.1", "8.2"]:
        if verbose:
            logger.info("Adding PHP PPA for older versions...")
        
        # Add PPA
        subprocess.run([
            "sudo", "apt", "install", "-y", "software-properties-common"
        ], check=True)
        
        subprocess.run([
            "sudo", "add-apt-repository", "-y", "ppa:ondrej/php"
        ], check=True)
        
        # Update package lists again after adding PPA
        if not update_package_lists(verbose):
            raise Exception("Failed to update package lists after adding PPA")
    
    # Install PHP-FPM
    if verbose:
        logger.info(f"Installing PHP {version} FPM package...")
    
    php_package = f"php{version}-fpm"
    
    # Try installation with better error handling
    try:
        result = subprocess.run(
            ["sudo", "apt", "install", "-y", php_package],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Check if it's a dpkg interruption error
        if "dpkg was interrupted" in e.stderr:
            # Try to fix dpkg and retry
            if verbose:
                logger.info("Detected dpkg interruption, attempting to fix...")
            
            if not fix_dpkg_interruption(verbose):
                raise Exception(f"Failed to fix dpkg interruption: {e.stderr}")
            
            # Retry the installation
            if verbose:
                logger.info(f"Retrying {php_package} installation...")
            
            result = subprocess.run(
                ["sudo", "apt", "install", "-y", php_package],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Re-raise the original error
            raise Exception(f"Failed to install {php_package}: {e.stderr}")
    
    # Install common extensions if requested
    if install_extensions:
        if verbose:
            logger.info("Installing common PHP extensions...")
        
        extensions = [
            f"php{version}-mysql",
            f"php{version}-xml",
            f"php{version}-mbstring",
            f"php{version}-curl",
            f"php{version}-zip",
            f"php{version}-gd",
            f"php{version}-intl",
            f"php{version}-bcmath"
            # JSON is built-in from PHP 8.0+
        ]
        
        for ext in extensions:
            try:
                subprocess.run(["sudo", "apt", "install", "-y", ext], check=True)
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to install extension: {ext}")
    
    # Enable and start service
    if verbose:
        logger.info(f"Enabling and starting PHP {version}-FPM service...")
    
    # ENHANCED DEBUG: Log service startup attempts
    debug_log(logger, "php", f"Attempting to start PHP {version}-FPM service")
    debug_log(logger, "php", f"PHP package name: {php_package}")
    
    # Check if we're in a Docker container (no systemd)
    try:
        # Try to enable service
        debug_log(logger, "php", f"Trying to enable {php_package} with systemctl")
        enable_result = subprocess.run(["sudo", "systemctl", "enable", php_package],
                                     capture_output=True, text=True)
        debug_log(logger, "php", f"systemctl enable return code: {enable_result.returncode}")
        if enable_result.stdout:
            debug_log(logger, "php", f"systemctl enable stdout: {enable_result.stdout}")
        if enable_result.stderr:
            debug_log(logger, "php", f"systemctl enable stderr: {enable_result.stderr}")
        
        # Try to start service
        debug_log(logger, "php", f"Trying to start {php_package} with systemctl")
        start_result = subprocess.run(["sudo", "systemctl", "start", php_package],
                                    capture_output=True, text=True)
        debug_log(logger, "php", f"systemctl start return code: {start_result.returncode}")
        if start_result.stdout:
            debug_log(logger, "php", f"systemctl start stdout: {start_result.stdout}")
        if start_result.stderr:
            debug_log(logger, "php", f"systemctl start stderr: {start_result.stderr}")
        
        # Verify service is running
        debug_log(logger, "php", f"Verifying if {php_package} is running after systemctl start")
        try:
            status_result = subprocess.run(["sudo", "systemctl", "is-active", php_package],
                                        capture_output=True, text=True)
            debug_log(logger, "php", f"systemctl is-active return code: {status_result.returncode}")
            debug_log(logger, "php", f"systemctl is-active stdout: {status_result.stdout}")
            if status_result.stderr:
                debug_log(logger, "php", f"systemctl is-active stderr: {status_result.stderr}")
        except Exception as e:
            logger.warning(f"[DEBUG] Error checking service status: {e}")
        
        if verbose:
            logger.info(f"PHP {version}-FPM service started with systemd")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        debug_log(logger, "php", f"Systemd method failed: {e}")
        # Fallback for containers without systemd
        if verbose:
            logger.info("Systemd not available, using service command fallback...")
        
        try:
            # Try using service command
            debug_log(logger, "php", f"Trying to start {php_package} with service command")
            service_result = subprocess.run(["sudo", "service", php_package, "start"],
                                          capture_output=True, text=True)
            debug_log(logger, "php", f"service start return code: {service_result.returncode}")
            if service_result.stdout:
                debug_log(logger, "php", f"service start stdout: {service_result.stdout}")
            if service_result.stderr:
                debug_log(logger, "php", f"service start stderr: {service_result.stderr}")
            
            # Verify service is running
            debug_log(logger, "php", f"Verifying if {php_package} is running after service start")
            try:
                status_result = subprocess.run(["sudo", "service", php_package, "status"],
                                            capture_output=True, text=True)
                debug_log(logger, "php", f"service status return code: {status_result.returncode}")
                debug_log(logger, "php", f"service status stdout: {status_result.stdout}")
                if status_result.stderr:
                    debug_log(logger, "php", f"service status stderr: {status_result.stderr}")
            except Exception as e:
                logger.warning(f"[DEBUG] Error checking service status: {e}")
            
            if verbose:
                logger.info(f"PHP {version}-FPM service started with service command")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            debug_log(logger, "php", f"Service command also failed: {e}")
            # Last resort: try to start the PHP-FPM process directly
            try:
                php_fpm_binary = f"/usr/sbin/php-fpm{version}"
                debug_log(logger, "php", f"Trying to start PHP-FPM directly with binary: {php_fpm_binary}")
                direct_result = subprocess.run(["sudo", php_fpm_binary, "--nodaemonize", "--fpm-config", f"/etc/php/{version}/fpm/php-fpm.conf"],
                                              capture_output=True, text=True, timeout=5)
                debug_log(logger, "php", f"Direct PHP-FPM start return code: {direct_result.returncode}")
                if direct_result.stdout:
                    debug_log(logger, "php", f"Direct PHP-FPM start stdout: {direct_result.stdout}")
                if direct_result.stderr:
                    debug_log(logger, "php", f"Direct PHP-FPM start stderr: {direct_result.stderr}")
                if verbose:
                    logger.info(f"PHP {version}-FPM started directly")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                debug_log(logger, "php", f"Direct PHP-FPM start also failed: {e}")
                logger.warning(f"Could not start PHP {version}-FPM service (this is normal in containers)")
    
    logger.info(f"PHP {version} installation completed successfully")


def _configure_php_fpm(version: str, verbose: bool = False) -> None:
    """
    Configure PHP-FPM with optimized settings.
    
    Args:
        version (str): PHP version to configure
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    import traceback
    
    if verbose:
        logger.info(f"Configuring PHP {version}-FPM...")
    
    # DEBUG: Log function entry
    debug_log(logger, "php", f"Starting PHP-FPM configuration for version {version}")
    
    # ENHANCED DEBUG: Log system environment
    debug_log(logger, "php", "System environment:")
    debug_log(logger, "php", f"  Current working directory: {os.getcwd()}")
    debug_log(logger, "php", f"  User ID: {os.getuid()}")
    debug_log(logger, "php", f"  Effective User ID: {os.geteuid()}")
    debug_log(logger, "php", f"  Python executable: {os.sys.executable}")
    
    # Get system memory for tuning calculations
    total_memory_mb = 2048  # Default to 2GB if unable to detect
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    mem_kb = int(line.split()[1])
                    total_memory_mb = mem_kb // 1024
                    break
    except:
        pass  # Keep default value if unable to detect

    # Calculate appropriate values based on available memory
    if total_memory_mb < 1024:  # Less than 1GB
        max_children = "5"
        start_servers = "2"
        min_spare_servers = "1"
        max_spare_servers = "3"
    elif total_memory_mb < 2048:  # 1-2GB
        max_children = "10"
        start_servers = "4"
        min_spare_servers = "2"
        max_spare_servers = "6"
    elif total_memory_mb < 4096:  # 2-4GB
        max_children = "20"
        start_servers = "8"
        min_spare_servers = "4"
        max_spare_servers = "12"
    else:  # 4GB+
        max_children = "50"
        start_servers = "20"
        min_spare_servers = "10"
        max_spare_servers = "30"
    
    # Path to PHP-FPM configuration file
    pool_config = f"/etc/php/{version}/fpm/pool.d/www.conf"
    
    # DEBUG: Check if configuration file exists
    debug_log(logger, "php", f"Checking if PHP-FPM config exists: {pool_config}")
    
    # ENHANCED DEBUG: Check directory structure
    php_dir = f"/etc/php/{version}"
    fpm_dir = f"/etc/php/{version}/fpm"
    pool_dir = f"/etc/php/{version}/fpm/pool.d"
    
    debug_log(logger, "php", "Checking directory structure:")
    debug_log(logger, "php", f"  PHP directory exists: {os.path.exists(php_dir)}")
    debug_log(logger, "php", f"  FPM directory exists: {os.path.exists(fpm_dir)}")
    debug_log(logger, "php", f"  Pool directory exists: {os.path.exists(pool_dir)}")
    
    if os.path.exists(pool_dir):
        debug_log(logger, "php", "Files in pool directory:")
        try:
            for file in os.listdir(pool_dir):
                debug_log(logger, "php", f"    {file}")
        except PermissionError as e:
            logger.error(f"[DEBUG] Permission error reading pool directory: {e}")
    
    if not os.path.exists(pool_config):
        logger.error(f"[DEBUG] PHP-FPM config file not found: {pool_config}")
        debug_log(logger, "php", f"This likely means PHP {version} is not installed properly")
        
        # ENHANCED DEBUG: Check if PHP package is installed
        php_package = f"php{version}-fpm"
        try:
            result = subprocess.run(["dpkg", "-l", php_package], capture_output=True, text=True)
            debug_log(logger, "php", f"dpkg -l {php_package} result: {result.returncode}")
            debug_log(logger, "php", f"dpkg output: {result.stdout}")
            if result.stderr:
                debug_log(logger, "php", f"dpkg stderr: {result.stderr}")
        except Exception as e:
            logger.error(f"[DEBUG] Error checking package installation: {e}")
        
        raise Exception(f"PHP-FPM configuration file not found: {pool_config}. This likely means PHP {version} is not installed properly.")
    
    # Create backup of original configuration
    debug_log(logger, "php", f"Creating backup of {pool_config}")
    try:
        subprocess.run([
            "sudo", "cp", pool_config, f"{pool_config}.bak"
        ], check=True)
        debug_log(logger, "php", "Backup created successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"[DEBUG] Failed to create backup: {e}")
        raise
    
    # Update PHP-FPM pool configuration
    sed_commands = [
        f"s/^user = .*/user = www-data/",
        f"s/^group = .*/group = www-data/",
        f"s|^listen = .*|listen = /run/php/php{version}-fpm.sock|",
        f"s/^listen.owner = .*/listen.owner = www-data/",
        f"s/^listen.group = .*/listen.group = www-data/",
        f"s/^pm = .*/pm = dynamic/",
        f"s/^pm.max_children = .*/pm.max_children = {max_children}/",
        f"s/^pm.start_servers = .*/pm.start_servers = {start_servers}/",
        f"s/^pm.min_spare_servers = .*/pm.min_spare_servers = {min_spare_servers}/",
        f"s/^pm.max_spare_servers = .*/pm.max_spare_servers = {max_spare_servers}/",
        f"s|^;php_admin_value\\[error_log\\] = .*|php_admin_value[error_log] = /var/log/php{version}-fpm.log|",
        f"s/^;php_admin_flag\\[log_errors\\] = .*/php_admin_flag[log_errors] = on/",
        f"s/^;php_admin_value\\[memory_limit\\] = .*/php_admin_value[memory_limit] = 256M/",
        f"s/^;php_admin_value\\[max_execution_time\\] = .*/php_admin_value[max_execution_time] = 300/",
    ]
    
    for i, sed_cmd in enumerate(sed_commands):
        debug_log(logger, "php", f"Applying sed command {i+1}/{len(sed_commands)}: {sed_cmd}")
        try:
            result = subprocess.run([
                "sudo", "sed", "-i", sed_cmd, pool_config
            ], check=True, capture_output=True, text=True)
            debug_log(logger, "php", f"Sed command {i+1} applied successfully")
            debug_log(logger, "php", f"Sed command {i+1} stdout: {result.stdout}")
            if result.stderr:
                debug_log(logger, "php", f"Sed command {i+1} stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[DEBUG] Failed to apply sed command {i+1}: {sed_cmd}")
            logger.error(f"[DEBUG] Return code: {e.returncode}")
            logger.error(f"[DEBUG] Stdout: {e.stdout}")
            logger.error(f"[DEBUG] Stderr: {e.stderr}")
            logger.error(f"[DEBUG] Command: {' '.join(e.cmd) if hasattr(e, 'cmd') else 'N/A'}")
            raise
    
    # Create PHP-FPM log directory
    debug_log(logger, "php", "Creating PHP log directory")
    try:
        subprocess.run([
            "sudo", "mkdir", "-p", "/var/log/php"
        ], check=True)
        debug_log(logger, "php", "PHP log directory created successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"[DEBUG] Failed to create PHP log directory: {e}")
        raise
    
    debug_log(logger, "php", "Setting ownership of PHP log directory")
    try:
        subprocess.run([
            "sudo", "chown", "www-data:www-data", "/var/log/php"
        ], check=True)
        debug_log(logger, "php", "PHP log directory ownership set successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"[DEBUG] Failed to set PHP log directory ownership: {e}")
        raise
    
    # Restart PHP-FPM service
    debug_log(logger, "php", f"Attempting to restart PHP-FPM service: php{version}-fpm")
    
    # ENHANCED DEBUG: Check service status before restart
    try:
        from ..core.system import is_service_running
        is_running = is_service_running(f"php{version}-fpm")
        debug_log(logger, "php", f"Service status before restart: {'running' if is_running else 'not running'}")
    except Exception as e:
        debug_log(logger, "php", f"Could not check service status: {e}")
    
    try:
        debug_log(logger, "php", f"About to call restart_service for php{version}-fpm")
        restart_result = restart_service(f"php{version}-fpm")
        debug_log(logger, "php", f"restart_service returned: {restart_result}")
        
        # Additional verification after restart
        debug_log(logger, "php", "Verifying service status after restart...")
        try:
            is_running_after = is_service_running(f"php{version}-fpm")
            debug_log(logger, "php", f"Service status after restart: {'running' if is_running_after else 'not running'}")
        except Exception as e:
            debug_log(logger, "php", f"Could not verify service status after restart: {e}")
        
        if not restart_result:
            logger.error(f"[DEBUG] restart_service failed, raising PackageInstallationError")
            
            # ENHANCED DEBUG: Try to understand why restart failed
            debug_log(logger, "php", "Attempting to diagnose restart failure...")
            try:
                # Check if service exists
                result = subprocess.run([
                    "sudo", "systemctl", "list-unit-files", f"php{version}-fpm.service"
                ], capture_output=True, text=True)
                debug_log(logger, "php", f"systemctl list-unit-files result: {result.returncode}")
                debug_log(logger, "php", f"systemctl list-unit-files stdout: {result.stdout}")
                if result.stderr:
                    debug_log(logger, "php", f"systemctl list-unit-files stderr: {result.stderr}")
            except Exception as e:
                debug_log(logger, "php", f"Error checking service unit file: {e}")
            
            raise PackageInstallationError(f"php{version}-fpm", "Failed to restart PHP-FPM service")
        
        debug_log(logger, "php", "PHP-FPM service restarted successfully")
        debug_log(logger, "php", "About to return from _configure_php_fpm function normally")
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        debug_log(logger, "php", f"restart_service failed with exception: {e}")
        debug_log(logger, "php", f"Exception type: {type(e).__name__}")
        debug_log(logger, "php", f"Exception args: {e.args}")
        # Fallback for containers without systemd
        try:
            debug_log(logger, "php", "Trying fallback service restart command")
            result = subprocess.run([
                "sudo", "service", f"php{version}-fpm", "restart"
            ], check=True, capture_output=True, text=True)
            debug_log(logger, "php", "Fallback service restart successful")
            debug_log(logger, "php", f"Fallback stdout: {result.stdout}")
            if result.stderr:
                debug_log(logger, "php", f"Fallback stderr: {result.stderr}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            debug_log(logger, "php", f"Fallback service restart also failed: {e}")
            debug_log(logger, "php", f"Fallback exception type: {type(e).__name__}")
            debug_log(logger, "php", f"Fallback exception args: {e.args}")
            
            # ENHANCED DEBUG: Try to understand why fallback failed
            debug_log(logger, "php", "Attempting to diagnose fallback failure...")
            try:
                # Check if service command exists
                result = subprocess.run(["which", "service"], capture_output=True, text=True)
                debug_log(logger, "php", f"which service result: {result.returncode}")
                debug_log(logger, "php", f"which service stdout: {result.stdout}")
                if result.stderr:
                    debug_log(logger, "php", f"which service stderr: {result.stderr}")
            except Exception as e:
                debug_log(logger, "php", f"Error checking service command: {e}")
            
            # In containers, service might not be running, which is OK
            if verbose:
                logger.info(f"Could not restart PHP {version}-FPM service (normal in containers)")
    
    except Exception as e:
        # ENHANCED DEBUG: Catch any unhandled exceptions and provide comprehensive error reporting
        logger.error(f"[DEBUG] Unhandled exception in PHP-FPM configuration!")
        logger.error(f"[DEBUG] Exception type: {type(e).__name__}")
        logger.error(f"[DEBUG] Exception message: {str(e)}")
        logger.error(f"[DEBUG] Exception args: {e.args}")
        
        # Log the full traceback
        logger.error(f"[DEBUG] Full traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"[DEBUG] {line}")
        
        # Re-raise the exception with additional context
        raise Exception(f"PHP-FPM configuration failed unexpectedly: {str(e)}") from e
    
    # Final completion logging (this runs regardless of which path was taken)
    if verbose:
        logger.info(f"PHP {version}-FPM configuration completed")
    
    debug_log(logger, "php", "PHP-FPM configuration function completed successfully")


def _install_extensions_interactive(version: str, verbose: bool = False) -> None:
    """
    Interactive extension installation for PHP.
    
    Args:
        version (str): PHP version
        verbose (bool): Enable verbose output
    """
    import subprocess
    
    if verbose:
        logger.info(f"Installing PHP {version} extensions...")
    
    # Define available extensions with descriptions
    available_extensions = {
        "mysql": {
            "package": f"php{version}-mysql",
            "description": "MySQL/MariaDB database support"
        },
        "pgsql": {
            "package": f"php{version}-pgsql",
            "description": "PostgreSQL database support"
        },
        "sqlite": {
            "package": f"php{version}-sqlite3",
            "description": "SQLite database support"
        },
        "xml": {
            "package": f"php{version}-xml",
            "description": "XML processing support"
        },
        "mbstring": {
            "package": f"php{version}-mbstring",
            "description": "Multi-byte string handling"
        },
        "curl": {
            "package": f"php{version}-curl",
            "description": "HTTP client and URL handling"
        },
        "zip": {
            "package": f"php{version}-zip",
            "description": "ZIP file handling"
        },
        "gd": {
            "package": f"php{version}-gd",
            "description": "Image processing (GD library)"
        },
        "imagick": {
            "package": f"php-imagick",
            "description": "Advanced image processing (ImageMagick)"
        },
        "intl": {
            "package": f"php{version}-intl",
            "description": "Internationalization functions"
        },
        "bcmath": {
            "package": f"php{version}-bcmath",
            "description": "Precision mathematics"
        },
        # JSON is built-in from PHP 8.0+, no need to install separately
        # "json": {
        #     "package": f"php{version}-json",
        #     "description": "JSON support"
        # },
        "soap": {
            "package": f"php{version}-soap",
            "description": "SOAP web services"
        },
        "redis": {
            "package": f"php-redis",
            "description": "Redis client"
        },
        "memcached": {
            "package": f"php-memcached",
            "description": "Memcached client"
        },
        "opcache": {
            "package": f"php{version}-opcache",
            "description": "Opcode cache for performance"
        },
        "xdebug": {
            "package": f"php-xdebug",
            "description": "Debugging and profiling tool"
        },
        "composer": {
            "package": "composer",
            "description": "PHP dependency manager"
        }
    }
    
    # Check which extensions are already installed
    installed_extensions = []
    for ext_name, ext_info in available_extensions.items():
        result = subprocess.run([
            "dpkg", "-l", ext_info["package"]
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            installed_extensions.append(ext_name)
    
    # Create selection list (excluding already installed)
    selection_options = []
    for ext_name, ext_info in available_extensions.items():
        if ext_name not in installed_extensions:
            selection_options.append(
                f"{ext_name} - {ext_info['description']}"
                )
    
    # Add common preset option (always add it, even if some extensions are already installed)
    selection_options.insert(0, "common - Install common web extensions (mysql, xml, mbstring, curl, zip, gd, intl, bcmath, json)")
    
    # Check if all extensions except "common" are already installed
    if len(selection_options) <= 1:  # Only "common" option exists
        from ..cli.menu import console
        console.print("[green]All common extensions are already installed![/green]")
        return
    
    # Let user select extensions
    from ..cli.menu import console
    console.print("[bold]Available PHP Extensions:[/bold]")
    
    # Display the numbered list of extensions
    for i, option in enumerate(selection_options, 1):
        console.print(f"  {i}. {option}")
    
    console.print("\nSelect extensions to install (space-separated numbers):")
    
    from ..cli.menu import get_user_input
    
    # Retry loop for valid input
    max_retries = 3
    retry_count = 0
    extensions_to_install = []
    
    while retry_count < max_retries and not extensions_to_install:
        selected_indices = get_user_input(
            f"Enter extension numbers (e.g., 1 3 5) or 'common' for preset (attempt {retry_count + 1}/{max_retries})",
            default="common"
        )
        
        # Debug logging
        if verbose:
            logger.debug(f"User input: {selected_indices}")
            logger.debug(f"Available options: {selection_options}")
        
        # Additional debug logging to diagnose the issue
        logger.debug(f"[DEBUG] User input received: '{selected_indices}'")
        logger.debug(f"[DEBUG] First option in selection_options: '{selection_options[0] if selection_options else 'None'}'")
        
        # Determine which extensions to install
        extensions_to_install = []
        
        if selected_indices.lower() == "common":
            # Install common web extensions (JSON is built-in from PHP 8.0+)
            common_extensions = ["mysql", "xml", "mbstring", "curl", "zip", "gd", "intl", "bcmath"]
            extensions_to_install = [ext for ext in common_extensions if ext not in installed_extensions]
            
            if not extensions_to_install:
                console.print("[yellow]All common extensions are already installed![/yellow]")
                return  # Exit the function early with no error
            
            console.print(f"[green]Selected common extensions: {', '.join(extensions_to_install)}[/green]")
            break  # Valid input, exit the loop
        else:
            # Parse user selection
            try:
                indices = [int(i.strip()) for i in selected_indices.split()]
                debug_log(logger, "php", f"Parsed indices: {indices}")
                valid_indices = []
                
                # Check if user selected the first option (common preset)
                if 1 in indices and len(selection_options) > 0:
                    first_option = selection_options[0]
                    if first_option.startswith("common -"):
                        debug_log(logger, "php", "User selected common preset via index 1")
                        # Install common web extensions (JSON is built-in from PHP 8.0+)
                        common_extensions = ["mysql", "xml", "mbstring", "curl", "zip", "gd", "intl", "bcmath"]
                        extensions_to_install = [ext for ext in common_extensions if ext not in installed_extensions]
                        
                        if not extensions_to_install:
                            console.print("[yellow]All common extensions are already installed![/yellow]")
                            return  # Exit the function early with no error
                        
                        console.print(f"[green]Selected common extensions: {', '.join(extensions_to_install)}[/green]")
                        valid_indices = ["1"]
                    else:
                        # Process normally if first option is not the common preset
                        for idx in indices:
                            debug_log(logger, "php", f"Processing index: {idx}")
                            if 1 <= idx <= len(selection_options):
                                ext_line = selection_options[idx - 1]
                                debug_log(logger, "php", f"Extension line: '{ext_line}'")
                                ext_name = ext_line.split(" - ")[0]
                                debug_log(logger, "php", f"Extracted extension name: '{ext_name}'")
                                if ext_name not in installed_extensions:
                                    extensions_to_install.append(ext_name)
                                    valid_indices.append(str(idx))
                                    debug_log(logger, "php", f"Added extension to install: '{ext_name}'")
                                else:
                                    debug_log(logger, "php", f"Extension '{ext_name}' already installed, skipping")
                            else:
                                console.print(f"[red]Invalid number: {idx}. Please enter numbers between 1 and {len(selection_options)}.[/red]")
                else:
                    # Process normally if first option is not selected
                    for idx in indices:
                        debug_log(logger, "php", f"Processing index: {idx}")
                        if 1 <= idx <= len(selection_options):
                            ext_line = selection_options[idx - 1]
                            debug_log(logger, "php", f"Extension line: '{ext_line}'")
                            ext_name = ext_line.split(" - ")[0]
                            debug_log(logger, "php", f"Extracted extension name: '{ext_name}'")
                            if ext_name not in installed_extensions:
                                extensions_to_install.append(ext_name)
                                valid_indices.append(str(idx))
                                debug_log(logger, "php", f"Added extension to install: '{ext_name}'")
                            else:
                                debug_log(logger, "php", f"Extension '{ext_name}' already installed, skipping")
                        else:
                            console.print(f"[red]Invalid number: {idx}. Please enter numbers between 1 and {len(selection_options)}.[/red]")
                
                if extensions_to_install:
                    console.print(f"[green]Selected extensions: {', '.join(valid_indices)}[/green]")
                    break  # Valid input, exit the loop
                elif not indices:
                    console.print("[red]No valid numbers provided. Please try again.[/red]")
                else:
                    console.print("[yellow]All selected extensions are already installed. Please select different extensions.[/yellow]")
                    
            except ValueError:
                console.print("[red]Invalid input. Please enter valid numbers separated by spaces.[/red]")
        
        retry_count += 1
        if retry_count < max_retries:
            console.print(f"[yellow]Please try again. You have {max_retries - retry_count} attempts left.[/yellow]")
    
    # If max retries reached and no valid selection
    if retry_count >= max_retries and not extensions_to_install:
        console.print("[red]Maximum retry attempts reached. No extensions will be installed.[/red]")
        return
    
    if not extensions_to_install:
        from ..cli.menu import console
        console.print("[yellow]No new extensions to install.[/yellow]")
        return
    
    # Install selected extensions
    from ..cli.menu import console
    console.print(f"[bold]Installing {len(extensions_to_install)} extensions:[/bold]")
    for ext_name in extensions_to_install:
        console.print(f"  • {ext_name} - {available_extensions[ext_name]['description']}")
    
    # Install packages
    debug_log(logger, "php", f"Extensions to install: {extensions_to_install}")
    packages_to_install = [available_extensions[ext]["package"] for ext in extensions_to_install]
    debug_log(logger, "php", f"Packages to install: {packages_to_install}")
    
    # Update package lists (includes dpkg interruption fix)
    from ..utils.package import update_package_lists
    if not update_package_lists(verbose):
        console.print("[red]Failed to update package lists[/red]")
        return
    
    # Install packages
    for package in packages_to_install:
        try:
            if verbose:
                debug_log(logger, "php", f"Installing {package}...")
            
            try:
                subprocess.run([
                    "sudo", "apt", "install", "-y", package
                ], check=True)
            except subprocess.CalledProcessError as e:
                # Check if it's a dpkg interruption error
                if "dpkg was interrupted" in e.stderr:
                    # Try to fix dpkg and retry
                    if verbose:
                        debug_log(logger, "php", f"Detected dpkg interruption while installing {package}, attempting to fix...")
                    
                    if not fix_dpkg_interruption(verbose):
                        raise Exception(f"Failed to fix dpkg interruption: {e.stderr}")
                    
                    # Retry the installation
                    if verbose:
                        debug_log(logger, "php", f"Retrying {package} installation...")
                    
                    subprocess.run([
                        "sudo", "apt", "install", "-y", package
                    ], check=True)
                else:
                    # Re-raise the original error
                    raise
            
            console.print(f"[green]✓ {package} installed[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to install {package}: {e}[/red]")
            logger.warning(f"Failed to install extension {package}: {e}")
    
    # Configure OPcache if installed
    if "opcache" in extensions_to_install:
        _configure_opcache(version, verbose)
    
    # Restart PHP-FPM to apply changes
    try:
        if not restart_service(f"php{version}-fpm"):
            raise PackageInstallationError(f"php{version}-fpm", "Failed to restart PHP-FPM service")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback for containers without systemd
        try:
            subprocess.run([
                "sudo", "service", f"php{version}-fpm", "restart"
            ], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # In containers, the service might not be running, which is OK
            if verbose:
                logger.info(f"Could not restart PHP {version}-FPM service (normal in containers)")


def _configure_opcache(version: str, verbose: bool = False) -> None:
    """
    Configure OPcache for optimal performance.
    
    Args:
        version (str): PHP version
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        debug_log(logger, "php", f"Configuring OPcache for PHP {version}...")
    
    # OPcache configuration
    opcache_config = f"""; OPcache configuration for PHP {version}
; Generated by KurServer CLI

opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=128
opcache.interned_strings_buffer=8
opcache.max_accelerated_files=4000
opcache.revalidate_freq=2
opcache.fast_shutdown=1
opcache.save_comments=1
opcache.load_comments=1
opcache.validate_timestamps=1
opcache.file_cache=/var/tmp/opcache
opcache.file_cache_only=0
opcache.file_cache_consistency_checks=1
opcache.huge_code_pages=0
opcache.optimization_level=0x7FFFBFFF
opcache.inheritance_hack=1
opcache.dups_fix=1
opcache.blacklist_filename=/etc/php/{version}/mods-available/opcache-blacklist.txt
opcache.max_file_size=0
opcache.consistency_checks=0
opcache.force_restart_timeout=180
opcache.error_log=/var/log/php{version}-fpm-opcache.log
opcache.log_verbosity_level=1
opcache.preferred_memory_model=opcache.preferred_memory_model=
opcache.protect_memory=0
opcache.restrict_api=
opcache.mmap_base=opcache.mmap_base=
opcache.file_update_protection=2
opcache.opt_debug_level=0
opcache.validate_permission=0
opcache.validate_root=0
"""
    
    # Create OPcache configuration file
    opcache_file = f"/etc/php/{version}/mods-available/opcache.ini"
    
    try:
        # Write configuration
        with open(opcache_file, 'w') as f:
            f.write(opcache_config)
        
        # Set appropriate permissions
        os.chmod(opcache_file, 0o644)
        
        # Create OPcache blacklist file
        blacklist_file = f"/etc/php/{version}/mods-available/opcache-blacklist.txt"
        with open(blacklist_file, 'w') as f:
            f.write("# OPcache blacklist file\n")
            f.write("# Add files that should not be cached\n")
        
        os.chmod(blacklist_file, 0o644)
        
        if verbose:
            debug_log(logger, "php", f"OPcache configuration for PHP {version} completed")
            
    except Exception as e:
        logger.warning(f"Failed to configure OPcache: {e}")