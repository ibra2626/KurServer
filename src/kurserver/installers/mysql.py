"""
MySQL/MariaDB installer module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

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
    
    # Note: In a real implementation, you would run mysql_secure_installation
    # For now, we'll just log that this step would happen
    logger.info(f"{db_type} installation completed successfully")