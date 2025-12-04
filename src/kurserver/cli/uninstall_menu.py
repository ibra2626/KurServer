"""
Uninstallation menu for KurServer CLI.
"""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..cli.menu import MenuOption, Menu, confirm_action, get_user_input
from ..core.logger import get_logger
from ..core.system import is_package_installed
from ..uninstallers.nginx import NginxUninstaller
from ..uninstallers.mysql import MySQLUninstaller
from ..uninstallers.php import PHPUninstaller
from ..utils.backup import BackupManager

console = Console()
logger = get_logger()


def uninstall_menu(verbose: bool = False) -> None:
    """
    Display uninstallation menu and handle user interaction.
    
    Args:
        verbose (bool): Enable verbose output
    """
    options = [
        MenuOption("1", "Uninstall Nginx", action=uninstall_nginx_menu),
        MenuOption("2", "Uninstall MySQL/MariaDB", action=uninstall_mysql_menu),
        MenuOption("3", "Uninstall PHP-FPM", action=uninstall_php_menu),
        MenuOption("4", "Uninstall all components", action=uninstall_all_menu),
        MenuOption("5", "Backup management", action=backup_management_menu),
        MenuOption("6", "Rollback from backup", action=rollback_menu),
    ]
    
    menu = Menu("KurServer CLI - Uninstallation Menu", options, show_status=True)
    menu.display(verbose=verbose)


def uninstall_nginx_menu(verbose: bool = False) -> None:
    """Handle Nginx uninstallation."""
    console.print("[bold red]Nginx Uninstallation[/bold red]")
    console.print("This will remove Nginx web server and all its configurations.")
    console.print("[yellow]Warning: This will remove all website configurations![/yellow]")
    console.print()
    
    # Check if Nginx is installed
    if not is_package_installed('nginx'):
        console.print("[yellow]Nginx is not installed.[/yellow]")
        return
    
    # Show what will be removed
    console.print("[bold]The following will be removed:[/bold]")
    console.print("• Nginx web server package")
    console.print("• All Nginx configuration files")
    console.print("• All website configurations")
    console.print("• Nginx log files")
    console.print("• SSL certificates (if any)")
    console.print()
    
    # Confirm uninstallation
    if not confirm_action("Are you sure you want to uninstall Nginx?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    # Additional confirmation
    if not confirm_action("This action cannot be undone. Continue anyway?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    try:
        uninstaller = NginxUninstaller()
        
        if uninstaller.uninstall(verbose=verbose):
            console.print("[bold green]✓ Nginx uninstalled successfully![/bold green]")
            console.print("[green]A backup has been created for safety.[/green]")
            
            # Show restart warning
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print("[yellow]After removing Nginx, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
        else:
            console.print("[bold red]✗ Nginx uninstallation failed![/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]✗ Uninstallation error:[/bold red] {e}")
        logger.error(f"Nginx uninstallation error: {e}")


def uninstall_mysql_menu(verbose: bool = False) -> None:
    """Handle MySQL/MariaDB uninstallation."""
    console.print("[bold red]MySQL/MariaDB Uninstallation[/bold red]")
    console.print("This will remove database server and all its data.")
    console.print("[yellow]Warning: This will delete all databases![/yellow]")
    console.print()
    
    # Check which database is installed
    mysql_installed = is_package_installed('mysql-server')
    mariadb_installed = is_package_installed('mariadb-server')
    
    if not mysql_installed and not mariadb_installed:
        console.print("[yellow]Neither MySQL nor MariaDB is installed.[/yellow]")
        return
    
    db_type = "MySQL" if mysql_installed else "MariaDB"
    
    # Show what will be removed
    console.print(f"[bold]The following will be removed:[/bold]")
    console.print(f"• {db_type} server package")
    console.print("• All databases and data")
    console.print("• All database users and permissions")
    console.print("• Database configuration files")
    console.print("• Database log files")
    console.print()
    
    # Confirm uninstallation
    if not confirm_action(f"Are you sure you want to uninstall {db_type}?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    # Additional confirmation
    if not confirm_action("This will permanently delete all databases. Continue anyway?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    try:
        uninstaller = MySQLUninstaller()
        
        if uninstaller.uninstall(verbose=verbose):
            console.print(f"[bold green]✓ {db_type} uninstalled successfully![/bold green]")
            console.print("[green]A backup of all databases has been created for safety.[/green]")
            
            # Show restart warning
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print(f"[yellow]After removing {db_type}, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
        else:
            console.print(f"[bold red]✗ {db_type} uninstallation failed![/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]✗ Uninstallation error:[/bold red] {e}")
        logger.error(f"MySQL uninstallation error: {e}")


def uninstall_php_menu(verbose: bool = False) -> None:
    """Handle PHP-FPM uninstallation."""
    console.print("[bold red]PHP-FPM Uninstallation[/bold red]")
    console.print("This will remove PHP-FPM and all installed extensions.")
    console.print()
    
    # Check which PHP versions are installed
    php_versions = []
    for version in ["7.4", "8.0", "8.1", "8.2", "8.3"]:
        if is_package_installed(f"php{version}-fpm"):
            php_versions.append(version)
    
    if not php_versions:
        console.print("[yellow]No PHP-FPM versions are installed.[/yellow]")
        return
    
    # Select version to uninstall
    if len(php_versions) == 1:
        selected_version = php_versions[0]
    else:
        selected_version = get_user_input(
            "Select PHP version to uninstall:",
            choices=php_versions
        )
    
    # Show what will be removed
    console.print(f"[bold]The following will be removed:[/bold]")
    console.print(f"• PHP {selected_version}-FPM package")
    console.print(f"• All PHP {selected_version} extensions")
    console.print(f"• PHP {selected_version} configuration files")
    console.print(f"• PHP {selected_version} log files")
    console.print()
    
    # Confirm uninstallation
    if not confirm_action(f"Are you sure you want to uninstall PHP {selected_version}-FPM?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    try:
        uninstaller = PHPUninstaller(selected_version)
        
        if uninstaller.uninstall(verbose=verbose):
            console.print(f"[bold green]✓ PHP {selected_version}-FPM uninstalled successfully![/bold green]")
            console.print("[green]A backup has been created for safety.[/green]")
            
            # Show restart warning
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print(f"[yellow]After removing PHP {selected_version}-FPM, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
        else:
            console.print(f"[bold red]✗ PHP {selected_version}-FPM uninstallation failed![/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]✗ Uninstallation error:[/bold red] {e}")
        logger.error(f"PHP uninstallation error: {e}")


def uninstall_all_menu(verbose: bool = False) -> None:
    """Handle uninstallation of all components."""
    console.print("[bold red]Complete System Uninstallation[/bold red]")
    console.print("This will remove all web server components from your system.")
    console.print("[yellow]Warning: This will remove everything![/yellow]")
    console.print()
    
    # Check what's installed
    nginx_installed = is_package_installed('nginx')
    mysql_installed = is_package_installed('mysql-server') or is_package_installed('mariadb-server')
    php_installed = any(is_package_installed(f"php{v}-fpm") for v in ["7.4", "8.0", "8.1", "8.2", "8.3"])
    
    if not nginx_installed and not mysql_installed and not php_installed:
        console.print("[yellow]No supported components are installed.[/yellow]")
        return
    
    # Show what will be removed
    console.print("[bold]The following components will be removed:[/bold]")
    if nginx_installed:
        console.print("• Nginx web server")
    if mysql_installed:
        console.print("• MySQL/MariaDB database server")
    if php_installed:
        console.print("• PHP-FPM and all extensions")
    console.print()
    
    # Multiple confirmations
    if not confirm_action("Are you sure you want to uninstall all components?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    if not confirm_action("This will remove all web services. Continue anyway?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    if not confirm_action("Final warning: This action cannot be undone. Continue?"):
        console.print("[yellow]Uninstallation cancelled.[/yellow]")
        return
    
    try:
        success_count = 0
        total_count = 0
        
        # Uninstall Nginx
        if nginx_installed:
            total_count += 1
            uninstaller = NginxUninstaller()
            if uninstaller.uninstall(verbose=verbose):
                success_count += 1
                console.print("[green]✓ Nginx uninstalled[/green]")
            else:
                console.print("[red]✗ Nginx uninstallation failed[/red]")
        
        # Uninstall MySQL/MariaDB
        if mysql_installed:
            total_count += 1
            try:
                uninstaller = MySQLUninstaller()
                if uninstaller.uninstall(verbose=verbose):
                    success_count += 1
                    console.print("[green]✓ MySQL/MariaDB uninstalled[/green]")
                else:
                    console.print("[red]✗ MySQL/MariaDB uninstallation failed[/red]")
            except Exception as e:
                console.print("[red]✗ MySQL/MariaDB uninstallation failed[/red]")
                logger.error(f"MySQL uninstallation error: {e}")
        
        # Uninstall PHP-FPM
        if php_installed:
            total_count += 1
            for version in ["7.4", "8.0", "8.1", "8.2", "8.3"]:
                if is_package_installed(f"php{version}-fpm"):
                    uninstaller = PHPUninstaller(version)
                    if uninstaller.uninstall(verbose=verbose):
                        console.print(f"[green]✓ PHP {version}-FPM uninstalled[/green]")
                    else:
                        console.print(f"[red]✗ PHP {version}-FPM uninstallation failed[/red]")
        
        # Summary
        if success_count == total_count:
            console.print("[bold green]✓ All components uninstalled successfully![/bold green]")
            console.print("[green]Backups have been created for safety.[/green]")
            
            # Show restart warning
            console.print()
            console.print("[bold yellow]⚠️  IMPORTANT WARNING[/bold yellow]")
            console.print("[yellow]After removing components, some processes may still be running in memory.[/yellow]")
            console.print("[yellow]It is recommended to restart your operating system to ensure all components are properly cleared.[/yellow]")
        else:
            console.print(f"[bold yellow]⚠ {success_count}/{total_count} components uninstalled successfully[/bold yellow]")
            
    except Exception as e:
        console.print(f"[bold red]✗ Uninstallation error:[/bold red] {e}")
        logger.error(f"Complete uninstallation error: {e}")


def backup_management_menu(verbose: bool = False) -> None:
    """Display backup management menu."""
    console.print("[bold blue]Backup Management[/bold blue]")
    console.print()
    
    # Get backup managers for each component
    components = ["nginx", "mysql", "php"]
    
    for component in components:
        backup_manager = BackupManager(component)
        backups = backup_manager.list_backups(verbose)
        
        console.print(f"[bold]{component.title()} Backups:[/bold]")
        
        if not backups:
            console.print(f"  [dim]No backups found[/dim]")
        else:
            table = Table(show_header=True, box=None)
            table.add_column("Timestamp", style="cyan")
            table.add_column("Size", style="white")
            table.add_column("Created", style="white")
            
            for backup in backups[:5]:  # Show latest 5 backups
                table.add_row(
                    backup["timestamp"],
                    backup["size"],
                    backup["created_at"][:19]  # Remove microseconds
                )
            
            console.print(table)
        
        console.print()
    
    input("Press Enter to continue...")


def rollback_menu(verbose: bool = False) -> None:
    """Handle rollback from backup."""
    console.print("[bold blue]Rollback from Backup[/bold blue]")
    console.print()
    
    # Select component
    component = get_user_input(
        "Select component to rollback:",
        choices=["nginx", "mysql", "php"]
    )
    
    backup_manager = BackupManager(component)
    backups = backup_manager.list_backups(verbose)
    
    if not backups:
        console.print(f"[yellow]No backups found for {component}[/yellow]")
        return
    
    # Display available backups
    console.print(f"[bold]Available {component.title()} Backups:[/bold]")
    
    for i, backup in enumerate(backups, 1):
        console.print(f"{i}. {backup['timestamp']} - {backup['size']} - {backup['created_at'][:19]}")
    
    # Select backup
    try:
        choice = int(get_user_input("Select backup number:")) - 1
        if choice < 0 or choice >= len(backups):
            console.print("[red]Invalid selection[/red]")
            return
        
        selected_backup = backups[choice]
        
        # Confirm rollback
        console.print(f"[bold]Selected backup:[/bold] {selected_backup['timestamp']}")
        console.print(f"[bold]Created:[/bold] {selected_backup['created_at']}")
        console.print(f"[bold]Size:[/bold] {selected_backup['size']}")
        console.print()
        
        if not confirm_action("Are you sure you want to rollback to this backup?"):
            console.print("[yellow]Rollback cancelled[/yellow]")
            return
        
        # Perform rollback
        if backup_manager.restore_backup(selected_backup['timestamp'], verbose):
            console.print("[bold green]✓ Rollback completed successfully![/bold green]")
        else:
            console.print("[bold red]✗ Rollback failed![/bold red]")
            
    except ValueError:
        console.print("[red]Invalid input[/red]")
    except Exception as e:
        console.print(f"[bold red]✗ Rollback error:[/bold red] {e}")
        logger.error(f"Rollback error: {e}")