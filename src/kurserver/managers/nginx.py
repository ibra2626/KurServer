"""
Nginx site manager module for KurServer CLI.
"""

import re
from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import get_available_php_versions, reload_nginx

logger = get_logger()

# Update options constant for better maintainability
UPDATE_OPTIONS = [
    "pull - Pull latest changes from repository",
    "branch - Switch to different branch",
    "composer - Run composer install/update",
    "npm - Run npm operations with Node.js version selection",
    "env - Update environment file",
    "full - Full re-deployment from scratch"
]


def _get_update_choice() -> str:
    """
    Get user's update choice with structured selection.
    
    Returns:
        str: Selected update option
    """
    from ..cli.menu import console
    
    console.print("\n[bold]Update Options:[/bold]")
    for i, option in enumerate(UPDATE_OPTIONS, 1):
        console.print(f"  [{i}] {option}")
    
    while True:
        try:
            choice = get_user_input(f"Select update option [1-{len(UPDATE_OPTIONS)}]", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(UPDATE_OPTIONS):
                # Extract option key (e.g., "pull" from "pull - Pull latest changes from repository")
                selected_option = UPDATE_OPTIONS[choice_num - 1].split(' - ')[0]
                return selected_option
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(UPDATE_OPTIONS)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")


def _execute_update(update_choice: str, deployment: dict, domain: str, verbose: bool = False) -> None:
    """
    Execute selected update operation with proper error handling.
    
    Args:
        update_choice (str): Type of update to perform
        deployment (dict): Deployment information
        domain (str): Domain name for the site
        verbose (bool): Enable verbose output
    """
    from ..deployment.github import _update_deployment, _update_deployment_with_branch, _full_redeploy
    from ..cli.menu import console
    
    try:
        if update_choice == "full":
            # Full re-deployment
            show_progress(
                "Re-deploying from GitHub...",
                _full_redeploy,
                deployment, domain, verbose
            )
        elif update_choice == "branch":
            # Branch update - get branch name first
            new_branch = get_user_input("Enter new branch name")
            
            # Update with progress
            show_progress(
                f"Updating branch to {new_branch}...",
                _update_deployment_with_branch,
                deployment, domain, new_branch, verbose
            )
        elif update_choice == "npm":
            # Enhanced npm operations with Node.js version selection
            web_root = deployment.get('web_root', f"/var/www/{domain}")
            _handle_npm_update(domain, web_root, verbose)
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
        
        # Provide specific error recovery suggestions
        if "Permission denied" in str(e):
            console.print("[yellow]Hint: Check file permissions and try running with sudo if needed.[/yellow]")
        elif "Network" in str(e) or "connection" in str(e).lower():
            console.print("[yellow]Hint: Check your internet connection and GitHub repository accessibility.[/yellow]")
        elif "Git" in str(e):
            console.print("[yellow]Hint: Ensure Git is installed and the repository is accessible.[/yellow]")
        else:
            console.print("[yellow]Hint: Check the logs for more detailed error information.[/yellow]")


def _handle_npm_update(domain: str, web_root: str, verbose: bool = False) -> None:
    """
    Handle npm update operations with Node.js version selection.
    
    Args:
        domain (str): Domain name for the site
        web_root (str): Web root directory of the site
        verbose (bool): Enable verbose output
    """
    from ..managers.npm import npm_site_menu
    
    try:
        # Call the enhanced npm site menu
        npm_site_menu(domain, web_root, verbose)
    except Exception as e:
        logger.error(f"NPM update failed for {domain}: {e}")
        raise Exception(f"NPM update failed: {e}")


def site_management_menu(verbose: bool = False) -> None:
    """
    Handle unified site management from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]Site Management[/bold blue]")
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
        MenuOption("3", "Update existing site", action=update_existing_site),
        MenuOption("4", "Remove website", action=remove_site),
        MenuOption("5", "Enable/disable site", action=toggle_site),
        MenuOption("6", "Site information", action=site_info),
        MenuOption("7", "NPM operations", action=npm_operations_menu),
        MenuOption("8", "Manage SSL certificates", action=manage_ssl),
    ]
    
    submenu = Menu("Site Management", options, show_status=False)
    submenu.display(verbose=verbose)


# Backward compatibility alias
def manage_nginx_menu(verbose: bool = False) -> None:
    """
    Backward compatibility wrapper for site_management_menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    site_management_menu(verbose)


def add_new_site(verbose: bool = False) -> None:
    """
    Add a new website configuration with unified deployment workflow.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Add New Website[/bold blue]")
    console.print()
    
    # Get basic site information first
    domain = get_user_input("Enter domain name (e.g., example.com)")
    
    # Validate domain
    if not domain or '.' not in domain:
        console.print("[red]Invalid domain name.[/red]")
        return
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    # Ask about deployment method FIRST (this is the key change)
    console.print("\n[bold]Site Deployment Method:[/bold]")
    console.print("  [1] GitHub - Clone from GitHub repository")
    console.print("  [2] Manual - Create placeholder site")
    console.print("  [3] Empty - Create configuration only, no files")
    
    while True:
        try:
            choice = get_user_input("Select deployment method (1-3)", default="2")
            choice_num = int(choice)
            
            if choice_num == 1:
                deployment_method = "github"
                break
            elif choice_num == 2:
                deployment_method = "manual"
                break
            elif choice_num == 3:
                deployment_method = "empty"
                break
            else:
                console.print("[red]Invalid selection. Please enter a number between 1 and 3.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Handle GitHub-specific configuration
    github_url = None
    github_branch = "main"
    github_token = None
    is_private = False
    
    if deployment_method == "github":
        console.print("\n[bold]GitHub Configuration:[/bold]")
        github_url = get_user_input("Enter GitHub repository URL")
        
        # Validate GitHub URL
        from ..deployment.github import _validate_github_url
        if not _validate_github_url(github_url):
            console.print("[red]Invalid GitHub repository URL.[/red]")
            return
        
        github_branch = get_user_input("Enter branch name", default="main")
        is_private = confirm_action("Is this a private repository?")
        
        if is_private:
            from ..deployment.github import _get_github_token
            github_token = _get_github_token()
            if not github_token:
                console.print("[red]GitHub token is required for private repositories.[/red]")
                console.print("[yellow]Please configure GitHub token first via 'GitHub settings' menu.[/yellow]")
                return
    
    # Now ask about server configuration (same for all deployment methods)
    console.print("\n[bold]Server Configuration:[/bold]")
    
    # Ask about SSL
    console.print("\n[bold]SSL/HTTPS Configuration:[/bold]")
    console.print("  [1] None - No SSL certificate")
    console.print("  [2] Self-signed - Create self-signed certificate")
    console.print("  [3] Let's Encrypt - Get free SSL certificate")
    
    while True:
        try:
            choice = get_user_input("Select SSL configuration (1-3)", default="1")
            choice_num = int(choice)
            
            if choice_num == 1:
                ssl_option = "none"
                break
            elif choice_num == 2:
                ssl_option = "self-signed"
                break
            elif choice_num == 3:
                ssl_option = "letsencrypt"
                break
            else:
                console.print("[red]Invalid selection. Please enter a number between 1 and 3.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    enable_ssl = ssl_option != "none"
    use_letsencrypt = ssl_option == "letsencrypt"
    
    # Ask about application type
    console.print("\n[bold]Application Type:[/bold]")
    console.print("  [1] Static HTML/CSS/JS")
    console.print("  [2] PHP Application")
    console.print("  [3] Node.js Application")
    
    app_type = "static"
    enable_php = False
    enable_nodejs = False
    php_version = None
    nodejs_version = None
    
    while True:
        try:
            choice = get_user_input("Select application type (1-3)", default="1")
            choice_num = int(choice)
            
            if choice_num == 1:
                app_type = "static"
                break
            elif choice_num == 2:
                app_type = "php"
                enable_php = True
                break
            elif choice_num == 3:
                app_type = "nodejs"
                enable_nodejs = True
                break
            else:
                console.print("[red]Invalid selection. Please enter a number between 1 and 3.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Get PHP version if PHP is enabled
    if enable_php:
        # Get installed PHP versions dynamically
        installed_php_versions = get_available_php_versions()
        
        if not installed_php_versions:
            console.print("[red]No PHP-FPM versions installed. Please install PHP-FPM first.[/red]")
            return
        
        console.print("\n[bold]Available PHP Versions:[/bold]")
        for i, version in enumerate(installed_php_versions, 1):
            console.print(f"  [{i}] PHP {version}")
        
        while True:
            try:
                choice = get_user_input(f"Select PHP version (1-{len(installed_php_versions)})", default="1")
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(installed_php_versions):
                    php_version = installed_php_versions[choice_num - 1]
                    break
                else:
                    console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(installed_php_versions)}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Get Node.js version if Node.js is enabled
    if enable_nodejs:
        from ..core.system import get_node_status, get_nvm_status
        
        # Check if NVM is installed
        nvm_status = get_nvm_status()
        if not nvm_status['installed']:
            console.print("[red]NVM is not installed. Please install NVM first.[/red]")
            console.print("[yellow]You can install NVM from the main menu > Install Software > NVM.[/yellow]")
            return
        
        # Get installed Node.js versions
        node_status = get_node_status()
        installed_versions = node_status.get('installed_versions', [])
        
        if not installed_versions:
            console.print("[red]No Node.js versions installed. Please install a Node.js version first.[/red]")
            console.print("[yellow]You can install Node.js from the main menu > NVM Management > Install Node.js version.[/yellow]")
            return
        
        console.print("\n[bold]Available Node.js Versions:[/bold]")
        for i, version in enumerate(installed_versions, 1):
            is_default = " (default)" if version == node_status.get('default_version') else ""
            is_current = " (current)" if version == node_status.get('current_version') else ""
            console.print(f"  [{i}] Node.js {version}{is_default}{is_current}")
        
        while True:
            try:
                choice = get_user_input(f"Select Node.js version (1-{len(installed_versions)})", default="1")
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(installed_versions):
                    nodejs_version = installed_versions[choice_num - 1]
                    break
                else:
                    console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(installed_versions)}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Get email for Let's Encrypt if needed
    email = None
    if use_letsencrypt:
        email = get_user_input("Enter email address for Let's Encrypt certificate")
        
        # Validate email
        if '@' not in email or '.' not in email.split('@')[1]:
            console.print("[red]Invalid email address.[/red]")
            return
    
    # Confirm creation
    console.print("\n[bold]Site Configuration Summary:[/bold]")
    console.print(f"Domain: {domain}")
    console.print(f"Web Root: {web_root}")
    console.print(f"Deployment Method: {deployment_method}")
    
    if deployment_method == "github":
        console.print(f"GitHub URL: {github_url}")
        console.print(f"Branch: {github_branch}")
        console.print(f"Private: {'Yes' if is_private else 'No'}")
    
    console.print(f"SSL: {ssl_option}")
    
    # Display application type information
    if app_type == "static":
        console.print("Application Type: Static HTML/CSS/JS")
    elif app_type == "php":
        console.print(f"Application Type: PHP ({php_version})")
    elif app_type == "nodejs":
        console.print(f"Application Type: Node.js ({nodejs_version})")
    
    if use_letsencrypt:
        console.print(f"Email for certificate: {email}")
    
    if not confirm_action("\nCreate this website configuration?"):
        console.print("[yellow]Website creation cancelled.[/yellow]")
        return
    
    try:
        # Create site configuration
        show_progress(
            "Creating website configuration...",
            _create_site_config,
            domain, web_root, ssl_option, app_type, php_version, nodejs_version, verbose
        )
        
        # Set up SSL if requested
        if enable_ssl:
            show_progress(
                "Setting up SSL certificate...",
                _setup_ssl,
                domain, ssl_option, email if use_letsencrypt else None, verbose
            )
        
        # Deploy site if requested
        if deployment_method != "empty":
            show_progress(
                "Deploying website...",
                _deploy_site,
                domain, deployment_method, github_url if deployment_method == "github" else None,
                github_branch if deployment_method == "github" else None,
                github_token if deployment_method == "github" and is_private else None,
                app_type, nodejs_version, verbose
            )
            
            # Save deployment info for GitHub deployments
            if deployment_method == "github":
                _save_deployment_info(domain, github_url, github_branch, f"/var/www/{domain}", is_private)
        
        console.print(f"[bold green]✓ Website '{domain}' created successfully![/bold green]")
        
        if use_letsencrypt:
            console.print("[green]✓ Let's Encrypt certificate installed![/green]")
            console.print(f"[yellow]Note: SSL certificate will auto-renew. Check logs at /var/log/letsencrypt/[/yellow]")
        
        # Show next steps based on deployment method
        if deployment_method == "github":
            console.print(f"[green]✓ Site deployed from GitHub![/green]")
            console.print(f"[cyan]Use 'Site Management' > 'Update existing site' to pull updates.[/cyan]")
        elif deployment_method == "manual":
            console.print(f"[green]✓ Placeholder site created![/green]")
            console.print(f"[cyan]Upload your files to: {web_root}[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Website creation failed:[/bold red] {e}")
        logger.error(f"Website creation failed for {domain}: {e}")


def _create_site_config(domain: str, web_root: str, ssl_option: str,
                       app_type: str, php_version: str = None, nodejs_version: str = None,
                       verbose: bool = False) -> None:
    """
    Create Nginx site configuration.
    
    Args:
        domain (str): Domain name
        web_root (str): Web root directory
        ssl_option (str): SSL option ('none', 'self-signed', 'letsencrypt')
        app_type (str): Application type ('static', 'php', 'nodejs')
        php_version (str): PHP version (if PHP is enabled)
        nodejs_version (str): Node.js version (if Node.js is enabled)
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    # Create web root directory with proper sudo elevation
    if verbose:
        logger.info(f"Creating web root directory: {web_root}")
    
    # Use subprocess with sudo to ensure proper permissions for /var/www/ directory
    try:
        subprocess.run(["sudo", "mkdir", "-p", web_root], check=True)
        logger.debug(f"[DEBUG] Successfully created directory with sudo: {web_root}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[DEBUG] Failed to create directory {web_root} with sudo: {e}")
        raise Exception(f"Failed to create web root directory: {web_root}")
    
    # Set permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    # Create Nginx configuration file
    config_path = f"/etc/nginx/sites-available/{domain}"
    
    # Generate configuration content
    config_content = _generate_nginx_config(domain, web_root, ssl_option, app_type, php_version, nodejs_version)
    
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
    if not reload_nginx():
        raise Exception("Failed to reload nginx configuration")
    
    logger.info(f"Nginx configuration for {domain} created successfully")


def _generate_nginx_config(domain: str, web_root: str, ssl_option: str,
                          app_type: str, php_version: str = None, nodejs_version: str = None) -> str:
    """
    Generate Nginx configuration content.
    
    Args:
        domain (str): Domain name
        web_root (str): Web root directory
        ssl_option (str): SSL option ('none', 'self-signed', 'letsencrypt')
        app_type (str): Application type ('static', 'php', 'nodejs')
        php_version (str): PHP version (if PHP is enabled)
        nodejs_version (str): Node.js version (if Node.js is enabled)
    
    Returns:
        str: Nginx configuration content
    """
    enable_ssl = ssl_option != "none"
    
    # Set index file based on application type
    if app_type == "nodejs":
        index_files = "index.js index.html"
    else:
        index_files = "index.html index.php"
    
    config = f"""server {{
    listen 80;
    server_name {domain};
    root {web_root};
    index {index_files};
    
    access_log /var/log/nginx/{domain}.access.log;
    error_log /var/log/nginx/{domain}.error.log;
    
"""
    
    # Add location blocks based on application type
    if app_type == "static":
        config += """    location / {
        try_files $uri $uri/ =404;
    }
"""
    elif app_type == "php":
        config += """    location / {
        try_files $uri $uri/ =404;
    }
"""
        config += f"""
    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
"""
    elif app_type == "nodejs":
        config += """    # For Node.js applications, proxy to Node.js server
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Serve static files directly
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
"""
    
    # Add redirect to HTTPS if SSL is enabled
    if enable_ssl:
        config += """
    location ~ /\.well-known/acme-challenge/ {
        allow all;
        root /var/www/html;
    }
}
"""
        
        # Add HTTPS server block
        ssl_config = f"""server {{
    listen 443 ssl http2;
    server_name {domain};
    root {web_root};
    index {index_files};
    
"""
        
        # Set SSL certificate paths based on option
        if ssl_option == "letsencrypt":
            ssl_config += f"""    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
"""
        else:  # self-signed
            ssl_config += f"""    ssl_certificate /etc/ssl/certs/{domain}.crt;
    ssl_certificate_key /etc/ssl/private/{domain}.key;
"""
        
        ssl_config += """    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    access_log /var/log/nginx/{domain}.ssl.access.log;
    error_log /var/log/nginx/{domain}.ssl.error.log;
    
    location / {{
        try_files $uri $uri/ =404;
    }}
"""
        
        # Add location blocks based on application type for HTTPS
        if app_type == "static":
            ssl_config += """    location / {
        try_files $uri $uri/ =404;
    }
"""
        elif app_type == "php":
            ssl_config += """    location / {
        try_files $uri $uri/ =404;
    }
"""
            ssl_config += f"""
    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
"""
        elif app_type == "nodejs":
            ssl_config += """    # For Node.js applications, proxy to Node.js server
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Serve static files directly
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
"""
            ssl_config += f"""
    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
"""
        
        ssl_config += "}\n"
        config += ssl_config
    else:
        config += "}\n"
    
    return config


def _setup_ssl(domain: str, ssl_option: str, email: str = None, verbose: bool = False) -> None:
    """
    Set up SSL certificate for the domain.
    
    Args:
        domain (str): Domain name
        ssl_option (str): SSL option ('self-signed' or 'letsencrypt')
        email (str): Email address for Let's Encrypt (if applicable)
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if ssl_option == "self-signed":
        if verbose:
            logger.info(f"Creating self-signed certificate for {domain}")
        
        # Create SSL directory if it doesn't exist
        subprocess.run(["sudo", "mkdir", "-p", "/etc/ssl/certs", "/etc/ssl/private"], check=True)
        
        # Generate self-signed certificate
        subprocess.run([
            "sudo", "openssl", "req", "-x509", "-nodes", "-days", "365",
            "-newkey", "rsa:2048",
            "-keyout", f"/etc/ssl/private/{domain}.key",
            "-out", f"/etc/ssl/certs/{domain}.crt",
            "-subj", f"/C=US/ST=State/L=City/O=Organization/CN={domain}"
        ], check=True)
        
        # Set appropriate permissions
        subprocess.run(["sudo", "chmod", "600", f"/etc/ssl/private/{domain}.key"], check=True)
        subprocess.run(["sudo", "chmod", "644", f"/etc/ssl/certs/{domain}.crt"], check=True)
        
        logger.info(f"Self-signed certificate created for {domain}")
        
    elif ssl_option == "letsencrypt":
        if verbose:
            logger.info(f"Setting up Let's Encrypt certificate for {domain}")
        
        # Install certbot if not already installed
        try:
            subprocess.run(["which", "certbot"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            if verbose:
                logger.info("Installing certbot...")
            
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "certbot", "python3-certbot-nginx"], check=True)
        
        # Set up webroot for Let's Encrypt challenge
        webroot_challenge = "/var/www/html"
        os.makedirs(webroot_challenge, exist_ok=True)
        
        # Obtain certificate
        cmd = [
            "sudo", "certbot", "certonly",
            "--webroot", "-w", webroot_challenge,
            "--non-interactive", "--agree-tos",
            "--email", email,
            "-d", domain
        ]
        
        if verbose:
            logger.info(f"Running: {' '.join(cmd)}")
        
        subprocess.run(cmd, check=True)
        
        # Set up auto-renewal
        cron_job = f"0 12 * * * /usr/bin/certbot renew --quiet"
        subprocess.run([
            "sudo", "bash", "-c", f"echo '{cron_job}' | crontab -"
        ], check=True)
        
        logger.info(f"Let's Encrypt certificate obtained for {domain}")


def _deploy_site(domain: str, method: str, github_url: str = None,
                github_branch: str = None, github_token: str = None,
                app_type: str = "static", nodejs_version: str = None, verbose: bool = False) -> None:
    """
    Deploy website files.
    
    Args:
        domain (str): Domain name
        method (str): Deployment method
        github_url (str): GitHub URL (if method is github)
        github_branch (str): GitHub branch (if method is github)
        github_token (str): GitHub token (if private repo)
        app_type (str): Application type ('static', 'php', 'nodejs')
        nodejs_version (str): Node.js version (if Node.js is enabled)
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    import shutil
    
    # Check if Git is installed, install if missing
    from ..utils.package import is_package_installed, install_package
    if not is_package_installed("git"):
        if verbose:
            logger.info("Git is not installed. Installing Git...")
        
        if not install_package("git", verbose):
            raise Exception("Failed to install Git. Please install it manually.")
    
    web_root = f"/var/www/{domain}"
    
    if method == "github":
        if verbose:
            logger.info(f"Cloning repository from {github_url}")
            logger.info(f"[DEBUG] Web root path: {web_root}")
            logger.info(f"[DEBUG] Web root exists before clone: {os.path.exists(web_root)}")
            
            # Check if directory exists and what's in it
            if os.path.exists(web_root):
                logger.info(f"[DEBUG] Directory contents: {os.listdir(web_root)}")
                logger.info(f"[DEBUG] Is directory empty: {not os.listdir(web_root)}")
        
        # Check if web_root already exists and is not empty
        if os.path.exists(web_root) and os.listdir(web_root):
            logger.warning(f"[DEBUG] Web root {web_root} exists and is not empty")
            if verbose:
                logger.info(f"Web root directory {web_root} already exists and is not empty.")
                logger.info("Removing existing directory before cloning...")
            
            # Remove the existing directory
            try:
                shutil.rmtree(web_root)
                logger.info(f"[DEBUG] Successfully removed existing directory: {web_root}")
            except Exception as e:
                logger.error(f"[DEBUG] Failed to remove directory {web_root}: {e}")
                raise Exception(f"Failed to remove existing web root directory: {e}")
        
        # Clone the repository
        if github_token:
            # For private repos, use token in URL
            url_with_token = github_url.replace('https://', f'https://{github_token}@')
            subprocess.run(["git", "clone", "-b", github_branch or "main", url_with_token, web_root], check=True)
        else:
            subprocess.run(["git", "clone", "-b", github_branch or "main", github_url, web_root], check=True)
    
    elif method == "manual":
        if verbose:
            logger.info("Creating placeholder files")
        
        if app_type == "nodejs":
            # Create a placeholder Node.js application
            with open(os.path.join(web_root, "package.json"), 'w') as f:
                f.write(f"""{{
  "name": "{domain.replace('.', '-')}-app",
  "version": "1.0.0",
  "description": "Node.js application for {domain}",
  "main": "app.js",
  "scripts": {{
    "start": "node app.js",
    "dev": "node app.js"
  }},
  "dependencies": {{
    "express": "^4.18.0"
  }}
}}
""")
            
            with open(os.path.join(web_root, "app.js"), 'w') as f:
                f.write(f"""const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {{
  res.send(`
    <!DOCTYPE html>
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
        <p>This Node.js application is managed by KurServer CLI.</p>
        <p>Running on Node.js {nodejs_version}</p>
    </body>
    </html>
  `);
}});

app.listen(port, () => {{
  console.log(`Server running at http://localhost:${port}`);
}});
""")
            
            # Create a simple README
            with open(os.path.join(web_root, "README.md"), 'w') as f:
                f.write(f"""# {domain}

This is a Node.js application deployed by KurServer CLI.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the application:
   ```bash
   npm start
   ```

## Node.js Version

This application is configured to use Node.js {nodejs_version}.

## Deployment

This application is configured to run on port 3000 and is proxied through Nginx.
""")
        else:
            # Create a placeholder index.html file for static/PHP sites
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


def list_sites_with_numbers(verbose: bool = False) -> list:
    """
    List all configured Nginx sites with numbers for selection.
    
    Returns:
        list: List of site names
    """
    from ..cli.menu import console
    import subprocess
    
    console.print("[bold blue]Available Nginx Sites[/bold blue]")
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
                for i, site in enumerate(sites, 1):
                    console.print(f"  [{i}] {site}")
                return sites
            else:
                console.print("No sites configured.")
                return []
        else:
            console.print("[red]Failed to list sites.[/red]")
            return []
            
    except Exception as e:
        console.print(f"[red]Error listing sites:[/red] {e}")
        return []


def remove_site(verbose: bool = False) -> None:
    """Remove a configured Nginx site."""
    from ..cli.menu import console
    import subprocess
    import os
    import shutil
    
    console.print("[bold blue]Remove Website[/bold blue]")
    console.print()
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available to remove.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number to remove (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Check if web root exists
    web_root = f"/var/www/{site}"
    web_root_exists = os.path.exists(web_root)
    
    # Show additional warning if web root exists
    if web_root_exists:
        console.print(f"[yellow]Warning: Web root directory {web_root} will be permanently deleted.[/yellow]")
    
    if not confirm_action(f"Are you sure you want to remove '{site}'? This action cannot be undone."):
        console.print("[yellow]Site removal cancelled.[/yellow]")
        return
    
    try:
        # Disable site
        subprocess.run(["sudo", "rm", "-f", f"/etc/nginx/sites-enabled/{site}"], check=True)
        
        # Remove configuration
        subprocess.run(["sudo", "rm", "-f", f"/etc/nginx/sites-available/{site}"], check=True)
        
        # Remove web root directory if it exists
        if web_root_exists:
            if verbose:
                logger.info(f"Removing web root directory: {web_root}")
            
            try:
                shutil.rmtree(web_root)
                logger.info(f"Web root directory {web_root} removed successfully")
            except Exception as e:
                logger.error(f"Failed to remove web root directory {web_root}: {e}")
                # Continue with site removal even if web root deletion fails
                console.print(f"[yellow]Warning: Failed to remove web root directory {web_root}: {e}[/yellow]")
        
        # Reload nginx
        if not reload_nginx():
            raise Exception("Failed to reload nginx configuration")
        
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
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available to toggle.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number to toggle (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
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
        if not reload_nginx():
            raise Exception("Failed to reload nginx configuration")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to {action} site:[/red] {e}")


def site_info(verbose: bool = False) -> None:
    """Show detailed information about a specific site."""
    from ..cli.menu import console
    import subprocess
    import os
    import re
    
    console.print("[bold blue]Site Information[/bold blue]")
    console.print()
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available to inspect.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number to inspect (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Check if site exists
    config_file = f"/etc/nginx/sites-available/{site}"
    if not os.path.exists(config_file):
        console.print(f"[red]Site '{site}' not found.[/red]")
        return
    
    try:
        # Read configuration file
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Extract information from config
        server_name = re.search(r'server_name\\s+([^;]+);', config_content)
        root = re.search(r'root\\s+([^;]+);', config_content)
        listen_ports = re.findall(r'listen\\s+([^;]+);', config_content)
        ssl_cert = re.search(r'ssl_certificate\\s+([^;]+);', config_content)
        php_version = re.search(r'fastcgi_pass\\s+unix:/var/run/php/php([^-]+)-fpm\\.sock', config_content)
        
        # Display site information
        console.print(f"[bold]Domain:[/bold] {server_name.group(1).strip() if server_name else 'N/A'}")
        console.print(f"[bold]Web Root:[/bold] {root.group(1).strip() if root else 'N/A'}")
        console.print(f"[bold]Listen Ports:[/bold] {', '.join(listen_ports) if listen_ports else 'N/A'}")
        
        # SSL status
        if ssl_cert:
            cert_path = ssl_cert.group(1).strip()
            if 'letsencrypt' in cert_path:
                console.print(f"[bold]SSL:[/bold] Let's Encrypt")
                # Check certificate expiry
                try:
                    result = subprocess.run([
                        "sudo", "openssl", "x509", "-in", cert_path, "-noout", "-dates"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'notAfter=' in line:
                                expiry_date = line.split('=')[1]
                                console.print(f"[bold]Certificate Expires:[/bold] {expiry_date}")
                                break
                except:
                    console.print("[bold]Certificate Status:[/bold] Unable to check expiry")
            else:
                console.print(f"[bold]SSL:[/bold] Self-signed")
        else:
            console.print("[bold]SSL:[/bold] Not configured")
        
        # PHP status
        if php_version:
            php_ver = php_version.group(1).strip()
            console.print(f"[bold]PHP:[/bold] {php_ver}")
            
            # Check if PHP-FPM is running
            try:
                result = subprocess.run([
                    "systemctl", "is-active", f"php{php_ver}-fpm"
                ], capture_output=True, text=True)
                
                status = result.stdout.strip()
                if status == "active":
                    console.print(f"[bold]PHP-FPM Status:[/bold] [green]Running[/green]")
                else:
                    console.print(f"[bold]PHP-FPM Status:[/bold] [red]Not running[/red]")
            except:
                console.print(f"[bold]PHP-FPM Status:[/bold] [yellow]Unknown[/yellow]")
        else:
            console.print("[bold]PHP:[/bold] Not configured")
        
        # Node.js status
        if nodejs_proxy:
            console.print("[bold]Node.js:[/bold] Enabled (proxied to port 3000)")
            
            # Try to detect Node.js version from package.json if it exists
            web_root = root.group(1).strip() if root else f"/var/www/{site}"
            package_json_path = os.path.join(web_root, "package.json")
            
            if os.path.exists(package_json_path):
                try:
                    with open(package_json_path, 'r') as f:
                        import json
                        package_data = json.load(f)
                        node_engine = package_data.get('engines', {}).get('node')
                        if node_engine:
                            console.print(f"[bold]Node.js Version (engines):[/bold] {node_engine}")
                except:
                    console.print("[bold]Node.js Version:[/bold] Unable to detect from package.json")
        else:
            console.print("[bold]Node.js:[/bold] Not configured")
        
        # Check if site is enabled
        is_enabled = os.path.exists(f"/etc/nginx/sites-enabled/{site}")
        console.print(f"[bold]Status:[/bold] {'[green]Enabled[/green]' if is_enabled else '[red]Disabled[/red]'}")
        
        # Disk usage
        if root:
            web_root = root.group(1).strip()
            if os.path.exists(web_root):
                try:
                    result = subprocess.run([
                        "du", "-sh", web_root
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        usage = result.stdout.split('\t')[0]
                        console.print(f"[bold]Disk Usage:[/bold] {usage}")
                except:
                    console.print("[bold]Disk Usage:[/bold] Unable to calculate")
        
        # Access logs summary (last 5 lines)
        access_log = f"/var/log/nginx/{site}.access.log"
        if os.path.exists(access_log):
            console.print("\n[bold]Recent Access Logs (last 5 entries):[/bold]")
            try:
                result = subprocess.run([
                    "tail", "-5", access_log
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            # Extract IP, date, and request
                            parts = line.split(' ')
                            if len(parts) >= 7:
                                ip = parts[0]
                                date = parts[3].lstrip('[')
                                request = ' '.join(parts[5:7])
                                console.print(f"  {ip} - {date} - {request}")
            except:
                console.print("  Unable to read access logs")
        
    except Exception as e:
        console.print(f"[red]Error getting site information:[/red] {e}")


def manage_ssl(verbose: bool = False) -> None:
    """Manage SSL certificates for sites."""
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]SSL Certificate Management[/bold blue]")
    console.print()
    
    # Create SSL management options
    options = [
        MenuOption("1", "List SSL certificates", action=list_ssl_certs),
        MenuOption("2", "Renew Let's Encrypt certificate", action=renew_ssl_cert),
        MenuOption("3", "Install new certificate", action=install_ssl_cert),
    ]
    
    submenu = Menu("SSL Certificate Management", options, show_status=False)
    submenu.display(verbose=verbose)


def list_ssl_certs(verbose: bool = False) -> None:
    """List all SSL certificates."""
    from ..cli.menu import console
    import subprocess
    import os
    
    console.print("[bold blue]SSL Certificates[/bold blue]")
    console.print()
    
    # List Let's Encrypt certificates
    if os.path.exists("/etc/letsencrypt/live"):
        console.print("[bold]Let's Encrypt Certificates:[/bold]")
        try:
            result = subprocess.run([
                "sudo", "find", "/etc/letsencrypt/live", "-maxdepth", "1", "-type", "l", "-exec", "basename", "{}", ";"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                domains = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                for domain in domains:
                    if domain.strip():
                        cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                        if os.path.exists(cert_path):
                            # Check expiry
                            try:
                                cert_result = subprocess.run([
                                    "sudo", "openssl", "x509", "-in", cert_path, "-noout", "-dates"
                                ], capture_output=True, text=True)
                                
                                if cert_result.returncode == 0:
                                    for line in cert_result.stdout.split('\n'):
                                        if 'notAfter=' in line:
                                            expiry_date = line.split('=')[1]
                                            console.print(f"  • {domain} - Expires: {expiry_date}")
                                            break
                            except:
                                console.print(f"  • {domain} - [red]Unable to check expiry[/red]")
        except Exception as e:
            console.print(f"[red]Error listing Let's Encrypt certificates:[/red] {e}")
    
    # List self-signed certificates
    console.print("\n[bold]Self-Signed Certificates:[/bold]")
    try:
        result = subprocess.run([
            "sudo", "find", "/etc/ssl/certs", "-name", "*.crt", "-exec", "basename", "{}", ";"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            certs = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            for cert in certs:
                if cert.strip() and cert != "ca-certificates.crt":
                    console.print(f"  • {cert}")
    except Exception as e:
        console.print(f"[red]Error listing self-signed certificates:[/red] {e}")


def renew_ssl_cert(verbose: bool = False) -> None:
    """Renew a Let's Encrypt certificate."""
    from ..cli.menu import console
    import subprocess
    import os
    
    console.print("[bold blue]Renew SSL Certificate[/bold blue]")
    console.print()
    
    # Get available Let's Encrypt certificates
    if not os.path.exists("/etc/letsencrypt/live"):
        console.print("[yellow]No Let's Encrypt certificates found.[/yellow]")
        return
    
    try:
        result = subprocess.run([
            "sudo", "find", "/etc/letsencrypt/live", "-maxdepth", "1", "-type", "l", "-exec", "basename", "{}", ";"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            domains = [d for d in result.stdout.strip().split('\n') if d.strip()]
            
            if not domains:
                console.print("[yellow]No Let's Encrypt certificates found.[/yellow]")
                return
            
            console.print("\n[bold]Available Domains for Certificate Renewal:[/bold]")
            for i, domain in enumerate(domains, 1):
                console.print(f"  [{i}] {domain}")
            
            while True:
                try:
                    choice = get_user_input(f"Select domain to renew certificate for (1-{len(domains)})", default="1")
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(domains):
                        domain = domains[choice_num - 1]
                        break
                    else:
                        console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(domains)}.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a valid number.[/red]")
            
            if not confirm_action(f"Renew SSL certificate for {domain}?"):
                console.print("[yellow]Certificate renewal cancelled.[/yellow]")
                return
            
            try:
                # Renew certificate
                subprocess.run([
                    "sudo", "certbot", "renew", "--cert-name", domain
                ], check=True)
                
                # Reload nginx
                if not reload_nginx():
                    raise Exception("Failed to reload nginx configuration")
                
                console.print(f"[green]✓ SSL certificate for {domain} renewed successfully![/green]")
                
            except Exception as e:
                console.print(f"[red]✗ Failed to renew certificate:[/red] {e}")
                
    except Exception as e:
        console.print(f"[red]Error getting certificate list:[/red] {e}")


def install_ssl_cert(verbose: bool = False) -> None:
    """Install a new SSL certificate for a site."""
    from ..cli.menu import console
    import subprocess
    import os
    
    console.print("[bold blue]Install SSL Certificate[/bold blue]")
    console.print()
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available for SSL installation.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number for SSL installation (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                domain = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Check if site exists
    if not os.path.exists(f"/etc/nginx/sites-available/{domain}"):
        console.print(f"[red]Site '{domain}' not found.[/red]")
        return
    
    # Get certificate type
    console.print("\n[bold]Certificate Type:[/bold]")
    console.print("  [1] Let's Encrypt - Obtain a free SSL certificate")
    console.print("  [2] Custom - Use your own certificate files")
    
    while True:
        try:
            choice = get_user_input("Select certificate type (1-2)", default="1")
            choice_num = int(choice)
            
            if choice_num == 1:
                cert_type = "letsencrypt"
                break
            elif choice_num == 2:
                cert_type = "custom"
                break
            else:
                console.print("[red]Invalid selection. Please enter a number between 1 and 2.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    if cert_type == "letsencrypt":
        # Get email
        email = get_user_input("Enter email address for Let's Encrypt certificate")
        
        if not confirm_action(f"Install Let's Encrypt certificate for {domain}?"):
            console.print("[yellow]Certificate installation cancelled.[/yellow]")
            return
        
        try:
            # Set up webroot for Let's Encrypt challenge
            webroot_challenge = "/var/www/html"
            os.makedirs(webroot_challenge, exist_ok=True)
            
            # Obtain certificate
            subprocess.run([
                "sudo", "certbot", "certonly",
                "--webroot", "-w", webroot_challenge,
                "--non-interactive", "--agree-tos",
                "--email", email,
                "-d", domain
            ], check=True)
            
            # Update Nginx configuration to use Let's Encrypt
            _update_ssl_config(domain, "letsencrypt")
            
            # Reload nginx
            if not reload_nginx():
                raise Exception("Failed to reload nginx configuration")
            
            console.print(f"[green]✓ Let's Encrypt certificate for {domain} installed![/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to install certificate:[/red] {e}")
    
    else:  # custom
        # Get certificate paths
        cert_path = get_user_input("Enter certificate file path")
        key_path = get_user_input("Enter private key file path")
        
        if not confirm_action(f"Install custom certificate for {domain}?"):
            console.print("[yellow]Certificate installation cancelled.[/yellow]")
            return
        
        try:
            # Copy certificates to standard locations
            subprocess.run(["sudo", "cp", cert_path, f"/etc/ssl/certs/{domain}.crt"], check=True)
            subprocess.run(["sudo", "cp", key_path, f"/etc/ssl/private/{domain}.key"], check=True)
            
            # Set permissions
            subprocess.run(["sudo", "chmod", "644", f"/etc/ssl/certs/{domain}.crt"], check=True)
            subprocess.run(["sudo", "chmod", "600", f"/etc/ssl/private/{domain}.key"], check=True)
            
            # Update Nginx configuration to use custom certificate
            _update_ssl_config(domain, "custom")
            
            # Reload nginx
            if not reload_nginx():
                raise Exception("Failed to reload nginx configuration")
            
            console.print(f"[green]✓ Custom certificate for {domain} installed![/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to install certificate:[/red] {e}")


def _update_ssl_config(domain: str, cert_type: str) -> None:
    """Update Nginx configuration to use SSL certificate using Jinja2 template."""
    import subprocess
    import os
    from jinja2 import Environment, FileSystemLoader
    
    config_file = f"/etc/nginx/sites-available/{domain}"
    
    # Read current configuration to extract existing settings
    with open(config_file, 'r') as f:
        config_content = f.read()
    
    # Extract configuration parameters from existing config
    server_name_match = re.search(r'server_name\s+([^;]+);', config_content)
    root_match = re.search(r'root\s+([^;]+);', config_content)
    index_match = re.search(r'index\s+([^;]+);', config_content)
    php_version_match = re.search(r'fastcgi_pass\s+unix:/var/run/php/php([^-]+)-fpm\\.sock', config_content)
    
    # Extract domain names (handle multiple domains)
    server_names = [name.strip() for name in server_name_match.group(1).strip().split()] if server_name_match else [domain]
    main_domain = server_names[0] if server_names else domain
    www_domain = any('www.' in name for name in server_names[1:]) if len(server_names) > 1 else False
    
    # Extract other parameters
    document_root = root_match.group(1).strip() if root_match else f"/var/www/{domain}"
    index_files = index_match.group(1).strip() if index_match else "index.html index.php"
    php_version = php_version_match.group(1).strip() if php_version_match else None
    
    # Determine application type
    enable_php = php_version is not None
    enable_nodejs = 'proxy_pass http://localhost:3000' in config_content
    
    # Set fallback based on application type
    if enable_php:
        fallback = '/index.php?$query_string'
    elif enable_nodejs:
        fallback = '/index.html'
    else:
        fallback = '=404'
    
    # Set SSL certificate paths based on certificate type
    if cert_type == "letsencrypt":
        ssl_cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        ssl_key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
    else:  # custom
        ssl_cert_path = f"/etc/ssl/certs/{domain}.crt"
        ssl_key_path = f"/etc/ssl/private/{domain}.key"
    
    # Prepare template context
    template_context = {
        'domain': main_domain,
        'www_domain': www_domain,
        'document_root': document_root,
        'index_files': index_files,
        'enable_ssl': True,
        'enable_php': enable_php,
        'enable_nodejs': enable_nodejs,
        'php_version': php_version,
        'ssl_certificate_path': ssl_cert_path,
        'ssl_certificate_key_path': ssl_key_path,
        'fallback': fallback
    }
    
    # Load and render template
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('nginx/site-ssl.conf.j2')
    
    # Render new configuration
    new_config_content = template.render(**template_context)
    
    # Write updated configuration to temporary file
    with open(f"/tmp/{domain}.conf", 'w') as f:
        f.write(new_config_content)
    
    # Replace original configuration
    subprocess.run(["sudo", "mv", f"/tmp/{domain}.conf", config_file], check=True)
    
    # Test configuration
    subprocess.run(["sudo", "nginx", "-t"], check=True)


def _save_deployment_info(domain: str, repo_url: str, branch: str,
                        web_root: str, is_private: bool) -> None:
    """Save deployment information."""
    from ..deployment.github import _save_deployment_info as github_save_deployment_info
    github_save_deployment_info(domain, repo_url, branch, web_root, is_private)


def _get_deployment_info(domain: str) -> dict:
    """Get deployment information for a domain."""
    from ..deployment.github import _get_deployments
    deployments = _get_deployments()
    return deployments.get(domain, {})


def update_existing_site(verbose: bool = False) -> None:
    """
    Update existing site with unified interface for all deployment types.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    from ..deployment.github import _get_deployments, _update_deployment, _full_redeploy
    
    console.print("[bold blue]Update Existing Site[/bold blue]")
    console.print()
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available to update.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number to update (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Check if site has GitHub deployment info
    deployments = _get_deployments()
    deployment = deployments.get(site, {})
    
    if not deployment:
        # No GitHub info, prompt to set it up
        console.print(f"[yellow]No GitHub deployment information found for '{site}'.[/yellow]")
        if not confirm_action("Would you like to set up GitHub deployment for this site?"):
            console.print("[yellow]Deployment update cancelled.[/yellow]")
            return
        
        # Get GitHub information
        github_url = get_user_input("Enter GitHub repository URL")
        
        # Validate GitHub URL
        from ..deployment.github import _validate_github_url
        if not _validate_github_url(github_url):
            console.print("[red]Invalid GitHub repository URL.[/red]")
            return
        
        github_branch = get_user_input("Enter branch name", default="main")
        is_private = confirm_action("Is this a private repository?")
        
        github_token = None
        if is_private:
            from ..deployment.github import _get_github_token
            github_token = _get_github_token()
            if not github_token:
                console.print("[red]GitHub token is required for private repositories.[/red]")
                return
        
        # Create deployment info
        deployment = {
            'domain': site,
            'repo_url': github_url,
            'branch': github_branch,
            'web_root': f"/var/www/{site}",
            'private': is_private
        }
        
        # Save deployment info
        _save_deployment_info(site, github_url, github_branch, f"/var/www/{site}", is_private)
        
        console.print(f"[green]✓ GitHub deployment information saved for '{site}'[/green]")
    
    # Get update choice using structured selection
    update_choice = _get_update_choice()
    
    # Execute update with professional error handling
    _execute_update(update_choice, deployment, site, verbose)


# Backward compatibility alias
def npm_operations_menu(verbose: bool = False) -> None:
    """
    Handle NPM operations for sites from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]NPM Operations[/bold blue]")
    console.print()
    
    # List available sites with numbers
    sites = list_sites_with_numbers(verbose)
    
    if not sites:
        console.print("[yellow]No sites available for NPM operations.[/yellow]")
        return
    
    console.print()
    
    # Get site selection by number
    while True:
        try:
            choice = get_user_input(f"Enter site number for NPM operations (1-{len(sites)})")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sites):
                site = sites[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(sites)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Get web root for the selected site
    web_root = f"/var/www/{site}"
    
    # Call the npm site menu
    from ..managers.npm import npm_site_menu
    npm_site_menu(site, web_root, verbose)


def update_deployment(verbose: bool = False) -> None:
    """
    Backward compatibility wrapper for update_existing_site.
    
    Args:
        verbose (bool): Enable verbose output
    """
    update_existing_site(verbose)