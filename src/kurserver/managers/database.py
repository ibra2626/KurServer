"""
Database manager module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

logger = get_logger()


def manage_database_menu(verbose: bool = False) -> None:
    """
    Handle database management from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]Database Management[/bold blue]")
    console.print()
    
    # Check if database is installed
    from ..core.system import is_package_installed
    mysql_installed = is_package_installed('mysql-server')
    mariadb_installed = is_package_installed('mariadb-server')
    
    if not mysql_installed and not mariadb_installed:
        console.print("[red]No database server is installed. Please install MySQL or MariaDB first.[/red]")
        return
    
    # Determine which database is available
    db_type = "mysql" if mysql_installed else "mariadb"
    
    # Create submenu options
    options = [
        MenuOption("1", "Create new database", action=create_database),
        MenuOption("2", "Create database user", action=create_user),
        MenuOption("3", "List databases", action=list_databases),
        MenuOption("4", "List users", action=list_users),
        MenuOption("5", "Drop database", action=drop_database),
        MenuOption("6", "Drop user", action=drop_user),
    ]
    
    submenu = Menu(f"{db_type.title()} Database Management", options, show_status=False)
    submenu.display(verbose=verbose)


def create_database(verbose: bool = False) -> None:
    """
    Create a new database.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Create New Database[/bold blue]")
    console.print()
    
    # Get database name
    db_name = get_user_input("Enter database name")
    
    # Validate database name
    if not db_name or not db_name.replace('_', '').replace('-', '').isalnum():
        console.print("[red]Invalid database name. Use only letters, numbers, underscores, and hyphens.[/red]")
        return
    
    # Get character set
    charset = get_user_input(
        "Enter character set",
        choices=["utf8mb4", "utf8", "latin1"],
        default="utf8mb4"
    )
    
    # Get collation
    collation = get_user_input(
        "Enter collation",
        choices=["utf8mb4_unicode_ci", "utf8mb4_general_ci", "utf8_unicode_ci"],
        default="utf8mb4_unicode_ci"
    )
    
    # Confirm creation
    if not confirm_action(f"Create database '{db_name}' with charset '{charset}' and collation '{collation}'?"):
        console.print("[yellow]Database creation cancelled.[/yellow]")
        return
    
    try:
        # Create database
        show_progress(
            "Creating database...",
            _create_database,
            db_name, charset, collation, verbose
        )
        
        console.print(f"[bold green]✓ Database '{db_name}' created successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Database creation failed:[/bold red] {e}")
        logger.error(f"Database creation failed for {db_name}: {e}")


def create_user(verbose: bool = False) -> None:
    """
    Create a new database user.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Create New Database User[/bold blue]")
    console.print()
    
    # Get username
    username = get_user_input("Enter username")
    
    # Validate username
    if not username or not username.replace('_', '').replace('-', '').isalnum():
        console.print("[red]Invalid username. Use only letters, numbers, underscores, and hyphens.[/red]")
        return
    
    # Get password
    password = get_user_input("Enter password", password=True)
    confirm_password = get_user_input("Confirm password", password=True)
    
    if password != confirm_password:
        console.print("[red]Passwords do not match.[/red]")
        return
    
    # Get host
    host = get_user_input(
        "Enter host (use % for any host)",
        default="localhost"
    )
    
    # Ask about database privileges
    grant_db = confirm_action("Grant privileges on a specific database?")
    
    if grant_db:
        # Get available databases
        from ..core.system import is_package_installed
        if is_package_installed('mysql-server'):
            db_type = "mysql"
        else:
            db_type = "mariadb"
        
        databases = _get_databases(db_type)
        if not databases:
            console.print("[yellow]No databases found. Creating user without database privileges.[/yellow]")
            grant_db = False
        else:
            db_name = get_user_input(
                "Select database to grant privileges on",
                choices=databases
            )
    
    # Confirm creation
    console.print("\n[bold]User Configuration Summary:[/bold]")
    console.print(f"Username: {username}")
    console.print(f"Host: {host}")
    console.print(f"Database privileges: {'Yes - ' + db_name if grant_db else 'No'}")
    
    if not confirm_action("\nCreate this database user?"):
        console.print("[yellow]User creation cancelled.[/yellow]")
        return
    
    try:
        # Create user
        show_progress(
            "Creating database user...",
            _create_user,
            username, password, host, grant_db, db_name if grant_db else None, verbose
        )
        
        console.print(f"[bold green]✓ User '{username}' created successfully![/bold green]")
        
        if grant_db:
            console.print(f"[green]✓ Privileges granted on database '{db_name}'![/green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ User creation failed:[/bold red] {e}")
        logger.error(f"User creation failed for {username}: {e}")


def list_databases(verbose: bool = False) -> None:
    """List all databases."""
    from ..cli.menu import console
    from ..core.system import is_package_installed
    
    console.print("[bold blue]Database List[/bold blue]")
    console.print()
    
    # Determine database type
    if is_package_installed('mysql-server'):
        db_type = "mysql"
    else:
        db_type = "mariadb"
    
    try:
        databases = _get_databases(db_type)
        
        if databases:
            for db in databases:
                console.print(f"  • {db}")
        else:
            console.print("No databases found.")
            
    except Exception as e:
        console.print(f"[red]Error listing databases:[/red] {e}")


def list_users(verbose: bool = False) -> None:
    """List all database users."""
    from ..cli.menu import console
    from ..core.system import is_package_installed
    
    console.print("[bold blue]Database Users[/bold blue]")
    console.print()
    
    # Determine database type
    if is_package_installed('mysql-server'):
        db_type = "mysql"
    else:
        db_type = "mariadb"
    
    try:
        users = _get_users(db_type)
        
        if users:
            for user, host in users:
                console.print(f"  • {user}@{host}")
        else:
            console.print("No users found.")
            
    except Exception as e:
        console.print(f"[red]Error listing users:[/red] {e}")


def drop_database(verbose: bool = False) -> None:
    """Drop a database."""
    from ..cli.menu import console
    
    console.print("[bold blue]Drop Database[/bold blue]")
    console.print()
    
    # Get database name
    from ..core.system import is_package_installed
    if is_package_installed('mysql-server'):
        db_type = "mysql"
    else:
        db_type = "mariadb"
    
    databases = _get_databases(db_type)
    if not databases:
        console.print("[yellow]No databases found.[/yellow]")
        return
    
    db_name = get_user_input(
        "Select database to drop",
        choices=databases
    )
    
    if not confirm_action(f"Are you sure you want to drop database '{db_name}'? This action cannot be undone."):
        console.print("[yellow]Database drop cancelled.[/yellow]")
        return
    
    try:
        # Drop database
        show_progress(
            "Dropping database...",
            _drop_database,
            db_name, verbose
        )
        
        console.print(f"[green]✓ Database '{db_name}' dropped successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to drop database:[/red] {e}")


def drop_user(verbose: bool = False) -> None:
    """Drop a database user."""
    from ..cli.menu import console
    
    console.print("[bold blue]Drop Database User[/bold blue]")
    console.print()
    
    # Get user information
    from ..core.system import is_package_installed
    if is_package_installed('mysql-server'):
        db_type = "mysql"
    else:
        db_type = "mariadb"
    
    users = _get_users(db_type)
    if not users:
        console.print("[yellow]No users found.[/yellow]")
        return
    
    # Format user choices
    user_choices = [f"{user}@{host}" for user, host in users]
    selected_user = get_user_input(
        "Select user to drop",
        choices=user_choices
    )
    
    # Parse username and host
    username, host = selected_user.split('@')
    
    if not confirm_action(f"Are you sure you want to drop user '{selected_user}'? This action cannot be undone."):
        console.print("[yellow]User drop cancelled.[/yellow]")
        return
    
    try:
        # Drop user
        show_progress(
            "Dropping database user...",
            _drop_user,
            username, host, verbose
        )
        
        console.print(f"[green]✓ User '{selected_user}' dropped successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to drop user:[/red] {e}")


def _create_database(db_name: str, charset: str, collation: str, verbose: bool = False) -> None:
    """Actually create the database."""
    import subprocess
    
    if verbose:
        logger.info(f"Creating database {db_name}")
    
    sql = f"CREATE DATABASE `{db_name}` CHARACTER SET {charset} COLLATE {collation};"
    
    subprocess.run([
        "sudo", "mysql", "-e", sql
    ], check=True)


def _create_user(username: str, password: str, host: str, grant_db: bool, 
                db_name: str = None, verbose: bool = False) -> None:
    """Actually create the database user."""
    import subprocess
    
    if verbose:
        logger.info(f"Creating database user {username}@{host}")
    
    # Create user
    create_sql = f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}';"
    
    subprocess.run([
        "sudo", "mysql", "-e", create_sql
    ], check=True)
    
    # Grant privileges if requested
    if grant_db and db_name:
        grant_sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{username}'@'{host}';"
        
        subprocess.run([
            "sudo", "mysql", "-e", grant_sql
        ], check=True)
    
    # Flush privileges
    subprocess.run([
        "sudo", "mysql", "-e", "FLUSH PRIVILEGES;"
    ], check=True)


def _get_databases(db_type: str) -> list:
    """Get list of databases."""
    import subprocess
    
    result = subprocess.run([
        "sudo", "mysql", "-e", "SHOW DATABASES;"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        # Skip header and system databases
        return [line.strip() for line in lines[1:] if line.strip() and not line.startswith('information_schema') and not line.startswith('performance_schema') and not line.startswith('mysql') and not line.startswith('sys')]
    
    return []


def _get_users(db_type: str) -> list:
    """Get list of database users."""
    import subprocess
    
    result = subprocess.run([
        "sudo", "mysql", "-e", "SELECT User, Host FROM mysql.user;"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        # Skip header
        users = []
        for line in lines[1:]:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    users.append((parts[0].strip(), parts[1].strip()))
        return users
    
    return []


def _drop_database(db_name: str, verbose: bool = False) -> None:
    """Actually drop the database."""
    import subprocess
    
    if verbose:
        logger.info(f"Dropping database {db_name}")
    
    sql = f"DROP DATABASE `{db_name}`;"
    
    subprocess.run([
        "sudo", "mysql", "-e", sql
    ], check=True)


def _drop_user(username: str, host: str, verbose: bool = False) -> None:
    """Actually drop the database user."""
    import subprocess
    
    if verbose:
        logger.info(f"Dropping database user {username}@{host}")
    
    sql = f"DROP USER '{username}'@'{host}';"
    
    subprocess.run([
        "sudo", "mysql", "-e", sql
    ], check=True)
    
    # Flush privileges
    subprocess.run([
        "sudo", "mysql", "-e", "FLUSH PRIVILEGES;"
    ], check=True)