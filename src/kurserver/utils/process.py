"""
Process management utilities for KurServer CLI.
"""

import subprocess
import time
import re
from typing import List, Dict, Optional, Tuple

from ..core.logger import get_logger

logger = get_logger()


def get_processes_using_port(port: int) -> List[Dict]:
    """
    Get list of processes using a specific port.
    
    Args:
        port (int): Port number to check
        
    Returns:
        List[Dict]: List of processes using the port
    """
    processes = []
    
    try:
        # Use netstat to find processes using the port
        result = subprocess.run(
            ["sudo", "netstat", "-tlnp"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if f":{port} " in line and "LISTEN" in line:
                    # Parse the line to extract process info
                    parts = line.split()
                    if len(parts) >= 7:
                        address = parts[3]
                        pid_info = parts[6]
                        
                        # Extract PID and process name
                        if '/' in pid_info:
                            pid, process_name = pid_info.split('/', 1)
                        else:
                            pid = pid_info
                            process_name = "unknown"
                        
                        processes.append({
                            'port': port,
                            'address': address,
                            'pid': pid,
                            'process_name': process_name,
                            'full_line': line
                        })
        
        # Also try using lsof as backup method
        if not processes:
            result = subprocess.run(
                ["sudo", "lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            process_name = parts[0]
                            pid = parts[1]
                            processes.append({
                                'port': port,
                                'address': f"*:{port}",
                                'pid': pid,
                                'process_name': process_name,
                                'full_line': line
                            })
    
    except Exception as e:
        logger.warning(f"Error getting processes for port {port}: {e}")
    
    return processes


# Process termination functions have been removed as per requirements
# The following functions are kept for process information purposes only


def verify_port_free(port: int, timeout: int = 5) -> bool:
    """
    Verify that a port is free (no processes listening).
    
    Args:
        port (int): Port number to check
        timeout (int): Timeout in seconds
        
    Returns:
        bool: True if port is free, False otherwise
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        processes = get_processes_using_port(port)
        if not processes:
            return True
        time.sleep(0.5)
    
    return False


def get_nginx_processes() -> List[Dict]:
    """
    Get all Nginx-related processes.
    
    Returns:
        List[Dict]: List of Nginx processes
    """
    processes = []
    
    try:
        # Get processes by name
        result = subprocess.run(
            ["sudo", "pgrep", "-f", "nginx"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            
            for pid in pids:
                if pid.strip():
                    # Get detailed process info
                    try:
                        result = subprocess.run(
                            ["ps", "-p", pid, "-o", "pid,ppid,cmd"],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            if len(lines) >= 2:
                                parts = lines[1].split(None, 2)
                                if len(parts) >= 3:
                                    processes.append({
                                        'pid': parts[0],
                                        'ppid': parts[1],
                                        'command': parts[2]
                                    })
                    except Exception:
                        pass
    
    except Exception as e:
        logger.warning(f"Error getting Nginx processes: {e}")
    
    return processes


# Process termination functions have been removed as per requirements
# The following functions are kept for process information purposes only