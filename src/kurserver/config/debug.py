"""
Debug mode configuration for KurServer CLI.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


class DebugConfig:
    """
    Manages debug mode configuration for KurServer CLI.
    """
    
    def __init__(self):
        self.config_dir = Path.home() / ".kurserver"
        self.config_file = self.config_dir / "debug.json"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load debug configuration from file.
        
        Returns:
            dict: Configuration dictionary
        """
        default_config = {
            "debug_enabled": False,
            "debug_components": {
                "system": False,
                "nginx": False,
                "mysql": False,
                "php": False,
                "general": False
            }
        }
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with default to ensure all keys exist
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                return loaded_config
            except (json.JSONDecodeError, IOError):
                # If config is corrupted, use default
                return default_config
        
        return default_config
    
    def _save_config(self) -> None:
        """
        Save debug configuration to file.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            # If we can't save config, that's not critical
            # Just print a warning
            print(f"Warning: Could not save debug config: {e}")
    
    def is_debug_enabled(self, component: str = None) -> bool:
        """
        Check if debug mode is enabled for a specific component or globally.
        
        Args:
            component (str, optional): Component name to check. If None, checks global debug setting.
            
        Returns:
            bool: True if debug is enabled, False otherwise
        """
        if not self._config.get("debug_enabled", False):
            return False
        
        if component is None:
            return self._config.get("debug_enabled", False)
        
        return self._config.get("debug_components", {}).get(component, False)
    
    def enable_debug(self, component: str = None) -> None:
        """
        Enable debug mode globally or for a specific component.
        
        Args:
            component (str, optional): Component name to enable debug for. If None, enables globally.
        """
        if component is None:
            # Enable global debug and all components
            self._config["debug_enabled"] = True
            for comp in self._config["debug_components"]:
                self._config["debug_components"][comp] = True
        else:
            # Enable global debug if not already enabled
            self._config["debug_enabled"] = True
            # Enable specific component
            if component in self._config["debug_components"]:
                self._config["debug_components"][component] = True
        
        self._save_config()
    
    def disable_debug(self, component: str = None) -> None:
        """
        Disable debug mode globally or for a specific component.
        
        Args:
            component (str, optional): Component name to disable debug for. If None, disables globally.
        """
        if component is None:
            # Disable global debug and all components
            self._config["debug_enabled"] = False
            for comp in self._config["debug_components"]:
                self._config["debug_components"][comp] = False
        else:
            # Disable specific component
            if component in self._config["debug_components"]:
                self._config["debug_components"][component] = False
            
            # Check if any components are still enabled
            any_enabled = any(self._config["debug_components"].values())
            if not any_enabled:
                self._config["debug_enabled"] = False
        
        self._save_config()
    
    def get_debug_status(self) -> Dict[str, Any]:
        """
        Get current debug status for all components.
        
        Returns:
            dict: Debug status information
        """
        return {
            "global_enabled": self._config.get("debug_enabled", False),
            "components": self._config.get("debug_components", {}).copy()
        }


# Global debug config instance
_debug_config = DebugConfig()


def is_debug_enabled(component: str = None) -> bool:
    """
    Check if debug mode is enabled for a specific component or globally.
    
    Args:
        component (str, optional): Component name to check. If None, checks global debug setting.
        
    Returns:
        bool: True if debug is enabled, False otherwise
    """
    return _debug_config.is_debug_enabled(component)


def enable_debug(component: str = None) -> None:
    """
    Enable debug mode globally or for a specific component.
    
    Args:
        component (str, optional): Component name to enable debug for. If None, enables globally.
    """
    _debug_config.enable_debug(component)


def disable_debug(component: str = None) -> None:
    """
    Disable debug mode globally or for a specific component.
    
    Args:
        component (str, optional): Component name to disable debug for. If None, disables globally.
    """
    _debug_config.disable_debug(component)


def get_debug_status() -> Dict[str, Any]:
    """
    Get current debug status for all components.
    
    Returns:
        dict: Debug status information
    """
    return _debug_config.get_debug_status()