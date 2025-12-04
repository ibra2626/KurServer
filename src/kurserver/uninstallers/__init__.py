"""
Uninstaller modules for KurServer CLI.
"""

from .base import BaseUninstaller
from .nginx import NginxUninstaller
from .mysql import MySQLUninstaller
from .php import PHPUninstaller

__all__ = [
    'BaseUninstaller',
    'NginxUninstaller',
    'MySQLUninstaller',
    'PHPUninstaller'
]