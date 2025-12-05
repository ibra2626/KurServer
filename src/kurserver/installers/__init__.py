"""
KurServer installers package.

This package contains modules for installing various server components.
"""

from .nginx import install_nginx_menu
from .mysql import install_mysql_menu
from .php import install_php_menu
from .nvm import install_nvm_menu

__all__ = [
    'install_nginx_menu',
    'install_mysql_menu', 
    'install_php_menu',
    'install_nvm_menu'
]