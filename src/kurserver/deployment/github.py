"""
GitHub deployment module for KurServer CLI.
"""

from ..core.logger import get_logger, debug_log
from ..cli.menu import get_user_input, confirm_action, show_progress

logger = get_logger()


def github_deployment_menu(verbose: bool = False) -> None:
    """
    Handle GitHub deployment from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]GitHub Deployment[/bold blue]")
    console.print()
    
    # Create submenu options
    options = [
        MenuOption("1", "Deploy new site from GitHub", action=deploy_from_github),
        MenuOption("2", "Update existing site from GitHub", action=update_deployment),
        MenuOption("3", "Configure GitHub token", action=configure_github_token),
        MenuOption("4", "List deployments", action=list_deployments),
    ]
    
    submenu = Menu("GitHub Deployment", options, show_status=False)
    submenu.display(verbose=verbose)


def deploy_from_github(verbose: bool = False) -> None:
    """
    Deploy a new site from GitHub repository.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Deploy from GitHub[/bold blue]")
    console.print()
    
    # Get GitHub repository URL
    repo_url = get_user_input("Enter GitHub repository URL")
    
    # Validate GitHub URL
    if not _validate_github_url(repo_url):
        console.print("[red]Invalid GitHub repository URL.[/red]")
        return
    
    # Check if repository is private
    is_private = confirm_action("Is this a private repository?")
    
    # Get GitHub token if private
    github_token = None
    if is_private:
        github_token = _get_github_token()
        if not github_token:
            console.print("[red]GitHub token is required for private repositories.[/red]")
            return
    
    # Get deployment target
    domain = get_user_input("Enter domain name for deployment")
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    # Get branch to deploy
    branch = get_user_input("Enter branch name", default="main")
    
    # Check for existing deployment
    import os
    if os.path.exists(web_root):
        if not confirm_action(f"Directory {web_root} already exists. Continue?"):
            console.print("[yellow]Deployment cancelled.[/yellow]")
            return
    
    # Ask about post-deployment setup
    console.print("\n[bold]Post-Deployment Options:[/bold]")
    run_composer = confirm_action("Run composer install if composer.json exists?")
    run_npm = confirm_action("Run npm install if package.json exists?")
    create_env = confirm_action("Create .env file from template?")
    
    # Confirm deployment
    console.print("\n[bold]Deployment Summary:[/bold]")
    console.print(f"Repository: {repo_url}")
    console.print(f"Branch: {branch}")
    console.print(f"Domain: {domain}")
    console.print(f"Web Root: {web_root}")
    console.print(f"Private: {'Yes' if is_private else 'No'}")
    console.print(f"Composer: {'Yes' if run_composer else 'No'}")
    console.print(f"NPM: {'Yes' if run_npm else 'No'}")
    console.print(f"Environment file: {'Yes' if create_env else 'No'}")
    
    if not confirm_action("\nProceed with deployment?"):
        console.print("[yellow]Deployment cancelled.[/yellow]")
        return
    
    try:
        # Deploy with progress
        show_progress(
            "Deploying from GitHub...",
            _deploy_from_github,
            repo_url, branch, domain, web_root, github_token, 
            run_composer, run_npm, create_env, verbose
        )
        
        # Save deployment info
        _save_deployment_info(domain, repo_url, branch, web_root, is_private)
        
        console.print(f"[bold green]✓ Deployment completed successfully![/bold green]")
        console.print(f"[green]Site deployed to: {web_root}[/green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Deployment failed:[/bold red] {e}")
        logger.error(f"GitHub deployment failed for {repo_url}: {e}")


def update_deployment(verbose: bool = False) -> None:
    
    """
    Update an existing deployment from GitHub.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Update Deployment[/bold blue]")
    console.print()
    
    # Get existing deployments
    deployments = _get_deployments()
    
    if not deployments:
        console.print("[yellow]No existing deployments found.[/yellow]")
        return
    
    # Display deployments with numbers
    domain_choices = list(deployments.keys())
    console.print("[bold]Available Deployments:[/bold]")
    for i, domain in enumerate(domain_choices, 1):
        deployment = deployments[domain]
        console.print(f"  [{i}] {domain} - {deployment['repo_url']} ({deployment['branch']})")
    
    # Get deployment selection by number
    while True:
        try:
            choice = get_user_input(f"Select deployment to update (1-{len(domain_choices)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(domain_choices):
                domain = domain_choices[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(domain_choices)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    deployment = deployments[domain]
    
    # Ask what to update
    console.print("\n[bold]Update Options:[/bold]")
    update_options = [
        "1 - Pull latest changes from repository",
        "2 - Switch to different branch",
        "3 - Run composer install/update",
        "4 - Run npm install/build",
        "5 - Update environment file",
        "6 - Full re-deployment from scratch"
    ]
    
    # Display options
    for option in update_options:
        console.print(f"[cyan]{option}[/cyan]")
    
    # Get numerical choice
    choice_map = {
        "1": "pull",
        "2": "branch",
        "3": "composer",
        "4": "npm",
        "5": "env",
        "6": "full"
    }
    
    while True:
        choice_input = get_user_input("Select update option (1-6)", default="1")
        if choice_input in choice_map:
            update_choice = choice_map[choice_input]
            break
        else:
            console.print("[red]Invalid choice. Please enter a number between 1 and 6.[/red]")
    
    
    try:
        if update_choice == "full":
            # Full re-deployment
            show_progress(
                "Re-deploying from GitHub...",
                _full_redeploy,
                deployment, domain, verbose
            )
        elif update_choice == "branch":
            # Get branch name before showing progress
            new_branch = get_user_input("Enter new branch name")
            
            # Update with progress
            show_progress(
                f"Updating branch to {new_branch}...",
                _update_deployment_with_branch,
                deployment, domain, new_branch, verbose
            )
        else:
            # Specific update
            show_progress(
                f"Updating {update_choice}...",
                _update_deployment,
                deployment, domain, update_choice, verbose
            )
        
        console.print(f"[bold green]✓ Update completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Update failed:[/bold red] {e}")
        logger.error(f"Deployment update failed for {domain}: {e}")


def configure_github_token(verbose: bool = False) -> None:
    """
    Configure GitHub personal access token.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Configure GitHub Token[/bold blue]")
    console.print()
    
    # Check if token already exists
    existing_token = _get_stored_github_token()
    
    if existing_token:
        console.print("[yellow]GitHub token is already configured.[/yellow]")
        if not confirm_action("Do you want to update it?"):
            return
    
    # Get new token
    token = get_user_input("Enter GitHub personal access token", password=True)
    
    if not token:
        console.print("[yellow]No token provided.[/yellow]")
        return
    
    # Validate token
    if not _validate_github_token(token):
        console.print("[red]Invalid GitHub token.[/red]")
        return
    
    # Store token
    _store_github_token(token)
    
    console.print("[bold green]✓ GitHub token configured successfully![/bold green]")


def list_deployments(verbose: bool = False) -> None:
    """
    List all GitHub deployments.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]GitHub Deployments[/bold blue]")
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
        console.print(f"  Last Updated: {info.get('last_updated', 'Unknown')}")
        console.print()


def _deploy_from_github(repo_url: str, branch: str, domain: str, web_root: str, 
                        github_token: str, run_composer: bool, run_npm: bool, 
                        create_env: bool, verbose: bool = False) -> None:
    """
    Actually deploy from GitHub repository.
    
    Args:
        repo_url (str): GitHub repository URL
        branch (str): Branch name
        domain (str): Domain name
        web_root (str): Web root directory
        github_token (str): GitHub token (for private repos)
        run_composer (bool): Run composer install
        run_npm (bool): Run npm install
        create_env (bool): Create .env file
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    # Check if Git is installed, install if missing
    from ..utils.package import is_package_installed, install_package
    if not is_package_installed("git"):
        if verbose:
            logger.info("Git is not installed. Installing Git...")
        
        if not install_package("git", verbose):
            raise Exception("Failed to install Git. Please install it manually.")
    
    if verbose:
        logger.info(f"Cloning {repo_url} to {web_root}")
    
    # Create web root directory
    # DEBUG: Add logging to validate permission issue diagnosis
    logger.debug(f"[DEBUG] GitHub deployment - Attempting to create directory: {web_root}")
    logger.debug(f"[DEBUG] GitHub deployment - Current user ID: {os.getuid()}")
    logger.debug(f"[DEBUG] GitHub deployment - Current effective user ID: {os.geteuid()}")
    logger.debug(f"[DEBUG] GitHub deployment - Directory parent exists: {os.path.exists(os.path.dirname(web_root))}")
    logger.debug(f"[DEBUG] GitHub deployment - Directory exists: {os.path.exists(web_root)}")
    
    try:
        subprocess.run(["sudo", "mkdir", "-p", web_root], check=True)
        logger.debug(f"[DEBUG] GitHub deployment - Successfully created directory: {web_root}")
    except PermissionError as e:
        logger.error(f"[DEBUG] GitHub deployment - Permission error creating directory {web_root}: {e}")
        logger.error(f"[DEBUG] GitHub deployment - This confirms the diagnosis - os.makedirs() lacks sudo privileges")
        raise
    
    # Clone repository
    if github_token:
        # For private repos, use token in URL
        url_with_token = repo_url.replace('https://', f'https://{github_token}@')
        subprocess.run(["git", "clone", "-b", branch, url_with_token, web_root], check=True)
    else:
        subprocess.run(["git", "clone", "-b", branch, repo_url, web_root], check=True)
    
    # Set permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    # Run composer if requested
    if run_composer and os.path.exists(os.path.join(web_root, "composer.json")):
        if verbose:
            logger.info("Running composer install...")
        
        subprocess.run(["composer", "install", "--no-dev", "--optimize-autoloader"], 
                      cwd=web_root, check=True)
    
    # Run npm if requested
    if run_npm and os.path.exists(os.path.join(web_root, "package.json")):
        from ..managers.npm import _execute_npm_operation
        from ..core.system import get_nvm_status
        
        # Get NVM status to determine Node.js version
        nvm_status = get_nvm_status()
        node_version = nvm_status.get('current_version') or 'system'
        
        if verbose:
            logger.info("Running npm install...")
        
        # Use enhanced npm manager for install
        _execute_npm_operation(web_root, node_version, "install", verbose)
        
        # Check if build script exists and run it
        import json
        with open(os.path.join(web_root, "package.json"), 'r') as f:
            package_data = json.load(f)
        
        if "scripts" in package_data and "build" in package_data["scripts"]:
            if verbose:
                logger.info("Running npm build...")
            
            # Use enhanced npm manager for build
            _execute_npm_operation(web_root, node_version, "build", verbose)
    
    # Create .env file if requested
    if create_env:
        _create_env_file(web_root, domain, verbose)
    
    logger.info(f"Deployment from {repo_url} completed successfully")


def _update_deployment(deployment: dict, domain: str, update_type: str, verbose: bool = False) -> None:
    """
    Update specific aspects of a deployment.
    
    Args:
        deployment (dict): Deployment information
        domain (str): Domain name for the deployment
        update_type (str): Type of update to perform
        verbose (bool): Enable verbose output
    """
    # Check if deployment has required fields
    if not deployment or 'web_root' not in deployment:
        raise Exception("Invalid deployment information. Missing web root directory.")
    import subprocess
    import os
    
    # Check if Git is installed, install if missing
    from ..utils.package import is_package_installed, install_package
    if not is_package_installed("git"):
        if verbose:
            logger.info("Git is not installed. Installing Git...")
        
        if not install_package("git", verbose):
            raise Exception("Failed to install Git. Please install it manually.")
    
    web_root = deployment['web_root']
    
    if update_type == "pull":
        if verbose:
            logger.info("Pulling latest changes...")
        
        # Fix Git ownership issue by setting safe directory
        try:
            subprocess.run(["git", "config", "--global", "--add", "safe.directory", web_root], check=True)
        except subprocess.CalledProcessError:
            # Ignore if safe directory already exists or other config issues
            pass
        
        subprocess.run(["git", "pull"], cwd=web_root, check=True)
        
    elif update_type == "branch":
        # This should not be called directly anymore - use _update_deployment_with_branch instead
        raise Exception("Use _update_deployment_with_branch instead")
        
    elif update_type == "composer":
        if os.path.exists(os.path.join(web_root, "composer.json")):
            if verbose:
                logger.info("Running composer install...")
            
            subprocess.run(["composer", "install", "--no-dev", "--optimize-autoloader"], 
                          cwd=web_root, check=True)
        else:
            logger.warning("composer.json not found")
            
    elif update_type == "npm":
        if os.path.exists(os.path.join(web_root, "package.json")):
            from ..managers.npm import npm_site_menu
            
            if verbose:
                logger.info("Starting npm operations...")
            
            # Use enhanced npm site menu for comprehensive npm operations
            npm_site_menu(domain, web_root, verbose)
        else:
            logger.warning("package.json not found")
            
    elif update_type == "env":
        _create_env_file(web_root, domain, verbose)


def _update_deployment_with_branch(deployment: dict, domain: str, new_branch: str, verbose: bool = False) -> None:
    
    """
    Update deployment to switch to a different branch.
    
    Args:
        deployment (dict): Deployment information
        domain (str): Domain name for the deployment
        new_branch (str): New branch name to switch to
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    # DEBUG: Log the deployment structure to understand the issue
    debug_log(logger, "github", f"[DEBUG] Deployment structure: {deployment}")
    debug_log(logger, "github", f"[DEBUG] Deployment keys: {list(deployment.keys()) if deployment else 'None'}")
    
    # Check if deployment has required fields
    if not deployment or 'web_root' not in deployment:
        raise Exception("Invalid deployment information. Missing web root directory.")
    
    # Check if Git is installed, install if missing
    from ..utils.package import is_package_installed, install_package
    if not is_package_installed("git"):
        if verbose:
            logger.info("Git is not installed. Installing Git...")
        
        if not install_package("git", verbose):
            raise Exception("Failed to install Git. Please install it manually.")
    
    web_root = deployment['web_root']
    
    if verbose:
        logger.info(f"Switching to branch {new_branch}...")
    
    # Fix Git ownership issue by setting safe directory
    try:
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", web_root], check=True)
    except subprocess.CalledProcessError:
        # Ignore if safe directory already exists or other config issues
        pass
    
    subprocess.run(["git", "fetch"], cwd=web_root, check=True)
    subprocess.run(["git", "checkout", new_branch], cwd=web_root, check=True)
    subprocess.run(["git", "pull"], cwd=web_root, check=True)
    
    # Update deployment info
    deployment['branch'] = new_branch
    _save_deployment_info(
        domain,
        deployment['repo_url'],
        new_branch,
        web_root,
        deployment['private']
    )


def _full_redeploy(deployment: dict, domain: str, verbose: bool = False) -> None:
    """
    Perform a full re-deployment from scratch.
    
    Args:
        deployment (dict): Deployment information
        domain (str): Domain name for the deployment
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    import shutil
    
    web_root = deployment['web_root']
    
    # Backup existing deployment
    backup_path = f"{web_root}.backup"
    if os.path.exists(web_root):
        if verbose:
            logger.info(f"Backing up existing deployment to {backup_path}")
        
        shutil.move(web_root, backup_path)
    
    try:
        # Get GitHub token if private
        github_token = None
        if deployment['private']:
            github_token = _get_github_token()
            if not github_token:
                raise Exception("GitHub token required for private repository")
        
        # Deploy from scratch
        _deploy_from_github(
            deployment['repo_url'],
            deployment['branch'],
            domain,
            web_root,
            github_token,
            True,  # run_composer
            True,  # run_npm
            True,  # create_env
            verbose
        )
        
        # Remove backup if successful
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
            
    except Exception as e:
        # Restore backup if deployment failed
        if os.path.exists(backup_path):
            if verbose:
                logger.info(f"Restoring backup from {backup_path}")
            
            shutil.rmtree(web_root)
            shutil.move(backup_path, web_root)
        
        raise e


def _create_env_file(web_root: str, domain: str, verbose: bool = False) -> None:
    """
    Create .env file from template.
    
    Args:
        web_root (str): Web root directory
        domain (str): Domain name
        verbose (bool): Enable verbose output
    """
    import os
    
    env_template = os.path.join(web_root, ".env.example")
    env_file = os.path.join(web_root, ".env")
    
    if os.path.exists(env_template) and not os.path.exists(env_file):
        if verbose:
            logger.info("Creating .env file from template")
        
        # Copy template to .env
        import shutil
        shutil.copy(env_template, env_file)
        
        # Set appropriate permissions
        os.chmod(env_file, 0o640)
        
        # Add some default values
        with open(env_file, 'a') as f:
            f.write(f"\n# Added by KurServer CLI\n")
            f.write(f"APP_URL=https://{domain}\n")
            f.write(f"APP_DOMAIN={domain}\n")


def _validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    import re
    
    # Basic GitHub URL validation
    github_pattern = r'https?://(www\.)?github\.com/[\w\-\.]+/[\w\-\.]+/?$'
    return bool(re.match(github_pattern, url))


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


def _get_github_token() -> str:
    """Get GitHub token from user input or storage."""
    from ..cli.menu import get_user_input
    
    # Try to get stored token first
    stored_token = _get_stored_github_token()
    if stored_token:
        return stored_token
    
    # Ask user for token
    return get_user_input("Enter GitHub personal access token", password=True)


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


def _save_deployment_info(domain: str, repo_url: str, branch: str, 
                        web_root: str, is_private: bool) -> None:
    """Save deployment information."""
    import os
    import json
    from datetime import datetime
    
    # Create deployments directory
    deployments_dir = os.path.expanduser("~/.kurserver/deployments")
    os.makedirs(deployments_dir, exist_ok=True)
    
    # Load existing deployments
    deployments_file = os.path.join(deployments_dir, "github.json")
    deployments = {}
    
    if os.path.exists(deployments_file):
        try:
            with open(deployments_file, 'r') as f:
                deployments = json.load(f)
        except:
            pass
    
    # Update deployment info
    deployments[domain] = {
        'repo_url': repo_url,
        'branch': branch,
        'web_root': web_root,
        'private': is_private,
        'last_updated': datetime.now().isoformat()
    }
    
    # Save deployments
    with open(deployments_file, 'w') as f:
        json.dump(deployments, f, indent=2)


def _remove_deployment(domain: str) -> None:
    """Remove deployment information for a domain."""
    import os
    import json
    
    deployments_file = os.path.expanduser("~/.kurserver/deployments/github.json")
    
    # Load existing deployments
    deployments = _get_deployments()
    
    # Remove the specified domain
    if domain in deployments:
        del deployments[domain]
        
        # Save updated deployments
        os.makedirs(os.path.dirname(deployments_file), exist_ok=True)
        with open(deployments_file, 'w') as f:
            json.dump(deployments, f, indent=2)


def _get_deployments() -> dict:
    """Get all GitHub deployments."""
    import os
    import json
    
    deployments_file = os.path.expanduser("~/.kurserver/deployments/github.json")
    
    if not os.path.exists(deployments_file):
        return {}
    
    try:
        with open(deployments_file, 'r') as f:
            return json.load(f)
    except:
        return {}