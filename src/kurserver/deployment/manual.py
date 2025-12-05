"""
Manual deployment module for KurServer CLI.
"""

from ..core.logger import get_logger
from ..cli.menu import get_user_input, confirm_action, show_progress

logger = get_logger()


def manual_deployment_menu(verbose: bool = False) -> None:
    """
    Handle manual deployment from menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]Manual Deployment[/bold blue]")
    console.print()
    
    # Create submenu options
    options = [
        MenuOption("1", "Upload files manually", action=upload_files),
        MenuOption("2", "Create project structure", action=create_project_structure),
        MenuOption("3", "Set up application", action=setup_application),
    ]
    
    submenu = Menu("Manual Deployment", options, show_status=False)
    submenu.display(verbose=verbose)


def upload_files(verbose: bool = False) -> None:
    """
    Guide user through manual file upload process.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Manual File Upload[/bold blue]")
    console.print()
    console.print("This option guides you through manually uploading files to your server.")
    console.print("You can use SCP, SFTP, or FTP to transfer files to the server.")
    console.print()
    
    # Get domain
    domain = get_user_input("Enter domain name")
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    # Create directory structure
    try:
        show_progress(
            "Creating directory structure...",
            _create_directory_structure,
            web_root, verbose
        )
        
        console.print(f"[bold green]✓ Directory structure created at {web_root}[/bold green]")
        
        # Show upload instructions
        console.print("\n[bold]Upload Instructions:[/bold]")
        console.print(f"1. Upload your website files to: {web_root}")
        console.print("2. Ensure the main directory contains your index.php or index.html")
        console.print("3. Set appropriate permissions:")
        console.print(f"   sudo chown -R www-data:www-data {web_root}")
        console.print(f"   sudo chmod -R 755 {web_root}")
        
        # Show SCP/SFTP examples
        console.print("\n[bold]SCP Example:[/bold]")
        console.print(f"scp -r /path/to/your/site/* user@your-server:{web_root}/")
        
        console.print("\n[bold]SFTP Example:[/bold]")
        console.print("sftp user@your-server")
        console.print(f"cd {web_root}")
        console.print("put -r /path/to/your/site/* .")
        
        console.print("\n[bold]After uploading, you can:[/bold]")
        console.print("1. Set up database (if needed)")
        console.print("2. Configure environment file (if needed)")
        console.print("3. Test your website")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to create directory structure:[/bold red] {e}")
        logger.error(f"Manual upload setup failed for {domain}: {e}")


def create_project_structure(verbose: bool = False) -> None:
    """
    Create a standard project structure for common applications.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Create Project Structure[/bold blue]")
    console.print()
    
    # Display project types with numbers
    console.print("[bold]Available Project Types:[/bold]")
    project_types = [
        "php-basic", "wordpress", "laravel", "symfony",
        "static", "nodejs", "django", "flask", "custom"
    ]
    for i, project_type in enumerate(project_types, 1):
        console.print(f"  [{i}] {project_type.title().replace('-', ' ')}")
    
    # Get project type selection by number
    while True:
        try:
            choice = get_user_input(f"Select project type (1-{len(project_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(project_types):
                project_type = project_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(project_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    # Get domain
    domain = get_user_input("Enter domain name")
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    try:
        # Create project structure
        show_progress(
            f"Creating {project_type} project structure...",
            _create_project_structure,
            project_type, web_root, domain, verbose
        )
        
        console.print(f"[bold green]✓ {project_type} project structure created at {web_root}[/bold green]")
        
        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Upload your application files to the appropriate directories")
        console.print("2. Configure your application (database connections, etc.)")
        console.print("3. Set up web server configuration if needed")
        console.print("4. Test your application")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to create project structure:[/bold red] {e}")
        logger.error(f"Project structure creation failed for {domain}: {e}")


def setup_application(verbose: bool = False) -> None:
    """
    Set up common application configurations.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Application Setup[/bold blue]")
    console.print()
    
    # Get domain
    domain = get_user_input("Enter domain name")
    
    # Get web root
    default_root = f"/var/www/{domain}"
    web_root = get_user_input(f"Enter web root directory", default=default_root)
    
    # Check if directory exists
    import os
    if not os.path.exists(web_root):
        console.print(f"[red]Directory {web_root} does not exist.[/red]")
        return
    
    # Display application types with numbers
    console.print("[bold]Available Application Types:[/bold]")
    app_types = [
        "wordpress", "laravel", "symfony", "django",
        "flask", "nodejs", "php-generic", "custom"
    ]
    for i, app_type in enumerate(app_types, 1):
        console.print(f"  [{i}] {app_type.title()}")
    
    # Get application type selection by number
    while True:
        try:
            choice = get_user_input(f"Select application type (1-{len(app_types)})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(app_types):
                app_type = app_types[choice_num - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(app_types)}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")
    
    try:
        # Set up application
        show_progress(
            f"Setting up {app_type} application...",
            _setup_application,
            app_type, web_root, domain, verbose
        )
        
        console.print(f"[bold green]✓ {app_type} application setup completed![/bold green]")
        
        # Show setup information
        console.print("\n[bold]Setup Information:[/bold]")
        console.print(f"Web Root: {web_root}")
        console.print(f"Domain: {domain}")
        
        if app_type == "wordpress":
            console.print("\n[bold]WordPress Setup:[/bold]")
            console.print("1. Visit https://{domain}/wp-admin/ to complete WordPress installation")
            console.print("2. Create database and user if not already done")
            console.print("3. Configure wp-config.php with database details")
            
        elif app_type == "laravel":
            console.print("\n[bold]Laravel Setup:[/bold]")
            console.print("1. Run 'composer install' if not already done")
            console.print("2. Copy .env.example to .env and configure")
            console.print("3. Run 'php artisan key:generate'")
            console.print("4. Run 'php artisan migrate'")
            
        elif app_type == "symfony":
            console.print("\n[bold]Symfony Setup:[/bold]")
            console.print("1. Run 'composer install' if not already done")
            console.print("2. Configure .env file with database details")
            console.print("3. Run 'php bin/console doctrine:migrations:migrate'")
            
        elif app_type == "django":
            console.print("\n[bold]Django Setup:[/bold]")
            console.print("1. Run 'pip install -r requirements.txt'")
            console.print("2. Configure settings.py with database details")
            console.print("3. Run 'python manage.py migrate'")
            console.print("4. Run 'python manage.py collectstatic'")
            
        elif app_type == "flask":
            console.print("\n[bold]Flask Setup:[/bold]")
            console.print("1. Run 'pip install -r requirements.txt'")
            console.print("2. Configure application with database details")
            console.print("3. Set up WSGI configuration if needed")
            
        elif app_type == "nodejs":
            console.print("\n[bold]Node.js Setup:[/bold]")
            console.print("1. Run 'npm install' if not already done")
            console.print("2. Configure environment variables")
            console.print("3. Run 'npm run build' if applicable")
            console.print("4. Set up process manager (PM2) for production")
        
    except Exception as e:
        console.print(f"[bold red]✗ Application setup failed:[/bold red] {e}")
        logger.error(f"Application setup failed for {domain}: {e}")


def _create_directory_structure(web_root: str, verbose: bool = False) -> None:
    """
    Create basic directory structure for manual upload.
    
    Args:
        web_root (str): Web root directory
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Creating directory structure at {web_root}")
    
    # Create web root directory
    os.makedirs(web_root, exist_ok=True)
    
    # Create common directories
    directories = [
        "logs", "temp", "cache", "uploads", "assets"
    ]
    
    for directory in directories:
        dir_path = os.path.join(web_root, directory)
        os.makedirs(dir_path, exist_ok=True)
    
    # Set permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    # Create a placeholder index.html
    index_file = os.path.join(web_root, "index.html")
    if not os.path.exists(index_file):
        with open(index_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {os.path.basename(web_root)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
        h1 {{ color: #333; }}
        .info {{ background: #f5f5f5; padding: 20px; margin: 20px auto; width: 600px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Welcome to {os.path.basename(web_root)}</h1>
    <div class="info">
        <p>This website is managed by KurServer CLI.</p>
        <p>Upload your website files to replace this page.</p>
    </div>
</body>
</html>
""")
        
        os.chmod(index_file, 0o644)
    
    logger.info(f"Directory structure created at {web_root}")


def _create_project_structure(project_type: str, web_root: str, domain: str, verbose: bool = False) -> None:
    """
    Create project structure based on project type.
    
    Args:
        project_type (str): Type of project
        web_root (str): Web root directory
        domain (str): Domain name
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Creating {project_type} project structure at {web_root}")
    
    # Create web root directory
    os.makedirs(web_root, exist_ok=True)
    
    if project_type == "php-basic":
        # Basic PHP structure
        directories = ["includes", "config", "assets/css", "assets/js", "assets/images"]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create basic files
        with open(os.path.join(web_root, "index.php"), 'w') as f:
            f.write("""<?php
// Basic PHP application entry point
echo "Hello, World!";
?>
""")
        
        with open(os.path.join(web_root, "config/config.php"), 'w') as f:
            f.write("""<?php
// Configuration file
define('APP_NAME', 'My PHP App');
define('DB_HOST', 'localhost');
define('DB_NAME', 'database_name');
define('DB_USER', 'username');
define('DB_PASS', 'password');
?>
""")
        
    elif project_type == "wordpress":
        # WordPress structure
        directories = ["wp-content/themes", "wp-content/plugins", "wp-content/uploads"]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create wp-config.php template
        with open(os.path.join(web_root, "wp-config-sample.php"), 'w') as f:
            f.write(f"""<?php
// WordPress configuration template
define('DB_NAME', '{domain}_wp');
define('DB_USER', 'wp_user');
define('DB_PASSWORD', 'secure_password');
define('DB_HOST', 'localhost');
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', '');

$table_prefix = 'wp_';
define('WP_DEBUG', false);

if ( !defined('ABSPATH') )
    define('ABSPATH', __DIR__ . '/');

require_once(ABSPATH . 'wp-settings.php');
""")
        
    elif project_type == "laravel":
        # Laravel structure
        directories = [
            "app/Http/Controllers", "app/Models", "database/migrations", 
            "resources/views", "public", "storage/app", "storage/framework", 
            "storage/logs", "bootstrap/cache"
        ]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create .env.example
        with open(os.path.join(web_root, ".env.example"), 'w') as f:
            f.write(f"""APP_NAME={domain}
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://{domain}

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE={domain}_laravel
DB_USERNAME=root
DB_PASSWORD=

BROADCAST_DRIVER=log
CACHE_DRIVER=file
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120
""")
        
    elif project_type == "symfony":
        # Symfony structure
        directories = [
            "src/Controller", "src/Entity", "templates", 
            "config", "public", "var/cache", "var/log"
        ]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
    elif project_type == "static":
        # Static site structure
        directories = ["css", "js", "images", "fonts"]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create basic HTML template
        with open(os.path.join(web_root, "index.html"), 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>Welcome to {domain}</h1>
    </header>
    <main>
        <p>Your static website is ready!</p>
    </main>
    <script src="js/main.js"></script>
</body>
</html>
""")
        
        with open(os.path.join(web_root, "css/style.css"), 'w') as f:
            f.write("""/* Basic styles */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

main {
    max-width: 800px;
    margin: 0 auto;
}
""")
        
    elif project_type == "nodejs":
        # Node.js structure
        directories = ["src", "public", "config", "logs"]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create package.json template
        with open(os.path.join(web_root, "package.json"), 'w') as f:
            f.write(f"""{{
  "name": "{domain}",
  "version": "1.0.0",
  "description": "Node.js application",
  "main": "src/app.js",
  "scripts": {{
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest"
  }},
  "dependencies": {{
    "express": "^4.18.0"
  }},
  "devDependencies": {{
    "nodemon": "^2.0.0"
  }}
}}
""")
        
        with open(os.path.join(web_root, "src/app.js"), 'w') as f:
            f.write("""const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.static('public'));

app.get('/', (req, res) => {
    res.send('Hello, World!');
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
""")
        
    elif project_type == "django":
        # Django structure
        directories = [
            "myproject", "myapp", "static", "media", "templates"
        ]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create requirements.txt
        with open(os.path.join(web_root, "requirements.txt"), 'w') as f:
            f.write("""Django>=4.0.0
psycopg2-binary>=2.9.0
python-decouple>=3.6
""")
        
    elif project_type == "flask":
        # Flask structure
        directories = [
            "app", "static/css", "static/js", "templates", "instance"
        ]
        for directory in directories:
            os.makedirs(os.path.join(web_root, directory), exist_ok=True)
        
        # Create requirements.txt
        with open(os.path.join(web_root, "requirements.txt"), 'w') as f:
            f.write("""Flask>=2.0.0
Flask-SQLAlchemy>=2.0.0
python-dotenv>=0.19.0
""")
    
    # Set permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    logger.info(f"{project_type} project structure created at {web_root}")


def _setup_application(app_type: str, web_root: str, domain: str, verbose: bool = False) -> None:
    """
    Set up application-specific configurations.
    
    Args:
        app_type (str): Type of application
        web_root (str): Web root directory
        domain (str): Domain name
        verbose (bool): Enable verbose output
    """
    import subprocess
    import os
    
    if verbose:
        logger.info(f"Setting up {app_type} application at {web_root}")
    
    if app_type == "wordpress":
        # WordPress setup
        wp_config = os.path.join(web_root, "wp-config.php")
        wp_config_sample = os.path.join(web_root, "wp-config-sample.php")
        
        if os.path.exists(wp_config_sample) and not os.path.exists(wp_config):
            # Generate secure keys
            import secrets
            import string
            
            def generate_key(length=64):
                chars = string.ascii_letters + string.digits
                return ''.join(secrets.choice(chars) for _ in range(length))
            
            # Copy and configure wp-config.php
            with open(wp_config_sample, 'r') as f:
                config_content = f.read()
            
            # Replace placeholder values
            config_content = config_content.replace(
                "'database_name_here'", 
                f"'{domain}_wp'"
            ).replace(
                "'username_here'", 
                "'wp_user'"
            ).replace(
                "'password_here'", 
                "'secure_password_change_me'"
            )
            
            # Generate and replace keys
            config_content = config_content.replace(
                "'put your unique phrase here'",
                generate_key()
            )
            
            with open(wp_config, 'w') as f:
                f.write(config_content)
            
            # Set permissions
            os.chmod(wp_config, 0o640)
            
    elif app_type == "laravel":
        # Laravel setup
        env_file = os.path.join(web_root, ".env")
        env_example = os.path.join(web_root, ".env.example")
        
        if os.path.exists(env_example) and not os.path.exists(env_file):
            # Copy .env.example to .env
            subprocess.run(["cp", env_example, env_file], check=True)
            
            # Generate app key
            subprocess.run(["php", "artisan", "key:generate"], cwd=web_root, check=True)
            
    elif app_type == "symfony":
        # Symfony setup
        env_file = os.path.join(web_root, ".env.local")
        
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(f"""APP_ENV=prod
APP_SECRET={os.urandom(32).hex()}
DATABASE_URL="mysql://root:password@127.0.0.1:3306/{domain}_symfony?serverVersion=8.0"
""")
            
    elif app_type == "django":
        # Django setup
        settings_file = os.path.join(web_root, "myproject", "settings.py")
        
        if os.path.exists(settings_file):
            # Update settings with production values
            with open(settings_file, 'r') as f:
                settings_content = f.read()
            
            # Replace secret key
            import secrets
            new_secret_key = secrets.token_urlsafe(50)
            settings_content = settings_content.replace(
                "SECRET_KEY = 'your-secret-key-here'",
                f"SECRET_KEY = '{new_secret_key}'"
            )
            
            # Update database settings
            settings_content = settings_content.replace(
                "'NAME': 'your_db_name'",
                f"'NAME': '{domain}_django'"
            ).replace(
                "'USER': 'your_db_user'",
                "'USER': 'django_user'"
            ).replace(
                "'PASSWORD': 'your_db_password'",
                "'PASSWORD': 'secure_password_change_me'"
            )
            
            with open(settings_file, 'w') as f:
                f.write(settings_content)
    
    elif app_type == "flask":
        # Flask setup
        env_file = os.path.join(web_root, ".env")
        
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(f"""FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY={os.urandom(32).hex()}
DATABASE_URL=sqlite:///app.db
""")
    
    elif app_type == "nodejs":
        # Node.js setup
        env_file = os.path.join(web_root, ".env")
        
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(f"""NODE_ENV=production
PORT=3000
APP_NAME={domain}
""")
    
    # Set appropriate permissions
    subprocess.run(["sudo", "chown", "-R", "www-data:www-data", web_root], check=True)
    subprocess.run(["sudo", "chmod", "-R", "755", web_root], check=True)
    
    logger.info(f"{app_type} application setup completed at {web_root}")