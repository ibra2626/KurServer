"""
Interactive menu system for KurServer CLI.
"""

import sys
from typing import Dict, List, Callable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.exceptions import KurServerError
from ..core.logger import get_logger, debug_log
from ..core.system import get_system_info, get_service_status

# Initialize Rich console
console = Console()
logger = get_logger()


class MenuOption:
    """Represents a menu option with its action and description."""
    
    def __init__(self, key: str, description: str, action: Optional[Callable] = None, submenu: Optional['Menu'] = None):
        self.key = key
        self.description = description
        self.action = action
        self.submenu = submenu
    
    def execute(self, verbose: bool = False) -> bool:
        """Execute the menu option's action or navigate to submenu."""
        if self.submenu:
            self.submenu.display(verbose=verbose)
            return True
        elif self.action:
            try:
                self.action(verbose=verbose)
                return True
            except KurServerError as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                if e.suggestion:
                    console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
                return False
            except Exception as e:
                console.print(f"[bold red]Unexpected error:[/bold red] {e}")
                logger.error(f"Unexpected error in menu option {self.key}: {e}")
                return False
        else:
            console.print("[yellow]This option is not yet implemented.[/yellow]")
            return False


class Menu:
    """Interactive menu system with navigation and option execution."""
    
    def __init__(self, title: str, options: List[MenuOption], show_status: bool = True):
        self.title = title
        self.options = options
        self.show_status = show_status
    
    def display(self, verbose: bool = False) -> None:
        """Display the menu and handle user interaction."""
        while True:
            try:
                self._render_menu(verbose)
                
                # Get user input
                choice = Prompt.ask(
                    "\n[bold blue]Select an option[/bold blue]",
                    choices=[opt.key for opt in self.options] + ['q', 'quit'],
                    default='q'
                ).lower()
                
                if choice in ['q', 'quit']:
                    console.print("[yellow]Exiting menu...[/yellow]")
                    break
                
                # Find and execute the selected option
                selected_option = self._find_option(choice)
                if selected_option:
                    selected_option.execute(verbose)
                    
                    # Pause after action execution (unless it was a submenu)
                    if not selected_option.submenu:
                        input("\nPress Enter to continue...")
                else:
                    console.print(f"[red]Invalid option: {choice}[/red]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user.[/yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]Unexpected error:[/bold red] {e}")
                logger.error(f"Unexpected error in menu: {e}")
                break
    
    def _render_menu(self, verbose: bool = False) -> None:
        """Render the menu interface."""
        console.clear()
        
        # Create title panel
        title_panel = Panel(
            f"[bold blue]{self.title}[/bold blue]",
            border_style="blue"
        )
        console.print(title_panel)
        
        # Show system status if enabled
        if self.show_status:
            self._show_system_status()
        
        # Create options table
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Description", style="white")
        
        for option in self.options:
            table.add_row(f"[{option.key}]", option.description)
        
        table.add_row("[q]", "Quit/Exit", style="red")
        
        console.print("\n[bold]Menu Options:[/bold]")
        console.print(table)
    
    def _show_system_status(self) -> None:
        """Display system status information."""
        try:
            # Get system info
            system_info = get_system_info()
            pretty_name = system_info.get('pretty_name', 'Unknown')
            
            # Get service status
            services = get_service_status()
            
            # Create status table
            status_table = Table(show_header=True, box=None, title=f"System Status: {pretty_name}")
            status_table.add_column("Service", style="cyan")
            status_table.add_column("Status", style="white")
            
            # Add service statuses
            for service_name, status in services.items():
                if status['installed']:
                    if status['running']:
                        status_text = "[green]Running[/green]"
                    else:
                        status_text = "[red]Stopped[/red]"
                else:
                    status_text = "[dim]Not installed[/dim]"
                
                status_table.add_row(service_name, status_text)
            
            console.print(status_table)
            console.print()
            
        except Exception as e:
            logger.warning(f"Failed to show system status: {e}")
    
    def _find_option(self, choice: str) -> Optional[MenuOption]:
        """Find a menu option by its key."""
        for option in self.options:
            if option.key.lower() == choice:
                return option
        return None


def show_progress(description: str, task_func, *args, **kwargs):
    """
    Show a progress spinner while executing a task.
    
    Args:
        description (str): Description of the task
        task_func (Callable): Function to execute
        *args: Arguments to pass to task_func
        **kwargs: Keyword arguments to pass to task_func
    
    Returns:
        Result of task_func
    """
    # DEBUG: Log function entry
    debug_log(logger, "general", f"show_progress starting: {description}, function: {task_func.__name__}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description, total=None)
        
        try:
            debug_log(logger, "general", f"Executing task function: {task_func.__name__}")
            result = task_func(*args, **kwargs)
            debug_log(logger, "general", f"Task function completed successfully with result: {result}")
            progress.update(task, description=f"[green]✓ {description}[/green]")
            debug_log(logger, "general", "Progress updated to success, about to return result")
            return result
        except Exception as e:
            logger.error(f"[DEBUG] Task function failed with exception: {type(e).__name__}: {e}")
            logger.error(f"[DEBUG] Exception traceback: {e.__traceback__}")
            progress.update(task, description=f"[red]✗ {description}[/red]")
            logger.error(f"[DEBUG] Progress updated to failure, about to re-raise exception")
            raise


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask for user confirmation with a styled prompt.
    
    Args:
        message (str): Confirmation message
        default (bool): Default value if user just presses Enter
    
    Returns:
        bool: True if user confirms, False otherwise
    """
    return Confirm.ask(f"[bold yellow]{message}[/bold yellow]", default=default)


def get_user_input(message: str, choices: List[str] = None, default: str = None, password: bool = False) -> str:
    """
    Get user input with a styled prompt.
    
    Args:
        message (str): Input prompt message
        choices (List[str], optional): List of valid choices
        default (str, optional): Default value
        password (bool): Whether to hide input (for passwords)
    
    Returns:
        str: User input
    """
    if password:
        return Prompt.ask(f"[bold blue]{message}[/bold blue]", default=default, password=True)
    elif choices:
        return Prompt.ask(f"[bold blue]{message}[/bold blue]", choices=choices, default=default)
    else:
        return Prompt.ask(f"[bold blue]{message}[/bold blue]", default=default)


def create_main_menu() -> Menu:
    """
    Create the main menu with all available options.
    
    Returns:
        Menu: Configured main menu
    """
    from ..installers.nginx import install_nginx_menu
    from ..installers.mysql import install_mysql_menu
    from ..installers.php import install_php_menu
    from ..installers.nvm import install_nvm_menu
    from ..managers.nginx import site_management_menu
    from ..managers.database import manage_database_menu
    from ..managers.github_settings import github_settings_menu
    from ..managers.nvm import nvm_management_menu
    from ..config.manager import config_management_menu
    
    options = [
        MenuOption("1", "Install Nginx", action=install_nginx_menu),
        MenuOption("2", "Install MySQL/MariaDB", action=install_mysql_menu),
        MenuOption("3", "Install PHP-FPM", action=install_php_menu),
        MenuOption("4", "Install NVM (Node Version Manager)", action=install_nvm_menu),
        MenuOption("5", "Site Management", action=site_management_menu),
        MenuOption("6", "Manage databases", action=manage_database_menu),
        MenuOption("7", "NVM management", action=nvm_management_menu),
        MenuOption("8", "GitHub settings", action=github_settings_menu),
        MenuOption("9", "Configuration management", action=config_management_menu),
        MenuOption("10", "System status", action=show_system_status_menu),
        MenuOption("11", "Uninstall components", action=uninstall_main_menu),
    ]
    
    return Menu("KurServer CLI - Main Menu", options)


def main_menu(verbose: bool = False) -> None:
    """
    Display the main menu and handle user interaction.
    
    Args:
        verbose (bool): Enable verbose output
    """
    menu = create_main_menu()
    menu.display(verbose=verbose)


def show_system_status_menu(verbose: bool = False) -> None:
    """Show detailed system status information."""
    console.clear()
    console.print("[bold blue]System Status[/bold blue]")
    console.print()
    
    try:
        # System information
        system_info = get_system_info()
        
        info_table = Table(show_header=True, box=None, title="System Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")
        
        for key, value in system_info.items():
            info_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(info_table)
        console.print()
        
        # Service status
        services = get_service_status()
        
        service_table = Table(show_header=True, box=None, title="Service Status")
        service_table.add_column("Service", style="cyan")
        service_table.add_column("Installed", style="white")
        service_table.add_column("Running", style="white")
        service_table.add_column("Enabled", style="white")
        
        for service_name, status in services.items():
            installed = "[green]Yes[/green]" if status['installed'] else "[red]No[/red]"
            running = "[green]Yes[/green]" if status['running'] else "[red]No[/red]"
            enabled = "[green]Yes[/green]" if status['enabled'] else "[red]No[/red]"
            
            service_table.add_row(service_name, installed, running, enabled)
        
        console.print(service_table)
        
    except Exception as e:
        console.print(f"[bold red]Error getting system status:[/bold red] {e}")



def uninstall_main_menu(verbose: bool = False) -> None:
    """
    Display the uninstallation menu and handle user interaction.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from .uninstall_menu import uninstall_menu
    uninstall_menu(verbose=verbose)