"""
NPM (Node Package Manager) operations module for KurServer CLI.
"""

import os
import subprocess
import json
from ..core.logger import get_logger, debug_log
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import get_nvm_status, get_npm_status

logger = get_logger()


def npm_site_menu(site_name: str, web_root: str, verbose: bool = False) -> None:
    """
    Handle NPM operations for a specific site.
    
    Args:
        site_name (str): Domain name of the site
        web_root (str): Web root directory of the site
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print(f"[bold blue]NPM Operations for {site_name}[/bold blue]")
    console.print()
    
    # Validate web root directory
    if not os.path.exists(web_root):
        console.print(f"[red]Web root directory {web_root} does not exist.[/red]")
        console.print("[yellow]Please check the site configuration and try again.[/yellow]")
        return
    
    # Check if web root is accessible
    if not os.access(web_root, os.R_OK | os.W_OK | os.X_OK):
        console.print(f"[red]Web root directory {web_root} is not accessible.[/red]")
        console.print("[yellow]Please check directory permissions.[/yellow]")
        return
    
    # Check if package.json exists
    package_json_path = os.path.join(web_root, "package.json")
    if not os.path.exists(package_json_path):
        console.print(f"[red]package.json not found in {web_root}[/red]")
        console.print("[yellow]NPM operations require a package.json file.[/yellow]")
        console.print(f"[cyan]Expected location: {package_json_path}[/cyan]")
        return
    
    # Validate package.json format
    try:
        with open(package_json_path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid package.json format:[/red] {e}")
        console.print("[yellow]Please check the JSON syntax in package.json.[/yellow]")
        return
    except Exception as e:
        console.print(f"[red]Error reading package.json:[/red] {e}")
        return
    
    # Get NVM status
    nvm_status = get_nvm_status()
    if not nvm_status['installed']:
        console.print("[red]NVM is not installed. Please install NVM first.[/red]")
        console.print("[yellow]You can install NVM from the main menu > Install Software > NVM.[/yellow]")
        return
    
    # Check if any Node.js versions are installed
    installed_versions = nvm_status.get('installed_versions', [])
    if not installed_versions:
        console.print("[red]No Node.js versions installed via NVM.[/red]")
        console.print("[yellow]Please install a Node.js version first using NVM Management.[/yellow]")
        return
    
    # Select Node.js version
    node_version = _select_node_version(nvm_status, verbose)
    if not node_version:
        console.print("[yellow]Node.js version selection cancelled.[/yellow]")
        return
    
    # Select NPM operation
    npm_operation = _select_npm_operation(package_json_path, verbose)
    if not npm_operation:
        console.print("[yellow]NPM operation cancelled.[/yellow]")
        return
    
    # Execute NPM operation
    try:
        show_progress(
            f"Running npm {npm_operation}...",
            _execute_npm_operation,
            web_root, node_version, npm_operation, verbose
        )
        
        console.print(f"[bold green]✓ NPM {npm_operation} completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ NPM operation failed:[/bold red] {e}")
        logger.error(f"NPM operation failed for {site_name}: {e}")
        
        # Provide specific error recovery suggestions
        if "Permission denied" in str(e):
            console.print("[yellow]Hint: Check file permissions and try running with sudo if needed.[/yellow]")
        elif "ENOSPC" in str(e) or "No space left" in str(e):
            console.print("[yellow]Hint: Insufficient disk space. Please free up disk space and try again.[/yellow]")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            console.print("[yellow]Hint: Network error. Please check your internet connection.[/yellow]")
        elif "npm ERR!" in str(e):
            console.print("[yellow]Hint: NPM error occurred. Check the error message above for details.[/yellow]")
        else:
            console.print("[yellow]Hint: Check the logs for more detailed error information.[/yellow]")


def _select_node_version(nvm_status: dict, verbose: bool = False) -> str:
    """
    Allow user to select a Node.js version.
    
    Args:
        nvm_status (dict): NVM status information
        verbose (bool): Enable verbose output
        
    Returns:
        str: Selected Node.js version or None if cancelled
    """
    from ..cli.menu import console
    
    installed_versions = nvm_status.get('installed_versions', [])
    
    if not installed_versions:
        console.print("[red]No Node.js versions installed via NVM.[/red]")
        console.print("[yellow]Please install a Node.js version first using NVM Management.[/yellow]")
        return None
    
    console.print("[bold]Available Node.js Versions:[/bold]")
    for i, version in enumerate(installed_versions, 1):
        current = " (current)" if version == nvm_status.get('current_version') else ""
        default = " (default)" if version == nvm_status.get('default_version') else ""
        console.print(f"  [{i}] Node.js {version}{current}{default}")
    
    console.print(f"  [{len(installed_versions) + 1}] Use system default Node.js")
    
    while True:
        try:
            choice = get_user_input(f"Select Node.js version (1-{len(installed_versions) + 1})", default="1")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(installed_versions):
                selected_version = installed_versions[choice_num - 1]
                console.print(f"[cyan]Using Node.js {selected_version}[/cyan]")
                return selected_version
            elif choice_num == len(installed_versions) + 1:
                console.print("[cyan]Using system default Node.js version[/cyan]")
                return "system"
            else:
                console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(installed_versions) + 1}.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")


def _select_npm_operation(package_json_path: str, verbose: bool = False) -> str:
    """
    Allow user to select an NPM operation.
    
    Args:
        package_json_path (str): Path to package.json file
        verbose (bool): Enable verbose output
        
    Returns:
        str: Selected NPM operation or None if cancelled
    """
    from ..cli.menu import console
    
    # Read package.json to get available scripts
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
    except Exception as e:
        logger.error(f"Failed to read package.json: {e}")
        scripts = {}
    
    console.print("\n[bold]Available NPM Operations:[/bold]")
    console.print("  [1] npm install - Install dependencies")
    
    if 'build' in scripts:
        console.print("  [2] npm run build - Build the project")
    
    if 'dev' in scripts:
        console.print("  [3] npm run dev - Run development mode")
    
    if 'start' in scripts:
        console.print("  [4] npm run start - Start the application")
    
    console.print("  [5] Custom command - Enter your own npm command")
    
    # Determine max option number based on available scripts
    max_option = 5  # Always include custom command
    available_options = [1, 5]  # Always available options
    
    if 'build' in scripts:
        available_options.append(2)
    if 'dev' in scripts:
        available_options.append(3)
    if 'start' in scripts:
        available_options.append(4)
    
    # Sort the options to determine the correct max
    available_options.sort()
    max_option = max(available_options)
    
    while True:
        try:
            choice = get_user_input(f"Select NPM operation ({', '.join(map(str, available_options))})", default="1")
            choice_num = int(choice)
            
            if choice_num == 1:
                return "install"
            elif choice_num == 2 and 'build' in scripts:
                return "build"
            elif choice_num == 3 and 'dev' in scripts:
                return "dev"
            elif choice_num == 4 and 'start' in scripts:
                return "start"
            elif choice_num == 5:
                custom_command = get_user_input("Enter custom npm command")
                if custom_command.strip():
                    return f"custom:{custom_command.strip()}"
                else:
                    console.print("[red]Custom command cannot be empty.[/red]")
            else:
                console.print(f"[red]Invalid selection. Please enter one of: {', '.join(map(str, available_options))}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")


def _execute_npm_operation(web_root: str, node_version: str, npm_operation: str, verbose: bool = False) -> None:
    """
    Execute an NPM operation with the specified Node.js version.
    
    Args:
        web_root (str): Web root directory of the site
        node_version (str): Node.js version to use
        npm_operation (str): NPM operation to execute
        verbose (bool): Enable verbose output
    """
    # Change to web root directory
    os.chdir(web_root)
    
    # Prepare npm command based on operation
    if npm_operation == "install":
        npm_cmd = "npm install"
    elif npm_operation == "build":
        npm_cmd = "npm run build"
    elif npm_operation == "dev":
        npm_cmd = "npm run dev"
    elif npm_operation == "start":
        npm_cmd = "npm run start"
    elif npm_operation.startswith("custom:"):
        custom_cmd = npm_operation[7:]  # Remove "custom:" prefix
        npm_cmd = f"npm {custom_cmd}"
    else:
        raise Exception(f"Unknown NPM operation: {npm_operation}")
    
    # Prepare NVM environment and combine with npm command
    if node_version != "system":
        full_cmd = f"""
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
        nvm use {node_version} && {npm_cmd}
        """
    else:
        full_cmd = f"""
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
        {npm_cmd}
        """
    
    if verbose:
        logger.info(f"Executing NPM operation in {web_root}")
        logger.info(f"Node.js version: {node_version}")
        logger.info(f"NPM command: {npm_cmd}")
    
    # Clean up the command and remove extra whitespace
    full_cmd = full_cmd.strip()
    
    # Execute the command
    result = subprocess.run(
        ["bash", "-c", full_cmd],
        capture_output=True,
        text=True,
        cwd=web_root
    )
    
    if result.returncode != 0:
        raise Exception(f"NPM operation failed: {result.stderr}")
    
    if verbose and result.stdout:
        logger.info(f"NPM output: {result.stdout}")


def get_npm_info(web_root: str, verbose: bool = False) -> dict:
    """
    Get NPM information for a site.
    
    Args:
        web_root (str): Web root directory of the site
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Dictionary with NPM information
    """
    from ..cli.menu import console
    
    info = {
        'package_json_exists': False,
        'node_modules_exists': False,
        'scripts': {},
        'dependencies': {},
        'dev_dependencies': {}
    }
    
    # Check if package.json exists
    package_json_path = os.path.join(web_root, "package.json")
    if os.path.exists(package_json_path):
        info['package_json_exists'] = True
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            info['scripts'] = package_data.get('scripts', {})
            info['dependencies'] = package_data.get('dependencies', {})
            info['dev_dependencies'] = package_data.get('devDependencies', {})
        except Exception as e:
            logger.error(f"Failed to read package.json: {e}")
    
    # Check if node_modules exists
    node_modules_path = os.path.join(web_root, "node_modules")
    if os.path.exists(node_modules_path):
        info['node_modules_exists'] = True
    
    if verbose:
        console.print("[bold]NPM Information:[/bold]")
        console.print(f"  package.json: {'Yes' if info['package_json_exists'] else 'No'}")
        console.print(f"  node_modules: {'Yes' if info['node_modules_exists'] else 'No'}")
        
        if info['scripts']:
            console.print("  Available scripts:")
            for script, command in info['scripts'].items():
                console.print(f"    • {script}: {command}")
        
        if info['dependencies']:
            console.print(f"  Dependencies: {len(info['dependencies'])} packages")
        
        if info['dev_dependencies']:
            console.print(f"  Dev Dependencies: {len(info['dev_dependencies'])} packages")
    
    return info