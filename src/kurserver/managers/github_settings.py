"""
GitHub settings management module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress, Menu, MenuOption, console

logger = get_logger()


def github_settings_menu(verbose: bool = False) -> None:
    """
    Handle GitHub settings from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    console.print("[bold blue]GitHub Settings[/bold blue]")
    console.print()
    
    # Create submenu options
    options = [
        MenuOption("1", "Configure GitHub access token", action=configure_github_token),
        MenuOption("2", "List all deployments", action=list_all_deployments),
        MenuOption("3", "Remove deployment configuration", action=remove_deployment_config),
        MenuOption("4", "Test GitHub connection", action=test_github_connection),
    ]
    
    submenu = Menu("GitHub Settings", options, show_status=False)
    submenu.display(verbose=verbose)


def configure_github_token(verbose: bool = False) -> None:
    """
    Configure GitHub personal access token.
    
    Args:
        verbose (bool): Enable verbose output
    """
    console.print("[bold blue]Configure GitHub Token[/bold blue]")
    console.print()
    
    # Check if token already exists
    existing_token = _get_stored_github_token()
    
    if existing_token:
        console.print("[yellow]GitHub token already configured.[/yellow]")
        if not confirm_action("Do you want to update it?"):
            return
    
    # Get new token
    token = get_user_input("Enter GitHub personal access token", password=True)
    
    if not token:
        console.print("[yellow]Token not provided.[/yellow]")
        return
    
    # Validate token
    if not _validate_github_token(token):
        console.print("[red]Invalid GitHub token.[/red]")
        return
    
    # Store token
    _store_github_token(token)
    
    console.print("[bold green]✓ GitHub token configured successfully![/bold green]")


def list_all_deployments(verbose: bool = False) -> None:
    """
    List all GitHub deployments.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..deployment.github import _get_deployments
    
    console.print("[bold blue]All GitHub Deployments[/bold blue]")
    console.print()
    
    deployments = _get_deployments()
    
    if not deployments:
        console.print("[yellow]No deployments found.[/yellow]")
        return
    
    for domain, info in deployments.items():
        console.print(f"[bold]{domain}[/bold]")
        console.print(f"  Repository: {info['repo_url']}")
        console.print(f"  Branch: {info['branch']}")
        console.print(f"  Web Root: {info['web_root']}")
        console.print(f"  Private: {'Yes' if info['private'] else 'No'}")
        console.print(f"  Last Update: {info.get('last_updated', 'Unknown')}")
        console.print()


def remove_deployment_config(verbose: bool = False) -> None:
    """
    Remove deployment configuration for a specific site.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..deployment.github import _get_deployments, _remove_deployment
    
    console.print("[bold blue]Remove Deployment Configuration[/bold blue]")
    console.print()
    
    # Get existing deployments
    deployments = _get_deployments()
    
    if not deployments:
        console.print("[yellow]No deployments found.[/yellow]")
        return
    
    # Select deployment to remove
    domain_choices = list(deployments.keys())
    domain = get_user_input(
        "Select deployment to remove",
        choices=domain_choices
    )
    
    deployment = deployments[domain]
    
    # Show deployment info
    console.print(f"\n[bold]Deployment to Remove:[/bold]")
    console.print(f"Domain: {domain}")
    console.print(f"Repository: {deployment['repo_url']}")
    console.print(f"Branch: {deployment['branch']}")
    
    if not confirm_action(f"\nRemove deployment configuration for '{domain}'?"):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return
    
    try:
        _remove_deployment(domain)
        console.print(f"[bold green]✓ Deployment configuration for '{domain}' removed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to remove deployment:[/bold red] {e}")
        logger.error(f"Failed to remove deployment for {domain}: {e}")


def test_github_connection(verbose: bool = False) -> None:
    """
    Test GitHub connection with configured token.
    
    Args:
        verbose (bool): Enable verbose output
    """
    console.print("[bold blue]Test GitHub Connection[/bold blue]")
    console.print()
    
    # Get stored token
    token = _get_stored_github_token()
    
    if not token:
        console.print("[yellow]GitHub token not configured.[/yellow]")
        console.print("Please configure a GitHub token first.")
        return
    
    console.print("Testing GitHub connection...")
    
    try:
        # Test token by making a simple API call
        import subprocess
        import json
        
        result = subprocess.run([
            "curl", "-s", "-H", f"Authorization: token {token}",
            "https://api.github.com/user"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            user_data = json.loads(result.stdout)
            if 'login' in user_data:
                console.print(f"[bold green]✓ GitHub connection successful![/bold green]")
                console.print(f"[green]Authenticated as: {user_data['login']}[/green]")
                console.print(f"[green]Name: {user_data.get('name', 'Unknown')}[/green]")
                console.print(f"[green]Email: {user_data.get('email', 'Unknown')}[/green]")
            else:
                console.print("[red]✗ GitHub authentication failed.[/red]")
        else:
            console.print("[red]✗ GitHub connection failed.[/red]")
            if verbose:
                console.print(f"Error: {result.stderr}")
                
    except Exception as e:
        console.print(f"[red]✗ Connection test failed:[/red] {e}")
        if verbose:
            logger.error(f"GitHub connection test failed: {e}")


def _get_stored_github_token() -> str:
    """Get stored GitHub token."""
    import os
    
    # Try to get token from environment variable
    token = os.environ.get('KURSERVER_GITHUB_TOKEN')
    if token:
        return token
    
    # Try to get token from config file
    config_file = os.path.expanduser("~/.kurserver/config.json")
    try:
        import json
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('github_token')
    except:
        pass
    
    return None


def _validate_github_token(token: str) -> bool:
    """Validate GitHub personal access token."""
    import subprocess
    import json
    
    try:
        # Test token by making a simple API call
        result = subprocess.run([
            "curl", "-s", "-H", f"Authorization: token {token}",
            "https://api.github.com/user"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            user_data = json.loads(result.stdout)
            return 'login' in user_data
        
        return False
    except:
        return False


def _store_github_token(token: str) -> None:
    """Store GitHub token securely."""
    import os
    import json
    
    # Create config directory
    config_dir = os.path.expanduser("~/.kurserver")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "config.json")
    
    # Load existing config
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            pass
    
    # Store token
    config['github_token'] = token
    
    # Write config
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    # Set appropriate permissions
    os.chmod(config_file, 0o600)