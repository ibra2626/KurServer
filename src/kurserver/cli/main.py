#!/usr/bin/env python3
"""
KurServer CLI - Main entry point for the server management CLI tool.
"""

import click
import sys
from rich.console import Console
from rich.text import Text

from ..core.exceptions import KurServerError
from ..core.logger import setup_logger
from ..config.debug import is_debug_enabled, enable_debug, disable_debug, get_debug_status
from .menu import main_menu

# Initialize Rich console for beautiful output
console = Console()

# Setup logger with debug mode check
debug_enabled = is_debug_enabled()
logger = setup_logger(debug_mode=debug_enabled)


@click.group()
@click.version_option(version="1.0.0", prog_name="KurServer")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    KurServer CLI - Ubuntu server management tool for rapid web server setup.
    
    Simplified server management without the complexity of traditional control panels.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print("[bold green]KurServer CLI[/bold green] - Verbose mode enabled")
    
    try:
        # Check if running on Ubuntu
        from ..core.system import check_system_requirements
        check_system_requirements()
    except KurServerError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start the interactive menu system."""
    console.print("[bold blue]Welcome to KurServer CLI![/bold blue]")
    console.print("This tool will help you set up and manage your web server.")
    console.print()
    
    try:
        main_menu(ctx.obj.get('verbose', False))
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except KurServerError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def status():
    """Show the status of installed services."""
    console.print("[bold blue]Server Status[/bold blue]")
    console.print("Checking installed services...")
    
    try:
        from ..core.system import get_service_status
        services = get_service_status()
        
        for service, status in services.items():
            if status['installed']:
                status_color = "green" if status['running'] else "red"
                status_text = "running" if status['running'] else "stopped"
                console.print(f"  {service}: [{status_color}]{status_text}[/{status_color}]")
            else:
                console.print(f"  {service}: [dim]not installed[/dim]")
                
    except KurServerError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.group()
def debug():
    """Manage debug mode settings."""
    pass


@debug.command()
@click.option('--component', '-c', help='Enable debug for specific component (system, nginx, mysql, php, general)')
def enable(component):
    """Enable debug mode."""
    if component:
        if component not in ['system', 'nginx', 'mysql', 'php', 'general']:
            console.print(f"[red]Invalid component: {component}[/red]")
            console.print("Valid components: system, nginx, mysql, php, general")
            sys.exit(1)
        enable_debug(component)
        console.print(f"[green]✓ Debug mode enabled for component: {component}[/green]")
    else:
        enable_debug()
        console.print("[green]✓ Debug mode enabled globally[/green]")
    
    # Show current status
    status = get_debug_status()
    console.print("\n[bold]Current Debug Status:[/bold]")
    console.print(f"Global: {'Enabled' if status['global_enabled'] else 'Disabled'}")
    console.print("Components:")
    for comp, enabled in status['components'].items():
        status_text = "Enabled" if enabled else "Disabled"
        color = "green" if enabled else "dim"
        console.print(f"  {comp}: [{color}]{status_text}[/{color}]")


@debug.command()
@click.option('--component', '-c', help='Disable debug for specific component (system, nginx, mysql, php, general)')
def disable(component):
    """Disable debug mode."""
    if component:
        if component not in ['system', 'nginx', 'mysql', 'php', 'general']:
            console.print(f"[red]Invalid component: {component}[/red]")
            console.print("Valid components: system, nginx, mysql, php, general")
            sys.exit(1)
        disable_debug(component)
        console.print(f"[yellow]Debug mode disabled for component: {component}[/yellow]")
    else:
        disable_debug()
        console.print("[yellow]Debug mode disabled globally[/yellow]")
    
    # Show current status
    status = get_debug_status()
    console.print("\n[bold]Current Debug Status:[/bold]")
    console.print(f"Global: {'Enabled' if status['global_enabled'] else 'Disabled'}")
    console.print("Components:")
    for comp, enabled in status['components'].items():
        status_text = "Enabled" if enabled else "Disabled"
        color = "green" if enabled else "dim"
        console.print(f"  {comp}: [{color}]{status_text}[/{color}]")


@debug.command()
def status():
    """Show current debug status."""
    status_info = get_debug_status()
    
    console.print("[bold]Debug Mode Status[/bold]")
    console.print(f"Global: {'Enabled' if status_info['global_enabled'] else 'Disabled'}")
    console.print("\nComponents:")
    
    for component, enabled in status_info['components'].items():
        status_text = "Enabled" if enabled else "Disabled"
        color = "green" if enabled else "dim"
        icon = "✓" if enabled else "✗"
        console.print(f"  {icon} {component}: [{color}]{status_text}[/{color}]")


def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()