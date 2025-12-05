"""
NVM (Node Version Manager) management module for KurServer CLI.
"""

import subprocess
import os
from ..core.logger import get_logger, debug_log
from ..cli.menu import get_user_input, confirm_action, show_progress
from ..core.system import get_nvm_status

logger = get_logger()


def nvm_management_menu(verbose: bool = False) -> None:
    """
    Handle NVM management from the menu.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console, Menu, MenuOption
    
    console.print("[bold blue]NVM (Node Version Manager) Management[/bold blue]")
    console.print()
    
    # Check if NVM is installed
    nvm_status = get_nvm_status()
    if not nvm_status['installed']:
        console.print("[red]NVM is not installed. Please install NVM first.[/red]")
        return
    
    # Create submenu options
    options = [
        MenuOption("1", "List installed Node.js versions", action=list_installed_versions),
        MenuOption("2", "Install Node.js version", action=install_node_version),
        MenuOption("3", "Switch Node.js version", action=switch_node_version),
        MenuOption("4", "Set default Node.js version", action=set_default_version),
        MenuOption("5", "Uninstall Node.js version", action=uninstall_node_version),
        MenuOption("6", "NVM status and information", action=show_nvm_status),
    ]
    
    submenu = Menu("NVM Management", options, show_status=False)
    submenu.display(verbose=verbose)


def list_available_versions(verbose: bool = False) -> None:
    """
    List available Node.js versions for installation.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Available Node.js Versions (16+ only)[/bold blue]")
    console.print()
    
    try:
        versions = _fetch_available_versions(verbose)
        
        if not versions:
            console.print("[red]No available Node.js versions found.[/red]")
            return
            
        # Display versions
        console.print("[bold]Latest Node.js Versions:[/bold]")
        for i, version in enumerate(versions[:10], 1):
            console.print(f"  {i}. {version}")
        
        if len(versions) > 10:
            console.print(f"\n[dim]... and {len(versions) - 10} more versions[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to fetch available versions:[/bold red] {e}")
        logger.error(f"Failed to fetch available Node.js versions: {e}")


def list_installed_versions(verbose: bool = False) -> None:
    """
    List installed Node.js versions.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Installed Node.js Versions[/bold blue]")
    console.print()
    
    try:
        # Add debug logging
        debug_log(logger, "nvm", "Starting list_installed_versions function")
        
        # Get latest data
        nvm_status = get_nvm_status()
        debug_log(logger, "nvm", f"NVM status retrieved: {nvm_status}")
        
        if not nvm_status['installed']:
            console.print("[red]NVM is not installed.[/red]")
            debug_log(logger, "nvm", "NVM not installed - exiting function")
            return
        
        if not nvm_status['installed_versions']:
            console.print("[yellow]No Node.js versions installed.[/yellow]")
            debug_log(logger, "nvm", "No installed versions found - exiting function")
            return
        
        console.print("[bold]Installed Versions:[/bold]")
        for version in nvm_status['installed_versions']:
            current = " (current)" if version == nvm_status['current_version'] else ""
            console.print(f"  • v{version}{current}")
            debug_log(logger, "nvm", f"Displayed version: v{version}{current}")
        
        if nvm_status['current_version']:
            # Remove duplicate 'v' prefix if present
            current_version = nvm_status['current_version']
            if current_version.startswith('vv'):
                current_version = current_version[1:]  # Remove one 'v'
            console.print(f"\n[cyan]Currently using: {current_version}[/cyan]")
            debug_log(logger, "nvm", f"Current version displayed: {current_version}")
        
        debug_log(logger, "nvm", "list_installed_versions function completed successfully")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to list installed versions:[/bold red] {e}")
        logger.error(f"Failed to list installed Node.js versions: {e}")
        debug_log(logger, "nvm", f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        debug_log(logger, "nvm", f"Traceback: {traceback.format_exc()}")


def install_node_version(verbose: bool = False) -> None:
    """
    Install a specific Node.js version.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Install Node.js Version[/bold blue]")
    console.print()
    
    try:
        # Simply ask for version directly without fetching remote versions
        console.print("[yellow]Enter the Node.js version you want to install (e.g., 18.17.0, 20.5.0):[/yellow]")
        selected_version = get_user_input("Node.js version: ").strip()
        
        # Basic validation of version format
        if not selected_version or not selected_version.replace('.', '').isdigit():
            console.print("[red]Invalid version format. Please use format like 18.17.0[/red]")
            return
        
        # Confirm installation
        if not confirm_action(f"Install Node.js v{selected_version}?"):
            console.print("[yellow]Installation cancelled.[/yellow]")
            return
        
        # Install version
        show_progress(
            f"Installing Node.js v{selected_version}...",
            _install_node_version,
            selected_version, verbose
        )
        
        console.print(f"[bold green]✓ Node.js v{selected_version} installed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"Node.js version installation failed: {e}")


def switch_node_version(verbose: bool = False) -> None:
    """
    Switch to a different Node.js version.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Switch Node.js Version[/bold blue]")
    console.print()
    
    try:
        nvm_status = get_nvm_status()
        
        if not nvm_status['installed']:
            console.print("[red]NVM is not installed.[/red]")
            return
        
        if not nvm_status['installed_versions']:
            console.print("[red]No Node.js versions installed. Please install a version first.[/red]")
            return
        
        console.print("[bold]Installed Versions:[/bold]")
        for i, version in enumerate(nvm_status['installed_versions'], 1):
            current = " (current)" if version == nvm_status['current_version'] else ""
            console.print(f"  [{i}] v{version}{current}")
        
        # Get user selection
        while True:
            try:
                choice = get_user_input(
                    f"Select version to switch to (1-{len(nvm_status['installed_versions'])})"
                )
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(nvm_status['installed_versions']):
                    selected_version = nvm_status['installed_versions'][choice_num - 1]
                    break
                else:
                    console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(nvm_status['installed_versions'])}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number.[/red]")
        
        # Confirm switch
        if not confirm_action(f"Switch to Node.js v{selected_version}?"):
            console.print("[yellow]Switch cancelled.[/yellow]")
            return
        
        # Switch version
        show_progress(
            f"Switching to Node.js v{selected_version}...",
            _switch_node_version,
            selected_version, verbose
        )
        
        console.print(f"[bold green]✓ Switched to Node.js v{selected_version}![/bold green]")
        console.print("[yellow]Note: You may need to restart your shell or run 'source ~/.bashrc' for changes to take effect.[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Version switch failed:[/bold red] {e}")
        logger.error(f"Node.js version switch failed: {e}")


def set_default_version(verbose: bool = False) -> None:
    """
    Set default Node.js version.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Set Default Node.js Version[/bold blue]")
    console.print()
    
    try:
        nvm_status = get_nvm_status()
        
        if not nvm_status['installed']:
            console.print("[red]NVM is not installed.[/red]")
            return
        
        if not nvm_status['installed_versions']:
            console.print("[red]No Node.js versions installed. Please install a version first.[/red]")
            return
        
        console.print("[bold]Installed Versions:[/bold]")
        for i, version in enumerate(nvm_status['installed_versions'], 1):
            current = " (current)" if version == nvm_status['current_version'] else ""
            default = " (default)" if version == nvm_status.get('default_version') else ""
            console.print(f"  [{i}] v{version}{current}{default}")
        
        # Get user selection
        while True:
            try:
                choice = get_user_input(
                    f"Select default version (1-{len(nvm_status['installed_versions'])})"
                )
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(nvm_status['installed_versions']):
                    selected_version = nvm_status['installed_versions'][choice_num - 1]
                    break
                else:
                    console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(nvm_status['installed_versions'])}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number.[/red]")
        
        # Confirm setting default
        if not confirm_action(f"Set Node.js v{selected_version} as default?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        # Set default version
        show_progress(
            f"Setting Node.js v{selected_version} as default...",
            _set_default_version,
            selected_version, verbose
        )
        
        console.print(f"[bold green]✓ Node.js v{selected_version} set as default![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Setting default failed:[/bold red] {e}")
        logger.error(f"Setting default Node.js version failed: {e}")


def uninstall_node_version(verbose: bool = False) -> None:
    """
    Uninstall a specific Node.js version.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    
    console.print("[bold blue]Uninstall Node.js Version[/bold blue]")
    console.print()
    
    try:
        nvm_status = get_nvm_status()
        
        if not nvm_status['installed']:
            console.print("[red]NVM is not installed.[/red]")
            return
        
        if not nvm_status['installed_versions']:
            console.print("[red]No Node.js versions installed.[/red]")
            return
        
        console.print("[bold]Installed Versions:[/bold]")
        for i, version in enumerate(nvm_status['installed_versions'], 1):
            current = " (current)" if version == nvm_status['current_version'] else ""
            console.print(f"  [{i}] v{version}{current}")
        
        # Get user selection
        while True:
            try:
                choice = get_user_input(
                    f"Select version to uninstall (1-{len(nvm_status['installed_versions'])})"
                )
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(nvm_status['installed_versions']):
                    selected_version = nvm_status['installed_versions'][choice_num - 1]
                    break
                else:
                    console.print(f"[red]Invalid selection. Please enter a number between 1 and {len(nvm_status['installed_versions'])}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number.[/red]")
        
        # Warn if uninstalling current version
        if selected_version == nvm_status['current_version']:
            console.print("[yellow]Warning: You are about to uninstall the currently active Node.js version.[/yellow]")
        
        # Confirm uninstallation
        if not confirm_action(f"Uninstall Node.js v{selected_version}? This action cannot be undone."):
            console.print("[yellow]Uninstallation cancelled.[/yellow]")
            return
        
        # Uninstall version
        show_progress(
            f"Uninstalling Node.js v{selected_version}...",
            _uninstall_node_version,
            selected_version, verbose
        )
        
        console.print(f"[bold green]✓ Node.js v{selected_version} uninstalled successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Uninstallation failed:[/bold red] {e}")
        logger.error(f"Node.js version uninstallation failed: {e}")


def show_nvm_status(verbose: bool = False) -> None:
    """
    Show detailed NVM status and information.
    
    Args:
        verbose (bool): Enable verbose output
    """
    from ..cli.menu import console
    from ..core.system import get_npm_status, get_node_status
    
    console.print("[bold blue]NVM Status and Information[/bold blue]")
    console.print()
    
    try:
        nvm_status = get_nvm_status()
        node_status = get_node_status()
        npm_status = get_npm_status()
        
        # NVM Information
        console.print("[bold]NVM Information:[/bold]")
        console.print(f"  Installed: {'Yes' if nvm_status['installed'] else 'No'}")
        console.print(f"  Version: {nvm_status['version'] or 'Unknown'}")
        console.print(f"  NVM Directory: {os.path.expanduser('~/.nvm')}")
        
        if nvm_status['installed']:
            console.print(f"  Current Node.js: v{nvm_status['current_version'] or 'Not set'}")
            console.print(f"  Default Node.js: v{nvm_status['default_version'] or 'Not set'}")
            console.print(f"  Installed Versions: {len(nvm_status['installed_versions'])}")
        
        console.print()
        
        # Node.js Information
        console.print("[bold]Node.js Information:[/bold]")
        console.print(f"  Installed: {'Yes' if node_status['installed'] else 'No'}")
        console.print(f"  Version: {node_status['version'] or 'Not installed'}")
        console.print(f"  Path: {node_status['path'] or 'Not found'}")
        
        console.print()
        
        # npm Information
        console.print("[bold]npm Information:[/bold]")
        console.print(f"  Installed: {'Yes' if npm_status['installed'] else 'No'}")
        console.print(f"  Version: {npm_status['version'] or 'Not installed'}")
        console.print(f"  Path: {npm_status['path'] or 'Not found'}")
        
        console.print()
        
        # Shell Configuration
        console.print("[bold]Shell Configuration:[/bold]")
        shell_files = [
            ('~/.bashrc', os.path.expanduser("~/.bashrc")),
            ('~/.zshrc', os.path.expanduser("~/.zshrc")),
            ('~/.profile', os.path.expanduser("~/.profile"))
        ]
        
        for name, path in shell_files:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                has_nvm = 'NVM_DIR' in content or 'nvm.sh' in content
                status = "[green]Configured[/green]" if has_nvm else "[red]Not configured[/red]"
                console.print(f"  {name}: {status}")
            else:
                console.print(f"  {name}: [dim]File not found[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Failed to get NVM status:[/bold red] {e}")
        logger.error(f"Failed to get NVM status: {e}")


def _fetch_available_versions(verbose: bool = False) -> list:
    """
    Fetch available Node.js versions (16+ only as per requirement).
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        list: List of available versions
    """
    try:
        # Try NVM first, then fallback to Node.js API
        nvm_versions = _fetch_from_nvm(verbose)
        if nvm_versions:
            return nvm_versions
            
        # Fallback to Node.js official API
        return _fetch_from_nodejs_api(verbose)
            
    except Exception as e:
        logger.error(f"Error fetching available versions: {e}")
        return []


def _fetch_from_nvm(verbose: bool = False) -> list:
    """
    Try to fetch versions using NVM.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        list: List of available versions or empty list if failed
    """
    try:
        # Use NVM to list available versions, then filter for 16+
        list_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm list-remote 2>/dev/null | grep -E '^v[1-9][6-9]|^v[2-9][0-9]' | head -20
        """
        
        result = subprocess.run([
            "bash", "-c", list_cmd
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            versions = result.stdout.strip().split('\n')
            filtered_versions = [v.strip() for v in versions if v.strip()]
            
            if verbose:
                debug_log(logger, "nvm", f"Fetched {len(filtered_versions)} Node.js versions from NVM (16+ only)")
                
            return filtered_versions
        else:
            if verbose:
                logger.warning(f"NVM fetch failed: {result.stderr}")
            return []
            
    except Exception as e:
        if verbose:
            logger.warning(f"NVM fetch exception: {e}")
        return []


def _fetch_from_nodejs_api(verbose: bool = False) -> list:
    """
    Fetch Node.js versions from official Node.js API as fallback.
    
    Args:
        verbose (bool): Enable verbose output
        
    Returns:
        list: List of available versions (16+ only)
    """
    try:
        import urllib.request
        import json
        
        # Fetch Node.js versions from official API
        url = "https://nodejs.org/dist/index.json"
        
        if verbose:
            debug_log(logger, "nvm", f"Fetching Node.js versions from {url}")
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        # Filter for versions 16+ and format them
        versions = []
        for version_info in data:
            version = version_info['version']
            # Extract major version number (e.g., "v18.17.0" -> 18)
            try:
                major_version = int(version[1:].split('.')[0])
                if major_version >= 16:
                    # Add LTS info if available
                    lts_info = f" (LTS: {version_info['lts']})" if version_info.get('lts') else ""
                    versions.append(f"{version}{lts_info}")
            except (ValueError, IndexError):
                continue
                
        # Sort by version (newest first) and limit to 20
        versions.sort(key=lambda x: x.split()[0], reverse=True)
        versions = versions[:20]
        
        if verbose:
            debug_log(logger, "nvm", f"Fetched {len(versions)} Node.js versions from API (16+ only)")
            
        return versions
        
    except Exception as e:
        logger.error(f"Failed to fetch from Node.js API: {e}")
        return []


def _get_available_versions() -> list:
    """
    Get available Node.js versions with LTS information (16+ only as per requirement).
    
    Returns:
        list: List of available versions
    """
    try:
        # Try NVM first, then fallback to Node.js API
        nvm_versions = _get_from_nvm_with_lts()
        if nvm_versions:
            return nvm_versions
            
        # Fallback to Node.js official API
        return _get_from_nodejs_api_with_lts()
        
    except Exception as e:
        logger.error(f"Error getting available versions: {e}")
        return []


def _get_from_nvm_with_lts() -> list:
    """
    Try to get versions with LTS info using NVM.
    
    Returns:
        list: List of available versions or empty list if failed
    """
    try:
        # Get LTS versions (16+ only)
        lts_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm list-remote | grep -i lts | grep -E '^v[1-9][6-9]|^v[2-9][0-9]' | head -10
        """
        
        result = subprocess.run([
            "bash", "-c", lts_cmd
        ], capture_output=True, text=True)
        
        lts_versions = []
        if result.returncode == 0 and result.stdout.strip():
            lts_versions = [v.strip() for v in result.stdout.strip().split('\n') if v.strip()]
        
        # Get recent versions (16+ only)
        recent_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm list-remote | grep -v -i lts | grep -E '^v[1-9][6-9]|^v[2-9][0-9]' | head -10
        """
        
        result = subprocess.run([
            "bash", "-c", recent_cmd
        ], capture_output=True, text=True)
        
        recent_versions = []
        if result.returncode == 0 and result.stdout.strip():
            recent_versions = [v.strip() for v in result.stdout.strip().split('\n') if v.strip()]
        
        if lts_versions or recent_versions:
            return lts_versions + recent_versions
        else:
            return []
            
    except Exception as e:
        logger.warning(f"NVM LTS fetch failed: {e}")
        return []


def _get_from_nodejs_api_with_lts() -> list:
    """
    Get Node.js versions with LTS information from official API.
    
    Returns:
        list: List of available versions (16+ only)
    """
    try:
        import urllib.request
        import json
        
        # Fetch Node.js versions from official API
        url = "https://nodejs.org/dist/index.json"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        # Separate LTS and recent versions (16+ only)
        lts_versions = []
        recent_versions = []
        
        for version_info in data:
            version = version_info['version']
            # Extract major version number
            try:
                major_version = int(version[1:].split('.')[0])
                if major_version >= 16:
                    formatted_version = f"{version}"
                    if version_info.get('lts'):
                        formatted_version += f"   (LTS: {version_info['lts']})"
                        lts_versions.append(formatted_version)
                    else:
                        recent_versions.append(formatted_version)
            except (ValueError, IndexError):
                continue
                
        # Sort versions (newest first) and limit
        lts_versions.sort(key=lambda x: x.split()[0], reverse=True)
        recent_versions.sort(key=lambda x: x.split()[0], reverse=True)
        
        # Return limited lists
        return lts_versions[:10] + recent_versions[:10]
        
    except Exception as e:
        logger.error(f"Failed to get versions from Node.js API: {e}")
        return []


def _install_node_version(version: str, verbose: bool = False) -> None:
    """
    Install a specific Node.js version.
    
    Args:
        version (str): Node.js version to install
        verbose (bool): Enable verbose output
    """
    install_cmd = f"""
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install {version}
    """
    
    result = subprocess.run([
        "bash", "-c", install_cmd
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to install Node.js {version}: {result.stderr}")
    
    logger.info(f"Node.js {version} installed successfully")


def _switch_node_version(version: str, verbose: bool = False) -> None:
    """
    Switch to a specific Node.js version.
    
    Args:
        version (str): Node.js version to switch to
        verbose (bool): Enable verbose output
    """
    switch_cmd = f"""
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm use {version}
    nvm alias default {version}
    """
    
    result = subprocess.run([
        "bash", "-c", switch_cmd
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to switch to Node.js {version}: {result.stderr}")
    
    logger.info(f"Switched to Node.js {version}")


def _set_default_version(version: str, verbose: bool = False) -> None:
    """
    Set default Node.js version.
    
    Args:
        version (str): Node.js version to set as default
        verbose (bool): Enable verbose output
    """
    default_cmd = f"""
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm alias default {version}
    """
    
    result = subprocess.run([
        "bash", "-c", default_cmd
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to set default Node.js {version}: {result.stderr}")
    
    logger.info(f"Node.js {version} set as default")


def _uninstall_node_version(version: str, verbose: bool = False) -> None:
    """
    Uninstall a specific Node.js version.
    
    Args:
        version (str): Node.js version to uninstall
        verbose (bool): Enable verbose output
    """
    uninstall_cmd = f"""
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm uninstall {version}
    """
    
    result = subprocess.run([
        "bash", "-c", uninstall_cmd
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to uninstall Node.js {version}: {result.stderr}")
    
    logger.info(f"Node.js {version} uninstalled successfully")