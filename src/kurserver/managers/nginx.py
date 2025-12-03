"""
Nginx site manager module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

logger = get_logger()


def manage_nginx_menu(verbose: bool = False) -> None:
    """
    Handle Nginx site management from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]Nginx Site Management[/bold blue]")
    console.print()
    
    # Check if Nginx is installed
    from ..core.system import is_package_installed
    if not is_package_installed('nginx'):
        console.print("[red]Nginx is not installed. Please install Nginx first.[/red]")
        return
    
    # Create submenu options
    options = [
        MenuOption("1", "Add new website", action=add_new_site),
        MenuOption("2", "List existing sites", action=list_sites),
        MenuOption("3", "Remove website", action=remove_site),
        MenuOption("4", "Enable/disable site", action=toggle_site),
    ]
    
    submenu = Menu("Nginx Site Management", options, show_status=False)
    submenu.display(verbose=verbose)


def add_new_site(verbose: bool = False) -> None:
    """
    Add a new website configuration.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Add New Website[/bold blue]")
    console.print()
    
    # Get site information
    domain = get_user_input("Enter domain name (e.g., example.com)")
    
    # Validate domain
    if not domain or '.' not in domain:
        console.print("[red]Invalid domain name.[/red]")
        return
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    # Ask about SSL
    enable_ssl = confirm_action("Enable SSL/HTTPS?")
    
    # Ask about PHP
    enable_php = confirm_action("Enable PHP processing?")
    
    # Get PHP version if PHP is enabled
    php_version = None
    if enable_php:
        php_version = get_user_input(
            "Select PHP version",
            choices=["7.4", "8.0", "8.1", "8.2"],
            default="8.1"
        )
    
    # Ask about deployment method
    console.print("\n[bold]Deployment Options:[/bold]")
    deployment_method = get_user_input(
        "How would you like to deploy the site?",
        choices=["github", "manual", "skip"],
        default="manual"
    )
    
    # Handle deployment
    if deployment_method == "github":
        github_url = get_user_input("Enter GitHub repository URL")
        is_private = confirm_action("Is this a private repository?")
        
        if is_private:
            github_token = get_user_input("Enter GitHub access token", password=True)
        else:
            github_token = None
    
    # Confirm creation
    console.print("\n[bold]Site Configuration Summary:[/bold]")
    console.print(f"Domain: {domain}")
    console.print(f"Web Root: {web_root}")
    console.print(f"SSL: {'Enabled' if enable_ssl else 'Disabled'}")
    console.print(f"PHP: {'Enabled (' + php_version + ')' if enable_php else 'Disabled'}")
    console.print(f"Deployment: {deployment_method}")
    
    if deployment_method == "github":
        console.print(f"GitHub URL: {github_url}")
        console.print(f"Private: {'Yes' if is_private else 'No'}")
    
    if not confirm_action("\nCreate this website configuration?"):
        console.print("[yellow]Website creation cancelled.[/yellow]")
        return
    
    try:
        # Create site configuration
        show_progress(
            "Creating website configuration...",
            _create_site_config,
            domain, web_root, enable_ssl, enable_php, php_version, verbose
        )
        
        # Deploy site if requested
        if deployment_method != "skip":
            show_progress(
                "Deploying website...",
                _deploy_site,
                domain, deployment_method, github_url if deployment_method == "github" else None,
                github_token if deployment_method == "github" and is_private else None,
                verbose
            )
        
        console.print(f"[bold green]✓ Website '{domain}' created successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Website creation failed:[/bold red] {e}")
        logger.error(f"Website creation failed for {domain}: {e}")


def _create_site_config(domain: str, web_root: str, enable_ssl: bool, 
                       enable_php: bool, php_version: str, verbose: bool = False) -> None:
    """
    Create Nginx site configuration.
    
    Args:
        domain (str): Domain name
        web_root (str): Web root directory
        enable_ssl (bool): Enable SSL
        enable_php (bool): Enable PHP
        php_version (str): PHP version
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    # Create web root directory
    if verbose:
        logger.info(f"Creating web root directory: {web_root}")
    
    os.makedirs(web_root, exist_ok=True)
    
    # Set permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    # Create Nginx configuration file
    config_path = f"/etc/nginx/sites-available/{domain}"
    
    # Generate configuration content
    config_content = _generate_nginx_config(domain, web_root, enable_ssl, enable_php, php_version)
    
    # Write configuration file
    with open(f"/tmp/{domain}.conf", 'w') as f:
        f.write(config_content)
    
    # Move to nginx sites-available
    subprocess.run(["sudo", "mv", f"/tmp/{domain}.conf", config_path], check=True)
    
    # Enable site
    subprocess.run(["sudo", "ln", "-sf", config_path, f"/etc/nginx/sites-enabled/{domain}"], check=True)
    
    # Test nginx configuration
    subprocess.run(["sudo", "nginx", "-t"], check=True)
    
    # Reload nginx
    subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
    
    logger.info(f"Nginx configuration for {domain} created successfully")


def _generate_nginx_config(domain: str, web_root: str, enable_ssl: bool, 
                          enable_php: bool, php_version: str) -> str:
    """
    Generate Nginx configuration content.
    
    Args:
        domain (str): Domain name
        web_root (str): Web root directory
        enable_ssl (bool): Enable SSL
        enable_php (bool): Enable PHP
        php_version (str): PHP version
    
    Returns:
        str: Nginx configuration content
    """
    config = f"""server {{
    listen 80;
    server_name {domain};
    root {web_root};
    index index.html index.php;
    
    access_log /var/log/nginx/{domain}.access.log;
    error_log /var/log/nginx/{domain}.error.log;
    
    location / {{
        try_files $uri $uri/ =404;
    }}
"""
    
    if enable_php:
        config += f"""
    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
"""
    
    config += "}\n"
    
    if enable_ssl:
        ssl_config = f"""server {{
    listen 443 ssl http2;
    server_name {domain};
    root {web_root};
    index index.html index.php;
    
    ssl_certificate /etc/ssl/certs/{domain}.crt;
    ssl_certificate_key /etc/ssl/private/{domain}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    access_log /var/log/nginx/{domain}.ssl.access.log;
    error_log /var/log/nginx/{domain}.ssl.error.log;
    
    location / {{
        try_files $uri $uri/ =404;
    }}
"""
        
        if enable_php:
            ssl_config += f"""
    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
"""
        
        ssl_config += "}\n"
        config += ssl_config
    
    return config


def _deploy_site(domain: str, method: str, github_url: str = None, 
                github_token: str = None, verbose: bool = False) -> None:
    """
    Deploy website files.
    
    Args:
        domain (str): Domain name
        method (str): Deployment method
        github_url (str): GitHub URL (if method is github)
        github_token (str): GitHub token (if private repo)
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    web_root = f"/var/www/{domain}"
    
    if method == "github":
        if verbose:
            logger.info(f"Cloning repository from {github_url}")
        
        # Clone the repository
        if github_token:
            # For private repos, use token in URL
            url_with_token = github_url.replace('https://', f'https://{github_token}@')
            subprocess.run(["git", "clone", url_with_token, web_root], check=True)
        else:
            subprocess.run(["git", "clone", github_url, web_root], check=True)
    
    elif method == "manual":
        if verbose:
            logger.info("Creating placeholder index file")
        
        # Create a placeholder index.html file
        with open(os.path.join(web_root, "index.html"), 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {domain}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Welcome to {domain}</h1>
    <p>This website is managed by KurServer CLI.</p>
</body>
</html>
""")
    
    logger.info(f"Website {domain} deployed successfully")


def list_sites(verbose: bool = False) -> None:
    """List all configured Nginx sites."""
    from ..cli.menu import console
    import subprocess
    
    console.print("[bold blue]Configured Nginx Sites[/bold blue]")
    console.print()
    
    try:
        # Get enabled sites
        result = subprocess.run(
            ["ls", "/etc/nginx/sites-enabled/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            sites = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if sites:
                for site in sites:
                    console.print(f"  • {site}")
            else:
                console.print("No sites configured.")
        else:
            console.print("[red]Failed to list sites.[/red]")
            
    except Exception as e:
        console.print(f"[red]Error listing sites:[/red] {e}")


def remove_site(verbose: bool = False) -> None:
    """Remove a configured Nginx site."""
    from ..cli.menu import console
    import subprocess
    
    console.print("[bold blue]Remove Website[/bold blue]")
    console.print()
    
    # Get site to remove
    site = get_user_input("Enter domain name to remove")
    
    if not confirm_action(f"Are you sure you want to remove '{site}'? This action cannot be undone."):
        console.print("[yellow]Site removal cancelled.[/yellow]")
        return
    
    try:
        # Disable site
        subprocess.run(["sudo", "rm", "-f", f"/etc/nginx/sites-enabled/{site}"], check=True)
        
        # Remove configuration
        subprocess.run(["sudo", "rm", "-f", f"/etc/nginx/sites-available/{site}"], check=True)
        
        # Reload nginx
        subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
        
        console.print(f"[green]✓ Site '{site}' removed successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to remove site:[/red] {e}")


def toggle_site(verbose: bool = False) -> None:
    """Enable or disable a configured Nginx site."""
    from ..cli.menu import console
    import subprocess
    import os
    
    console.print("[bold blue]Enable/Disable Website[/bold blue]")
    console.print()
    
    # Get site to toggle
    site = get_user_input("Enter domain name")
    
    # Check if site exists
    if not os.path.exists(f"/etc/nginx/sites-available/{site}"):
        console.print(f"[red]Site '{site}' not found.[/red]")
        return
    
    # Check if site is enabled
    is_enabled = os.path.exists(f"/etc/nginx/sites-enabled/{site}")
    
    # Ask what to do
    action = "disable" if is_enabled else "enable"
    
    if not confirm_action(f"Site is currently {'enabled' if is_enabled else 'disabled'}. Do you want to {action} it?"):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return
    
    try:
        if is_enabled:
            # Disable site
            subprocess.run(["sudo", "rm", "-f", f"/etc/nginx/sites-enabled/{site}"], check=True)
            console.print(f"[green]✓ Site '{site}' disabled![/green]")
        else:
            # Enable site
            subprocess.run(["sudo", "ln", "-sf", f"/etc/nginx/sites-available/{site}", f"/etc/nginx/sites-enabled/{site}"], check=True)
            console.print(f"[green]✓ Site '{site}' enabled![/green]")
        
        # Reload nginx
        subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
        
    except Exception as e:
        console.print(f"[red]✗ Failed to {action} site:[/red] {e}")