"""
NVM (Node Version Manager) installer module for KurServer CLI.
"""

import os
import subprocess
from ..core.logger import get_logger, debug_log
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import get_system_info, get_disk_space, is_package_installed
from ..core.exceptions import SystemRequirementError

logger = get_logger()


def install_nvm_menu(verbose: bool = False) -> None:
    """
    Handle NVM installation from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]NVM (Node Version Manager) Installation[/bold blue]")
    console.print("This will install NVM and Node.js on your Ubuntu system.")
    console.print("NVM allows you to install and manage multiple Node.js versions.")
    console.print()
    
    # System preparation checks
    if not _check_system_requirements(verbose):
        console.print("[red]System requirements not met. Cannot proceed with installation.[/red]")
        return
    
    # Check if already installed
    if _is_nvm_installed():
        if not confirm_action("NVM is already installed. Do you want to reinstall?"):
            return
    
    # Get installation preferences
    console.print("[bold]Installation Options:[/bold]")
    
    # Ask about default Node.js version
    install_default_node = confirm_action("Install default LTS Node.js version after NVM installation?", default=True)
    
    # Ask about shell configuration
    configure_shell = confirm_action("Automatically configure shell profiles?", default=True)
    
    # Ask for confirmation
    if not confirm_action("Do you want to proceed with NVM installation?"):
        console.print("[yellow]Installation cancelled.[/yellow]")
        return
    
    try:
        # Perform installation with progress
        show_progress(
            "Installing NVM...",
            _install_nvm,
            verbose, install_default_node, configure_shell
        )
        
        console.print("[bold green]✓ NVM installation completed successfully![/bold green]")
        
        # Test installation
        if _test_nvm_installation(verbose):
            console.print("[bold green]✓ NVM installation validated successfully![/bold green]")
        else:
            console.print("[yellow]⚠ NVM installed but validation failed. Please check logs.[/yellow]")
        
        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Log out and log back in to load NVM")
        console.print("2. Or run: source ~/.bashrc (or ~/.zshrc)")
        console.print("3. Use 'nvm list-remote' to see available Node.js versions")
        console.print("4. Use 'nvm install <version>' to install specific versions")
        console.print("5. Use 'nvm use <version>' to switch between versions")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"NVM installation failed: {e}")


def _check_system_requirements(verbose: bool = False) -> bool:
    """
    Check if system meets requirements for NVM installation.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if requirements are met, False otherwise
    """
    from ..cli.menu import console
    
    if verbose:
        console.print("[bold]Checking system requirements...[/bold]")
    
    try:
        # Check Ubuntu version
        system_info = get_system_info()
        if system_info.get('distro') != 'ubuntu':
            console.print("[red]Ubuntu Linux is required.[/red]")
            return False
        
        # Check disk space (minimum 500MB free)
        disk_space = get_disk_space('/')
        if disk_space['available'] < 500 * 1024 * 1024:  # 500MB in bytes
            console.print("[red]Insufficient disk space. At least 500MB free space required.[/red]")
            return False
        
        # Check memory (minimum 256MB)
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        if mem_kb < 256 * 1024:  # 256MB in KB
                            console.print("[red]Insufficient memory. At least 256MB RAM required.[/red]")
                            return False
                        break
        except FileNotFoundError:
            console.print("[yellow]Could not check memory requirements.[/yellow]")
        
        # Check for curl or wget
        has_curl = is_package_installed('curl')
        has_wget = is_package_installed('wget')
        
        if not has_curl and not has_wget:
            console.print("[red]Either curl or wget is required for NVM installation.[/red]")
            return False
        
        if verbose:
            console.print("[green]✓ System requirements check passed[/green]")
        
        return True
        
    except Exception as e:
        logger.error(f"System requirements check failed: {e}")
        console.print(f"[red]Error checking system requirements: {e}[/red]")
        return False


def _is_nvm_installed() -> bool:
    """
    Check if NVM is already installed.
    
    Returns:
        bool: True if NVM is installed, False otherwise
    """
    try:
        # Check if NVM directory exists
        nvm_dir = os.path.expanduser("~/.nvm")
        if not os.path.exists(nvm_dir):
            return False
        
        # Check if NVM command is available
        result = subprocess.run(
            ["bash", "-c", "command -v nvm"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True
        
        # Check shell configuration files for NVM
        shell_files = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc"),
            os.path.expanduser("~/.profile"),
            os.path.expanduser("~/.bash_profile")
        ]
        
        for shell_file in shell_files:
            if os.path.exists(shell_file):
                with open(shell_file, 'r') as f:
                    content = f.read()
                    if 'NVM_DIR' in content or 'nvm.sh' in content:
                        return True
        
        return False
        
    except Exception:
        return False


def _install_nvm(verbose: bool = False, install_default_node: bool = True, configure_shell: bool = True) -> None:
    """
    Actually install NVM with configuration options.
    
    Args:
        verbose (bool): Enable verbose output
        install_default_node (bool): Install default Node.js version
        configure_shell (bool): Configure shell profiles
    """
    # Install required dependencies
    debug_log(logger, "nvm", "Installing required dependencies...")
    
    # Update package lists
    subprocess.run(["sudo", "apt", "update"], check=True)
    
    # Install curl if not present
    if not is_package_installed('curl'):
        subprocess.run(["sudo", "apt", "install", "-y", "curl"], check=True)
    
    # Install build-essential for Node.js compilation
    subprocess.run(["sudo", "apt", "install", "-y", "build-essential"], check=True)
    
    # Download and install NVM
    debug_log(logger, "nvm", "Downloading and installing NVM...")
    
    nvm_install_script = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh"
    
    # Use curl to download and execute installation script
    result = subprocess.run([
        "curl", "-o-", nvm_install_script
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to download NVM installation script: {result.stderr}")
    
    # Execute installation script
    install_result = subprocess.run([
        "bash", "-s", "--"
    ], input=result.stdout, capture_output=True, text=True)
    
    if install_result.returncode != 0:
        raise Exception(f"NVM installation failed: {install_result.stderr}")
    
    # Configure shell profiles
    if configure_shell:
        debug_log(logger, "nvm", "Configuring shell profiles...")
        _update_shell_profiles(verbose)
    
    # Install default Node.js version
    if install_default_node:
        debug_log(logger, "nvm", "Installing default Node.js LTS version...")
        _install_default_node_version(verbose)
    
    logger.info("NVM installation completed successfully")


def _update_shell_profiles(verbose: bool = False) -> None:
    """
    Update shell configuration files to load NVM.
    
    Args:
        verbose (bool): Enable verbose output
    """
    nvm_config = """
# NVM configuration added by KurServer CLI
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
"""
    
    shell_files = [
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/.profile"),
        os.path.expanduser("~/.bash_profile")
    ]
    
    for shell_file in shell_files:
        try:
            # Check if file exists
            if not os.path.exists(shell_file):
                # Create file if it doesn't exist
                with open(shell_file, 'w') as f:
                    f.write(nvm_config)
            else:
                # Check if NVM is already configured
                with open(shell_file, 'r') as f:
                    content = f.read()
                
                if 'NVM_DIR' not in content and 'nvm.sh' not in content:
                    # Append NVM configuration
                    with open(shell_file, 'a') as f:
                        f.write(nvm_config)
        
        except Exception as e:
            logger.warning(f"Failed to update shell profile {shell_file}: {e}")


def _install_default_node_version(verbose: bool = False) -> None:
    """
    Install default LTS Node.js version.
    
    Args:
        verbose (bool): Enable verbose output
    """
    try:
        # Load NVM in current shell and install LTS
        install_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install --lts
        nvm use --lts
        nvm alias default node
        """
        
        result = subprocess.run([
            "bash", "-c", install_cmd
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"Failed to install default Node.js version: {result.stderr}")
        else:
            logger.info("Default Node.js LTS version installed successfully")
            
    except Exception as e:
        logger.warning(f"Failed to install default Node.js version: {e}")


def _test_nvm_installation(verbose: bool = False) -> bool:
    """
    Test NVM installation and configuration.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if tests pass, False otherwise
    """
    try:
        # Test NVM command availability
        debug_log(logger, "nvm", "Testing NVM command availability...")
        
        test_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm --version
        """
        
        result = subprocess.run([
            "bash", "-c", test_cmd
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"NVM command test failed: {result.stderr}")
            return False
        
        # Test Node.js installation if requested
        debug_log(logger, "nvm", "Testing Node.js installation...")
        
        node_test_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        node --version
        """
        
        node_result = subprocess.run([
            "bash", "-c", node_test_cmd
        ], capture_output=True, text=True)
        
        if node_result.returncode != 0:
            logger.warning("Node.js test failed, but NVM is installed")
            # Don't fail the test, as Node.js might not be installed yet
        else:
            debug_log(logger, "nvm", f"Node.js version: {node_result.stdout.strip()}")
        
        # Test npm installation
        debug_log(logger, "nvm", "Testing npm installation...")
        
        npm_test_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        npm --version
        """
        
        npm_result = subprocess.run([
            "bash", "-c", npm_test_cmd
        ], capture_output=True, text=True)
        
        if npm_result.returncode != 0:
            logger.warning("npm test failed, but NVM is installed")
        else:
            debug_log(logger, "nvm", f"npm version: {npm_result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        logger.error(f"NVM installation test failed: {e}")
        return False


def get_nvm_info(verbose: bool = False) -> dict:
    """
    Get comprehensive NVM information.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Dictionary with NVM information
    """
    from ..cli.menu import console
    
    info = {
        'installed': _is_nvm_installed(),
        'version': None,
        'node_version': None,
        'npm_version': None,
        'installed_versions': [],
        'current_version': None,
        'default_version': None
    }
    
    if not info['installed']:
        return info
    
    try:
        # Get NVM version
        nvm_version_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm --version
        """
        
        result = subprocess.run([
            "bash", "-c", nvm_version_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            info['version'] = result.stdout.strip()
        
        # Get current Node.js version
        node_version_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        node --version 2>/dev/null || echo "Not installed"
        """
        
        result = subprocess.run([
            "bash", "-c", node_version_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "Not installed" not in result.stdout:
            info['node_version'] = result.stdout.strip()
        
        # Get npm version
        npm_version_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        npm --version 2>/dev/null || echo "Not installed"
        """
        
        result = subprocess.run([
            "bash", "-c", npm_version_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "Not installed" not in result.stdout:
            info['npm_version'] = result.stdout.strip()
        
        # Get installed Node.js versions
        list_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm list 2>/dev/null || echo "No versions installed"
        """
        
        result = subprocess.run([
            "bash", "-c", list_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "No versions installed" not in result.stdout:
            # Parse the output to get version list
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip().startswith('v') or line.strip().startswith('->'):
                    version = line.strip().replace('->', '').replace('*', '').strip()
                    if version.startswith('v'):
                        version = version[1:]  # Remove 'v' prefix
                    info['installed_versions'].append(version)
                    
                    # Check if this is the current version
                    if '->' in line or '*' in line:
                        info['current_version'] = version
        
        # Get default version
        default_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm alias default 2>/dev/null || echo "No default set"
        """
        
        result = subprocess.run([
            "bash", "-c", default_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "No default set" not in result.stdout:
            default_line = result.stdout.strip()
            if 'default' in default_line:
                parts = default_line.split()
                if len(parts) >= 2:
                    info['default_version'] = parts[1].replace('v', '')
        
        if verbose:
            console.print("[bold]NVM Information:[/bold]")
            console.print(f"  Installed: {'Yes' if info['installed'] else 'No'}")
            console.print(f"  NVM Version: {info['version'] or 'Unknown'}")
            console.print(f"  Current Node.js: {info['node_version'] or 'Not installed'}")
            console.print(f"  npm Version: {info['npm_version'] or 'Not installed'}")
            console.print(f"  Default Version: {info['default_version'] or 'Not set'}")
            
            if info['installed_versions']:
                console.print("  Installed Versions:")
                for version in info['installed_versions']:
                    current = " (current)" if version == info['current_version'] else ""
                    default = " (default)" if version == info['default_version'] else ""
                    console.print(f"    • v{version}{current}{default}")
            else:
                console.print("  Installed Versions: None")
    
    except Exception as e:
        logger.error(f"Error getting NVM info: {e}")
    
    return info