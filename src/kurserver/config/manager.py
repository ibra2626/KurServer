"""
Configuration manager module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import reload_nginx, is_container_environment

logger = get_logger()


def config_management_menu(verbose: bool = False) -> None:
    """
    Handle configuration management from menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]Configuration Management[/bold blue]")
    console.print()
    
    # Create submenu options
    options = [
        MenuOption("1", "View configuration", action=view_config),
        MenuOption("2", "Edit configuration", action=edit_config),
        MenuOption("3", "Backup configuration", action=backup_config),
        MenuOption("4", "Restore configuration", action=restore_config),
        MenuOption("5", "Validate configuration", action=validate_config),
        MenuOption("6", "Reset configuration", action=reset_config),
    ]
    
    submenu = Menu("Configuration Management", options, show_status=False)
    submenu.display(verbose=verbose)


def view_config(verbose: bool = False) -> None:
    """
    View configuration files.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]View Configuration[/bold blue]")
    console.print()
    
    # Display configuration types with numbers
    console.print("[bold]Available Configuration Types:[/bold]")
    config_types = [
        "nginx", "php", "mysql", "mariadb",
        "php-fpm", "ssl", "system", "kurserver"
    ]
    for i, config_type in enumerate(config_types, 1):
        console.print(f"  [{i}] {config_type.title()}")
    
    # Get configuration type selection by number
    while True:
        try:
            choice = get_user_input(f"Select configuration to view (1-{len(config_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(config_types):
                config_type = config_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(config_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    try:
        if config_type == "nginx":
            _view_nginx_config()
        elif config_type == "php":
            _view_php_config()
        elif config_type == "mysql":
            _view_mysql_config()
        elif config_type == "mariadb":
            _view_mariadb_config()
        elif config_type == "php-fpm":
            _view_php_fpm_config()
        elif config_type == "ssl":
            _view_ssl_config()
        elif config_type == "system":
            _view_system_config()
        elif config_type == "kurserver":
            _view_kurserver_config()
            
    except Exception as e:
        console.print(f"[bold red]✗ Failed to view configuration:[/bold red] {e}")
        logger.error(f"Failed to view {config_type} configuration: {e}")


def edit_config(verbose: bool = False) -> None:
    """
    Edit configuration files.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Edit Configuration[/bold blue]")
    console.print()
    
    # Display configuration types with numbers
    console.print("[bold]Available Configuration Types:[/bold]")
    config_types = [
        "nginx", "php", "mysql", "mariadb",
        "php-fpm", "ssl", "system", "kurserver"
    ]
    for i, config_type in enumerate(config_types, 1):
        console.print(f"  [{i}] {config_type.title()}")
    
    # Get configuration type selection by number
    while True:
        try:
            choice = get_user_input(f"Select configuration to edit (1-{len(config_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(config_types):
                config_type = config_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(config_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    try:
        if config_type == "nginx":
            _edit_nginx_config()
        elif config_type == "php":
            _edit_php_config()
        elif config_type == "mysql":
            _edit_mysql_config()
        elif config_type == "mariadb":
            _edit_mariadb_config()
        elif config_type == "php-fpm":
            _edit_php_fpm_config()
        elif config_type == "ssl":
            _edit_ssl_config()
        elif config_type == "system":
            _edit_system_config()
        elif config_type == "kurserver":
            _edit_kurserver_config()
            
    except Exception as e:
        console.print(f"[bold red]✗ Failed to edit configuration:[/bold red] {e}")
        logger.error(f"Failed to edit {config_type} configuration: {e}")


def backup_config(verbose: bool = False) -> None:
    """
    Backup configuration files.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Backup Configuration[/bold blue]")
    console.print()
    
    # Display backup types with numbers
    console.print("[bold]Available Backup Types:[/bold]")
    backup_types = ["full", "selective"]
    for i, backup_type in enumerate(backup_types, 1):
        console.print(f"  [{i}] {backup_type.title()}")
    
    # Get backup type selection by number
    while True:
        try:
            choice = get_user_input(f"Select backup type (1-{len(backup_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(backup_types):
                backup_type = backup_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(backup_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    if backup_type == "selective":
        # Get configurations to backup
        configs = get_user_input(
            "Enter configurations to backup (space-separated)",
            choices=["nginx", "php", "mysql", "mariadb", "php-fpm", "ssl", "system", "kurserver"],
            default="nginx php mysql"
        ).split()
    else:
        configs = ["nginx", "php", "mysql", "mariadb", "php-fpm", "ssl", "system", "kurserver"]
    
    # Get backup name
    backup_name = get_user_input(
        "Enter backup name (optional)",
        default=""
    )
    
    if not backup_name:
        from datetime import datetime
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not confirm_action(f"Create backup '{backup_name}' with {len(configs)} configurations?"):
        console.print("[yellow]Backup cancelled.[/yellow]")
        return
    
    try:
        show_progress(
            "Creating configuration backup...",
            _create_backup,
            configs, backup_name, verbose
        )
        
        console.print(f"[bold green]✓ Backup '{backup_name}' created successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Backup failed:[/bold red] {e}")
        logger.error(f"Configuration backup failed: {e}")


def restore_config(verbose: bool = False) -> None:
    """
    Restore configuration from backup.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Restore Configuration[/bold blue]")
    console.print()
    
    # Get available backups
    backups = _get_available_backups()
    
    if not backups:
        console.print("[yellow]No configuration backups found.[/yellow]")
        return
    
    # Display backups with numbers
    console.print("[bold]Available Backups:[/bold]")
    for i, backup in enumerate(backups, 1):
        console.print(f"  [{i}] {backup}")
    
    # Get backup selection by number
    while True:
        try:
            choice = get_user_input(f"Select backup to restore (1-{len(backups)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(backups):
                backup_name = backups[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(backups)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Display restore types with numbers
    console.print("[bold]Available Restore Types:[/bold]")
    restore_types = ["full", "selective"]
    for i, restore_type in enumerate(restore_types, 1):
        console.print(f"  [{i}] {restore_type.title()}")
    
    # Get restore type selection by number
    while True:
        try:
            choice = get_user_input(f"Select restore type (1-{len(restore_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(restore_types):
                restore_type = restore_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(restore_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    if restore_type == "selective":
        # Get configurations to restore
        configs = get_user_input(
            "Enter configurations to restore (space-separated)",
            choices=["nginx", "php", "mysql", "mariadb", "php-fpm", "ssl", "system", "kurserver"],
            default="nginx php mysql"
        ).split()
    else:
        configs = None  # Restore all
    
    if not confirm_action(f"Restore backup '{backup_name}'? This will overwrite current configurations."):
        console.print("[yellow]Restore cancelled.[/yellow]")
        return
    
    try:
        show_progress(
            "Restoring configuration backup...",
            _restore_backup,
            backup_name, configs, verbose
        )
        
        console.print(f"[bold green]✓ Backup '{backup_name}' restored successfully![/bold green]")
        
        # Restart services if needed
        if confirm_action("Restart affected services to apply changes?"):
            _restart_services_after_restore(configs, verbose)
            console.print("[green]✓ Services restarted![/green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Restore failed:[/bold red] {e}")
        logger.error(f"Configuration restore failed: {e}")


def validate_config(verbose: bool = False) -> None:
    """
    Validate configuration files.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Validate Configuration[/bold blue]")
    console.print()
    
    # Get configurations to validate
    configs = get_user_input(
        "Enter configurations to validate (space-separated, or 'all')",
        choices=["all", "nginx", "php", "mysql", "mariadb", "php-fpm", "ssl"],
        default="all"
    ).split()
    
    if "all" in configs:
        configs = ["nginx", "php", "mysql", "mariadb", "php-fpm", "ssl"]
    
    validation_results = {}
    
    for config in configs:
        try:
            if verbose:
                logger.info(f"Validating {config} configuration...")
            
            result = _validate_single_config(config, verbose)
            validation_results[config] = result
            
        except Exception as e:
            validation_results[config] = {"valid": False, "error": str(e)}
    
    # Display results
    console.print("\n[bold]Validation Results:[/bold]")
    
    for config, result in validation_results.items():
        if result["valid"]:
            console.print(f"  {config}: [green]✓ Valid[/green]")
        else:
            console.print(f"  {config}: [red]✗ Invalid[/red]")
            if "error" in result:
                console.print(f"    Error: {result['error']}")
            if "suggestion" in result:
                console.print(f"    Suggestion: {result['suggestion']}")


def reset_config(verbose: bool = False) -> None:
    """
    Reset configuration to defaults.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Reset Configuration[/bold blue]")
    console.print()
    
    # Display configuration types with numbers
    console.print("[bold]Available Configuration Types:[/bold]")
    config_types = [
        "nginx", "php", "mysql", "mariadb",
        "php-fpm", "ssl", "system", "kurserver"
    ]
    for i, config_type in enumerate(config_types, 1):
        console.print(f"  [{i}] {config_type.title()}")
    
    # Get configuration type selection by number
    while True:
        try:
            choice = get_user_input(f"Select configuration to reset (1-{len(config_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(config_types):
                config_type = config_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(config_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Confirm reset
    if not confirm_action(f"Are you sure you want to reset {config_type} configuration to defaults?"):
        console.print("[yellow]Reset cancelled.[/yellow]")
        return
    
    try:
        show_progress(
            f"Resetting {config_type} configuration...",
            _reset_single_config,
            config_type, verbose
        )
        
        console.print(f"[bold green]✓ {config_type} configuration reset successfully![/bold green]")
        
        # Restart service if needed
        if confirm_action(f"Restart {config_type} service to apply changes?"):
            _restart_service(config_type, verbose)
            console.print(f"[green]✓ {config_type} service restarted![/green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Reset failed:[/bold red] {e}")
        logger.error(f"Configuration reset failed for {config_type}: {e}")


def _view_nginx_config() -> None:
    """View Nginx configuration."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get available sites
    sites = []
    if os.path.exists("/etc/nginx/sites-available"):
        sites = os.listdir("/etc/nginx/sites-available")
    
    if not sites:
        console.print("[yellow]No Nginx sites found.[/yellow]")
        return
    
    # Display sites with numbers
    console.print("[bold]Available Nginx Sites:[/bold]")
    for i, site in enumerate(sites, 1):
        console.print(f"  [{i}] {site}")
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Select site to view (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    config_file = f"/etc/nginx/sites-available/{site}"
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        console.print(f"\n[bold]Nginx Configuration for {site}:[/bold]")
        console.print(content)
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _view_php_config() -> None:
    """View PHP configuration."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get PHP versions
    php_versions = []
    if os.path.exists("/etc/php"):
        php_versions = [d for d in os.listdir("/etc/php") if d.startswith("7.") or d.startswith("8.")]
    
    if not php_versions:
        console.print("[yellow]No PHP installations found.[/yellow]")
        return
    
    # Display PHP versions with numbers
    console.print("[bold]Available PHP Versions:[/bold]")
    for i, version in enumerate(php_versions, 1):
        console.print(f"  [{i}] PHP {version}")
    
    # Get PHP version selection by number
    while True:
        try:
            choice = get_user_input(f"Select PHP version (1-{len(php_versions)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(php_versions):
                version = php_versions[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(php_versions)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    config_file = f"/etc/php/{version}/apache2/php.ini"
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        console.print(f"\n[bold]PHP {version} Configuration:[/bold]")
        console.print(content)
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _view_mysql_config() -> None:
    """View MySQL configuration."""
    from ..cli.menu import console
    
    try:
        with open("/etc/mysql/my.cnf", 'r') as f:
            content = f.read()
        
        console.print("\n[bold]MySQL Configuration:[/bold]")
        console.print(content)
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _view_mariadb_config() -> None:
    """View MariaDB configuration."""
    from ..cli.menu import console
    
    try:
        with open("/etc/mysql/my.cnf", 'r') as f:
            content = f.read()
        
        console.print("\n[bold]MariaDB Configuration:[/bold]")
        console.print(content)
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _view_php_fpm_config() -> None:
    """View PHP-FPM configuration."""
    from ..cli.menu import console
    import os
    
    # Get PHP versions
    php_versions = []
    if os.path.exists("/etc/php"):
        php_versions = [d for d in os.listdir("/etc/php") if d.startswith("7.") or d.startswith("8.")]
    
    if not php_versions:
        console.print("[yellow]No PHP-FPM installations found.[/yellow]")
        return
    
    # Display PHP versions with numbers
    console.print("[bold]Available PHP-FPM Versions:[/bold]")
    for i, version in enumerate(php_versions, 1):
        console.print(f"  [{i}] PHP-FPM {version}")
    
    # Get PHP version selection by number
    while True:
        try:
            choice = get_user_input(f"Select PHP-FPM version (1-{len(php_versions)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(php_versions):
                version = php_versions[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(php_versions)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    config_file = f"/etc/php/{version}/fpm/pool.d/www.conf"
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        console.print(f"\n[bold]PHP-FPM {version} Configuration:[/bold]")
        console.print(content)
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _view_ssl_config() -> None:
    """View SSL certificate information."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get available certificates
    certs = []
    
    # Let's Encrypt certificates
    if os.path.exists("/etc/letsencrypt/live"):
        certs.extend(os.listdir("/etc/letsencrypt/live"))
    
    # Self-signed certificates
    if os.path.exists("/etc/ssl/certs"):
        certs.extend([c for c in os.listdir("/etc/ssl/certs") if c.endswith(".crt")])
    
    if not certs:
        console.print("[yellow]No SSL certificates found.[/yellow]")
        return
    
    # Display certificates with numbers
    console.print("[bold]Available SSL Certificates:[/bold]")
    for i, cert in enumerate(certs, 1):
        console.print(f"  [{i}] {cert}")
    
    # Get certificate selection by number
    while True:
        try:
            choice = get_user_input(f"Select certificate to view (1-{len(certs)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(certs):
                cert_name = certs[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(certs)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    try:
        if cert_name in os.listdir("/etc/letsencrypt/live"):
            cert_path = f"/etc/letsencrypt/live/{cert_name}/fullchain.pem"
        else:
            cert_path = f"/etc/ssl/certs/{cert_name}"
        
        # Get certificate information
        result = subprocess.run([
            "openssl", "x509", "-in", cert_path, "-noout", "-text"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print(f"\n[bold]SSL Certificate Information for {cert_name}:[/bold]")
            console.print(result.stdout)
        else:
            console.print(f"[red]Failed to read certificate:[/red] {result.stderr}")
            
    except Exception as e:
        console.print(f"[red]Failed to read certificate:[/red] {e}")


def _view_system_config() -> None:
    """View system configuration."""
    from ..cli.menu import console
    import subprocess
    
    try:
        # Get system information
        result = subprocess.run([
            "uname", "-a"
        ], capture_output=True, text=True)
        
        console.print("\n[bold]System Information:[/bold]")
        console.print(result.stdout.strip())
        
        # Get memory information
        with open("/proc/meminfo", 'r') as f:
            mem_info = f.read()
        
        console.print("\n[bold]Memory Information:[/bold]")
        for line in mem_info.split('\n')[:5]:  # Show first 5 lines
            console.print(line)
        
        # Get disk information
        result = subprocess.run([
            "df", "-h"
        ], capture_output=True, text=True)
        
        console.print("\n[bold]Disk Usage:[/bold]")
        console.print(result.stdout)
        
    except Exception as e:
        console.print(f"[red]Failed to get system information:[/red] {e}")


def _view_kurserver_config() -> None:
    """View KurServer configuration."""
    from ..cli.menu import console
    import os
    import json
    
    config_file = os.path.expanduser("~/.kurserver/config.json")
    
    if not os.path.exists(config_file):
        console.print("[yellow]KurServer configuration not found.[/yellow]")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        console.print("\n[bold]KurServer Configuration:[/bold]")
        console.print(json.dumps(config, indent=2))
        
    except Exception as e:
        console.print(f"[red]Failed to read configuration:[/red] {e}")


def _edit_nginx_config() -> None:
    """Edit Nginx configuration."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get available sites
    sites = []
    if os.path.exists("/etc/nginx/sites-available"):
        sites = os.listdir("/etc/nginx/sites-available")
    
    if not sites:
        console.print("[yellow]No Nginx sites found.[/yellow]")
        return
    
    # Display sites with numbers
    console.print("[bold]Available Nginx Sites:[/bold]")
    for i, site in enumerate(sites, 1):
        console.print(f"  [{i}] {site}")
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Select site to edit (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    config_file = f"/etc/nginx/sites-available/{site}"
    
    try:
        # Open in nano editor
        subprocess.run(["sudo", "nano", config_file], check=True)
        
        # Test configuration
        result = subprocess.run(["sudo", "nginx", "-t"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Configuration is valid![/green]")
            
            # Reload Nginx
            if confirm_action("Reload Nginx to apply changes?"):
                if reload_nginx():
                    console.print("[green]✓ Nginx reloaded![/green]")
                else:
                    console.print("[red]✗ Failed to reload Nginx[/red]")
        else:
            console.print(f"[red]✗ Configuration is invalid:[/red] {result.stderr}")
            
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _edit_php_config() -> None:
    """Edit PHP configuration."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get PHP versions
    php_versions = []
    if os.path.exists("/etc/php"):
        php_versions = [d for d in os.listdir("/etc/php") if d.startswith("7.") or d.startswith("8.")]
    
    if not php_versions:
        console.print("[yellow]No PHP installations found.[/yellow]")
        return
    
    # Select PHP version
    version = get_user_input(
        "Select PHP version",
        choices=php_versions
    )
    
    config_file = f"/etc/php/{version}/apache2/php.ini"
    
    try:
        # Open in nano editor
        subprocess.run(["sudo", "nano", config_file], check=True)
        
        # Restart PHP-FPM
        if confirm_action(f"Restart PHP {version}-FPM to apply changes?"):
            if _restart_service(f"php{version}-fpm"):
                console.print(f"[green]✓ PHP {version}-FPM restarted![/green]")
            else:
                console.print(f"[red]✗ Failed to restart PHP {version}-FPM[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _edit_mysql_config() -> None:
    """Edit MySQL configuration."""
    from ..cli.menu import console
    import subprocess
    
    try:
        # Open in nano editor
        subprocess.run(["sudo", "nano", "/etc/mysql/my.cnf"], check=True)
        
        # Restart MySQL
        if confirm_action("Restart MySQL to apply changes?"):
            if _restart_service("mysql"):
                console.print("[green]✓ MySQL restarted![/green]")
            else:
                console.print("[red]✗ Failed to restart MySQL[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _edit_mariadb_config() -> None:
    """Edit MariaDB configuration."""
    from ..cli.menu import console
    import subprocess
    
    try:
        # Open in nano editor
        subprocess.run(["sudo", "nano", "/etc/mysql/my.cnf"], check=True)
        
        # Restart MariaDB
        if confirm_action("Restart MariaDB to apply changes?"):
            if _restart_service("mariadb"):
                console.print("[green]✓ MariaDB restarted![/green]")
            else:
                console.print("[red]✗ Failed to restart MariaDB[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _edit_php_fpm_config() -> None:
    """Edit PHP-FPM configuration."""
    from ..cli.menu import console
    import subprocess
    import os
    
    # Get PHP versions
    php_versions = []
    if os.path.exists("/etc/php"):
        php_versions = [d for d in os.listdir("/etc/php") if d.startswith("7.") or d.startswith("8.")]
    
    if not php_versions:
        console.print("[yellow]No PHP-FPM installations found.[/yellow]")
        return
    
    # Select PHP version
    version = get_user_input(
        "Select PHP-FPM version",
        choices=php_versions
    )
    
    config_file = f"/etc/php/{version}/fpm/pool.d/www.conf"
    
    try:
        # Open in nano editor
        subprocess.run(["sudo", "nano", config_file], check=True)
        
        # Test configuration
        result = subprocess.run([
            "php-fpm{version}", "-t"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Configuration is valid![/green]")
            
            # Restart PHP-FPM
            if confirm_action(f"Restart PHP {version}-FPM to apply changes?"):
                if _restart_service(f"php{version}-fpm"):
                    console.print(f"[green]✓ PHP {version}-FPM restarted![/green]")
                else:
                    console.print(f"[red]✗ Failed to restart PHP {version}-FPM[/red]")
        else:
            console.print(f"[red]✗ Configuration is invalid:[/red] {result.stderr}")
            
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _edit_ssl_config() -> None:
    """Edit SSL certificate configuration."""
    from ..cli.menu import console
    
    console.print("[yellow]SSL certificates cannot be edited directly.[/yellow]")
    console.print("To update SSL certificates:")
    console.print("1. For Let's Encrypt: Use 'Manage SSL certificates' option")
    console.print("2. For custom certificates: Replace certificate files and restart services")


def _edit_system_config() -> None:
    """Edit system configuration."""
    from ..cli.menu import console
    
    console.print("[yellow]System configuration requires manual editing.[/yellow]")
    console.print("Common system configuration files:")
    console.print("  /etc/hosts - Host name resolution")
    console.print("  /etc/fstab - File system mount points")
    console.print("  /etc/sysctl.conf - Kernel parameters")
    console.print("  /etc/limits.conf - User limits")


def _edit_kurserver_config() -> None:
    """Edit KurServer configuration."""
    from ..cli.menu import console
    import os
    import json
    import subprocess
    
    config_file = os.path.expanduser("~/.kurserver/config.json")
    
    # Create config if it doesn't exist
    if not os.path.exists(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump({}, f)
    
    try:
        # Open in nano editor
        subprocess.run(["nano", config_file], check=True)
        console.print("[green]✓ Configuration updated![/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to edit configuration:[/red] {e}")


def _create_backup(configs: list, backup_name: str, verbose: bool = False) -> None:
    """
    Create configuration backup.
    
    Args:
        configs (list): List of configurations to backup
        backup_name (str): Backup name
        verbose (bool): Enable verbose output
    """
    import os
    import shutil
    import subprocess
    from datetime import datetime
    
    # Create backup directory
    backup_dir = os.path.expanduser(f"~/.kurserver/backups/{backup_name}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup each configuration
    for config in configs:
        if verbose:
            logger.info(f"Backing up {config} configuration...")
        
        if config == "nginx":
            if os.path.exists("/etc/nginx"):
                shutil.copytree("/etc/nginx", f"{backup_dir}/nginx", dirs_exist_ok=True)
        
        elif config == "php":
            if os.path.exists("/etc/php"):
                shutil.copytree("/etc/php", f"{backup_dir}/php", dirs_exist_ok=True)
        
        elif config in ["mysql", "mariadb"]:
            if os.path.exists("/etc/mysql"):
                shutil.copytree("/etc/mysql", f"{backup_dir}/mysql", dirs_exist_ok=True)
        
        elif config == "php-fpm":
            if os.path.exists("/etc/php"):
                shutil.copytree("/etc/php", f"{backup_dir}/php-fpm", dirs_exist_ok=True)
        
        elif config == "ssl":
            if os.path.exists("/etc/ssl"):
                shutil.copytree("/etc/ssl", f"{backup_dir}/ssl", dirs_exist_ok=True)
            if os.path.exists("/etc/letsencrypt"):
                shutil.copytree("/etc/letsencrypt", f"{backup_dir}/letsencrypt", dirs_exist_ok=True)
        
        elif config == "system":
            # Backup system info
            with open(f"{backup_dir}/system_info.txt", 'w') as f:
                f.write(f"System backup created at {datetime.now().isoformat()}\n\n")
                
                # System information
                result = subprocess.run(["uname", "-a"], capture_output=True, text=True)
                f.write(f"System: {result.stdout.strip()}\n")
                
                # Memory information
                with open("/proc/meminfo", 'r') as meminfo:
                    f.write("\nMemory Information:\n")
                    f.write(meminfo.read())
                
                # Disk information
                result = subprocess.run(["df", "-h"], capture_output=True, text=True)
                f.write(f"\nDisk Usage:\n{result.stdout}")
        
        elif config == "kurserver":
            kurserver_dir = os.path.expanduser("~/.kurserver")
            if os.path.exists(kurserver_dir):
                shutil.copytree(kurserver_dir, f"{backup_dir}/kurserver", dirs_exist_ok=True)
    
    # Create backup metadata
    metadata = {
        "name": backup_name,
        "created_at": datetime.now().isoformat(),
        "configs": configs,
        "system": os.uname().sysname
    }
    
    import json
    with open(f"{backup_dir}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Configuration backup '{backup_name}' created successfully")


def _get_available_backups() -> list:
    """Get list of available configuration backups."""
    import os
    
    backup_dir = os.path.expanduser("~/.kurserver/backups")
    
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for item in os.listdir(backup_dir):
        if os.path.isdir(os.path.join(backup_dir, item)):
            backups.append(item)
    
    return sorted(backups, reverse=True)


def _restore_backup(backup_name: str, configs: list = None, verbose: bool = False) -> None:
    """
    Restore configuration from backup.
    
    Args:
        backup_name (str): Backup name
        configs (list): List of configurations to restore (None for all)
        verbose (bool): Enable verbose output
    """
    import os
    import shutil
    import json
    
    backup_dir = os.path.expanduser(f"~/.kurserver/backups/{backup_name}")
    
    if not os.path.exists(backup_dir):
        raise Exception(f"Backup '{backup_name}' not found")
    
    # Read backup metadata
    with open(f"{backup_dir}/metadata.json", 'r') as f:
        metadata = json.load(f)
    
    # Restore configurations
    configs_to_restore = configs or metadata["configs"]
    
    for config in configs_to_restore:
        if verbose:
            logger.info(f"Restoring {config} configuration...")
        
        if config == "nginx":
            if os.path.exists(f"{backup_dir}/nginx"):
                shutil.rmtree("/etc/nginx", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/nginx", "/etc/nginx")
        
        elif config == "php":
            if os.path.exists(f"{backup_dir}/php"):
                shutil.rmtree("/etc/php", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/php", "/etc/php")
        
        elif config in ["mysql", "mariadb"]:
            if os.path.exists(f"{backup_dir}/mysql"):
                shutil.rmtree("/etc/mysql", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/mysql", "/etc/mysql")
        
        elif config == "php-fpm":
            if os.path.exists(f"{backup_dir}/php-fpm"):
                shutil.rmtree("/etc/php", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/php-fpm", "/etc/php")
        
        elif config == "ssl":
            if os.path.exists(f"{backup_dir}/ssl"):
                shutil.rmtree("/etc/ssl", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/ssl", "/etc/ssl")
            if os.path.exists(f"{backup_dir}/letsencrypt"):
                shutil.rmtree("/etc/letsencrypt", ignore_errors=True)
                shutil.copytree(f"{backup_dir}/letsencrypt", "/etc/letsencrypt")
        
        elif config == "kurserver":
            if os.path.exists(f"{backup_dir}/kurserver"):
                kurserver_dir = os.path.expanduser("~/.kurserver")
                shutil.rmtree(kurserver_dir, ignore_errors=True)
                shutil.copytree(f"{backup_dir}/kurserver", kurserver_dir)
    
    logger.info(f"Configuration backup '{backup_name}' restored successfully")


def _validate_single_config(config: str, verbose: bool = False) -> dict:
    """
    Validate a single configuration.
    
    Args:
        config (str): Configuration type
        verbose (bool): Enable verbose output
    
    Returns:
        dict: Validation result
    """
    import subprocess
    
    result = {"valid": False, "error": None, "suggestion": None}
    
    try:
        if config == "nginx":
            # Test Nginx configuration
            test_result = subprocess.run(
                ["sudo", "nginx", "-t"],
                capture_output=True, text=True
            )
            
            if test_result.returncode == 0:
                result["valid"] = True
            else:
                result["error"] = test_result.stderr
                result["suggestion"] = "Check syntax in /etc/nginx/sites-available/ files"
        
        elif config == "php":
            # Test PHP configuration
            test_result = subprocess.run(
                ["php", "-l", "/etc/php/8.1/apache2/php.ini"],
                capture_output=True, text=True
            )
            
            if test_result.returncode == 0:
                result["valid"] = True
            else:
                result["error"] = test_result.stderr
                result["suggestion"] = "Check PHP syntax in php.ini file"
        
        elif config in ["mysql", "mariadb"]:
            # Test MySQL/MariaDB configuration
            test_result = subprocess.run(
                ["sudo", "mysqld", "--help", "--verbose"],
                capture_output=True, text=True
            )
            
            # This is a basic check - more thorough testing would require starting the service
            result["valid"] = True
            result["suggestion"] = "Manual verification recommended for database configurations"
        
        elif config == "php-fpm":
            # Test PHP-FPM configuration
            test_result = subprocess.run(
                ["php-fpm8.1", "-t"],
                capture_output=True, text=True
            )
            
            if test_result.returncode == 0:
                result["valid"] = True
            else:
                result["error"] = test_result.stderr
                result["suggestion"] = "Check PHP-FPM pool configuration"
        
        elif config == "ssl":
            # Basic SSL certificate validation
            result["valid"] = True
            result["suggestion"] = "Manual certificate verification recommended"
    
    except Exception as e:
        result["error"] = str(e)
        result["suggestion"] = "Check file permissions and paths"
    
    return result


def _reset_single_config(config: str, verbose: bool = False) -> None:
    """
    Reset a single configuration to defaults.
    
    Args:
        config (str): Configuration type
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Resetting {config} configuration to defaults...")
    
    if config == "nginx":
        # Remove custom configurations
        subprocess.run(["sudo", "rm", "-rf", "/etc/nginx/sites-available/*"], check=True)
        subprocess.run(["sudo", "rm", "-rf", "/etc/nginx/sites-enabled/*"], check=True)
        
        # Restore default configuration
        subprocess.run(["sudo", "apt", "install", "--reinstall", "nginx", "-y"], check=True)
    
    elif config == "php":
        # Restore default PHP configuration
        subprocess.run(["sudo", "apt", "install", "--reinstall", "php8.1-common", "-y"], check=True)
    
    elif config in ["mysql", "mariadb"]:
        # Restore default database configuration
        subprocess.run(["sudo", "apt", "install", "--reinstall", config, "-y"], check=True)
    
    elif config == "php-fpm":
        # Restore default PHP-FPM configuration
        subprocess.run(["sudo", "apt", "install", "--reinstall", "php8.1-fpm", "-y"], check=True)
    
    elif config == "kurserver":
        # Reset KurServer configuration
        kurserver_dir = os.path.expanduser("~/.kurserver")
        if os.path.exists(kurserver_dir):
            import shutil
            shutil.rmtree(kurserver_dir)
    
    logger.info(f"{config} configuration reset successfully")


def _restart_service(service: str, verbose: bool = False) -> None:
    """
    Restart a service.
    
    Args:
        service (str): Service name
        verbose (bool): Enable verbose output
    """
    import subprocess
    
    if verbose:
        logger.info(f"Restarting {service} service...")
    
    service_map = {
        "nginx": "nginx",
        "php": "php8.1-fpm",
        "php-fpm": "php8.1-fpm",
        "mysql": "mysql",
        "mariadb": "mariadb"
    }
    
    if service in service_map:
        _restart_service(service_map[service])
    
    logger.info(f"{service} service restarted successfully")


def _restart_services_after_restore(configs: list, verbose: bool = False) -> None:
    """
    Restart services after configuration restore.
    
    Args:
        configs (list): List of configurations that were restored
        verbose (bool): Enable verbose output
    """
    services_to_restart = []
    
    if "nginx" in configs:
        services_to_restart.append("nginx")
    
    if "php" in configs or "php-fpm" in configs:
        services_to_restart.append("php-fpm")
    
    if "mysql" in configs:
        services_to_restart.append("mysql")
    
    if "mariadb" in configs:
        services_to_restart.append("mariadb")
    
    for service in services_to_restart:
        _restart_service(service, verbose)


def _restart_service(service_name: str, verbose: bool = False) -> bool:
    """
    Restart a service using appropriate method for the environment.
    
    Args:
        service_name (str): Name of the service to restart
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    import subprocess
    
    if verbose:
        logger.info(f"Restarting {service_name} service...")
    
    # Check if we're in a container environment
    if is_container_environment():
        try:
            # In containers, try to restart using service command
            subprocess.run(['sudo', 'service', service_name, 'restart'], check=True)
            return True
        except subprocess.SubprocessError:
            try:
                # Fallback to direct command if available
                if service_name == 'nginx':
                    subprocess.run(['sudo', 'nginx', '-s', 'reload'], check=True)
                    return True
                # Add more service-specific commands as needed
            except subprocess.SubprocessError:
                return False
    else:
        # In regular systems, use systemctl
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
            return True
        except subprocess.SubprocessError:
            return False