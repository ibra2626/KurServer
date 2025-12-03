"""
Nginx installer module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

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
    
    # Check if already installed
    from ..core.system import is_package_installed
    if is_package_installed('nginx'):
        if not confirm_action("Nginx is already installed. Do you want to reinstall?"):
            return
    
    # Get installation preferences
    console.print("[bold]Installation Options:[/bold]")
    
    # Ask for confirmation
    if not confirm_action("Do you want to proceed with Nginx installation?"):
        console.print("[yellow]Installation cancelled.[/yellow]")
        return
    
    try:
        # Perform installation with progress
        show_progress(
            "Installing Nginx...",
            _install_nginx,
            verbose
        )
        
        console.print("[bold green]✓ Nginx installation completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"Nginx installation failed: {e}")


def _install_nginx(verbose: bool = False) -> None:
    """
    Actually install Nginx.
    
    Args:
        verbose (bool): Enable verbose output
    """
    import subprocess
    
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
    
    # Enable and start Nginx service
    if verbose:
        logger.info("Enabling and starting Nginx service...")
    
    # Enable service
    subprocess.run(["sudo", "systemctl", "enable", "nginx"], check=True)
    
    # Start service
    subprocess.run(["sudo", "systemctl", "start", "nginx"], check=True)
    
    logger.info("Nginx installation completed successfully")