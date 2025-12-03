"""
PHP-FPM installer module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

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
        choices=["7.4", "8.0", "8.1", "8.2"],
        default="8.1"
    )
    
    # Check if already installed
    from ..core.system import is_package_installed
    php_package = f"php{php_choice}-fpm"
    if is_package_installed(php_package):
        if not confirm_action(f"PHP {php_choice} is already installed. Do you want to reinstall?"):
            return
    
    # Ask about extensions
    console.print(f"[bold]PHP {php_choice} Installation Options:[/bold]")
    install_extensions = confirm_action("Do you want to install common PHP extensions?")
    
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
        
        if install_extensions:
            console.print("[green]✓ Common PHP extensions installed![/green]")
        
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
    
    # Add PPA for older PHP versions if needed
    if version in ["7.4", "8.0"]:
        if verbose:
            logger.info("Adding PHP PPA for older versions...")
        
        # Add PPA
        subprocess.run([
            "sudo", "apt", "install", "-y", "software-properties-common"
        ], check=True)
        
        subprocess.run([
            "sudo", "add-apt-repository", "-y", "ppa:ondrej/php"
        ], check=True)
        
        # Update package lists
        subprocess.run(["sudo", "apt", "update"], check=True)
    
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
    
    # Install PHP-FPM
    if verbose:
        logger.info(f"Installing PHP {version} FPM package...")
    
    php_package = f"php{version}-fpm"
    result = subprocess.run(
        ["sudo", "apt", "install", "-y", php_package],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to install {php_package}: {result.stderr}")
    
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
            f"php{version}-bcmath",
            f"php{version}-json"
        ]
        
        for ext in extensions:
            try:
                subprocess.run(["sudo", "apt", "install", "-y", ext], check=True)
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to install extension: {ext}")
    
    # Enable and start service
    if verbose:
        logger.info(f"Enabling and starting PHP {version}-FPM service...")
    
    # Enable service
    subprocess.run(["sudo", "systemctl", "enable", php_package], check=True)
    
    # Start service
    subprocess.run(["sudo", "systemctl", "start", php_package], check=True)
    
    logger.info(f"PHP {version} installation completed successfully")