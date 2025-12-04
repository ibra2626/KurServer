"""
MySQL/MariaDB installer module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import is_package_installed, restart_service
from ..core.exceptions import PackageInstallationError

logger = get_logger()


def install_mysql_menu(verbose: bool = False) -> None:
    """
    Handle MySQL/MariaDB installation from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]MySQL/MariaDB Installation[/bold blue]")
    console.print("This will install and configure MySQL/MariaDB database server on your Ubuntu system.")
    console.print()
    
    # Ask which database to install
    db_choice = get_user_input(
        "Which database would you like to install?",
        choices=["mysql", "mariadb"],
        default="mysql"
    )
    
    # Check if already installed
    from ..core.system import is_package_installed
    if is_package_installed(db_choice):
        if not confirm_action(f"{db_choice.title()} is already installed. Do you want to reinstall?"):
            return
    
    # Get installation preferences
    console.print(f"[bold]{db_choice.title()} Installation Options:[/bold]")
    
    # Ask for confirmation
    if not confirm_action(f"Do you want to proceed with {db_choice} installation?"):
        console.print("[yellow]Installation cancelled.[/yellow]")
        return
    
    try:
        # Perform installation with progress
        show_progress(
            f"Installing {db_choice}...",
            _install_database,
            db_choice,
            verbose
        )
        
        console.print(f"[bold green]✓ {db_choice.title()} installation completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"{db_choice} installation failed: {e}")


def _install_database(db_type: str, verbose: bool = False) -> None:
    """
    Actually install MySQL or MariaDB.
    
    Args:
        db_type (str): Database type ('mysql' or 'mariadb')
        verbose (bool): Enable verbose output
    """
    import subprocess
    from ..utils.package import update_package_lists
    
    # Update package lists (includes dpkg interruption fix)
    if not update_package_lists(verbose):
        raise Exception("Failed to update package lists")
    
    # Install database server
    if verbose:
        logger.info(f"Installing {db_type} package...")
    
    # Set non-interactive installation for MySQL
    env = {'DEBIAN_FRONTEND': 'noninteractive'}
    
    if db_type == 'mysql':
        # Pre-configure MySQL root password
        subprocess.run([
            "sudo", "debconf-set-selections"
        ], input=f"mysql-server mysql-server/root_password password root\n", 
           text=True, env=env)
        subprocess.run([
            "sudo", "debconf-set-selections"
        ], input=f"mysql-server mysql-server/root_password_again password root\n", 
           text=True, env=env)
        
        result = subprocess.run(
            ["sudo", "apt", "install", "-y", "mysql-server"],
            capture_output=True,
            text=True,
            env=env
        )
    else:  # mariadb
        result = subprocess.run(
            ["sudo", "apt", "install", "-y", "mariadb-server"],
            capture_output=True,
            text=True
        )
    
    if result.returncode != 0:
        raise Exception(f"Failed to install {db_type}: {result.stderr}")
    
    # Enable and start service
    if verbose:
        logger.info(f"Enabling and starting {db_type} service...")
    
    # Enable service
    subprocess.run(["sudo", "systemctl", "enable", db_type], check=True)
    
    # Start service
    subprocess.run(["sudo", "systemctl", "start", db_type], check=True)
    
    # Run secure installation
    if verbose:
        logger.info("Running secure installation...")
    
    _secure_database_installation(db_type, verbose)
    
    # Performance tuning
    if verbose:
        logger.info("Applying performance tuning...")
    
    _apply_performance_tuning(db_type, verbose)
    
    logger.info(f"{db_type} installation completed successfully")


def _secure_database_installation(db_type: str, verbose: bool = False) -> None:
    """
    Perform security hardening for MySQL/MariaDB installation.
    
    Args:
        db_type (str): Database type ('mysql' or 'mariadb')
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Securing {db_type} installation...")
    
    # Set root password if MySQL (MariaDB typically has no root password by default)
    if db_type == 'mysql':
        # For MySQL, we already set the password during installation
        root_password = "root"
        
        # Remove anonymous users
        subprocess.run([
            "sudo", "mysql", "-uroot", f"-p{root_password}", "-e",
            "DELETE FROM mysql.user WHERE User='';"
        ], check=True)
        
        # Disallow remote root login
        subprocess.run([
            "sudo", "mysql", "-uroot", f"-p{root_password}", "-e",
            "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
        ], check=True)
        
        # Remove test database
        subprocess.run([
            "sudo", "mysql", "-uroot", f"-p{root_password}", "-e",
            "DROP DATABASE IF EXISTS test;"
        ], check=True)
        
        subprocess.run([
            "sudo", "mysql", "-uroot", f"-p{root_password}", "-e",
            "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
        ], check=True)
        
        # Reload privileges
        subprocess.run([
            "sudo", "mysql", "-uroot", f"-p{root_password}", "-e",
            "FLUSH PRIVILEGES;"
        ], check=True)
    
    else:  # MariaDB
        # For MariaDB, run mysql_secure_installation script with automated answers
        # Create expect script for automated secure installation
        expect_script = f"""
#!/usr/bin/expect -f
set timeout 10
spawn sudo mysql_secure_installation

expect "Enter current password for root (enter for none):"
send "\\r"

expect "Switch to unix_socket authentication \\[Y/n\\]"
send "n\\r"

expect "Change the root password? \\[Y/n\\]"
send "n\\r"

expect "Remove anonymous users? \\[Y/n\\]"
send "Y\\r"

expect "Disallow root login remotely? \\[Y/n\\]"
send "Y\\r"

expect "Remove test database and access to it? \\[Y/n\\]"
send "Y\\r"

expect "Reload privilege tables now? \\[Y/n\\]"
send "Y\\r"

expect eof
"""
        
        # Write expect script to temporary file
        with open('/tmp/secure_mariadb.exp', 'w') as f:
            f.write(expect_script)
        
        # Make it executable and run it
        os.chmod('/tmp/secure_mariadb.exp', 0o755)
        subprocess.run(["expect", "/tmp/secure_mariadb.exp"], check=True)
        
        # Clean up
        os.remove('/tmp/secure_mariadb.exp')
    
    if verbose:
        logger.info(f"{db_type} security hardening completed")


def _apply_performance_tuning(db_type: str, verbose: bool = False) -> None:
    """
    Apply performance tuning configuration for MySQL/MariaDB.
    
    Args:
        db_type (str): Database type ('mysql' or 'mariadb')
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Applying performance tuning for {db_type}...")
    
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
        innodb_buffer_pool = "128M"
        innodb_log_file_size = "32M"
        max_connections = "50"
    elif total_memory_mb < 2048:  # 1-2GB
        innodb_buffer_pool = "256M"
        innodb_log_file_size = "64M"
        max_connections = "100"
    elif total_memory_mb < 4096:  # 2-4GB
        innodb_buffer_pool = "512M"
        innodb_log_file_size = "128M"
        max_connections = "150"
    else:  # 4GB+
        innodb_buffer_pool = "1G"
        innodb_log_file_size = "256M"
        max_connections = "200"
    
    # Create performance tuning configuration
    config_content = f"""# Performance tuning configuration for {db_type}
# Generated by KurServer CLI

[mysqld]
# Connection settings
max_connections = {max_connections}
connect_timeout = 10
wait_timeout = 600
max_allowed_packet = 64M

# General query log (disable in production for performance)
general_log = 0
general_log_file = /var/log/mysql/mysql.log

# Error log
log_error = /var/log/mysql/error.log

# Slow query log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 2

# InnoDB settings (only apply to MySQL/MariaDB with InnoDB)
innodb_buffer_pool_size = {innodb_buffer_pool}
innodb_log_file_size = {innodb_log_file_size}
innodb_flush_method = O_DIRECT
innodb_flush_log_at_trx_commit = 2
innodb_lock_wait_timeout = 50

# MyISAM settings
key_buffer_size = 32M
myisam_sort_buffer_size = 8M

# Query cache (disable in production for performance)
query_cache_type = 0
query_cache_size = 0

# Table settings
table_open_cache = 1024
open_files_limit = 65535

# Binary log
log_bin = /var/log/mysql/mysql-bin.log
expire_logs_days = 10
max_binlog_size = 100M

# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
"""
    
    # Write configuration to override file
    config_file = f"/etc/mysql/conf.d/kurserver-performance.cnf"
    
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Write configuration
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Set appropriate permissions
        os.chmod(config_file, 0o644)
        
        # Restart database service to apply changes
        if not restart_service(db_type):
            raise PackageInstallationError(db_type, f"Failed to restart {db_type} service")
        
        if verbose:
            logger.info(f"Performance tuning applied and {db_type} restarted")
            
    except Exception as e:
        logger.warning(f"Failed to apply performance tuning: {e}")