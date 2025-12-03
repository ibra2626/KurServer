"""
Logging configuration for KurServer CLI.
"""

import logging
import os
from pathlib import Path


def setup_logger(name="kurserver", level=logging.INFO, log_file=None):
    """
    Set up logging configuration for KurServer CLI.
    
    Args:
        name (str): Logger name
        level (int): Logging level
        log_file (str, optional): Path to log file. If None, logs to console only.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # More verbose logging to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name="kurserver"):
    """
    Get a logger instance.
    
    Args:
        name (str): Logger name
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def setup_file_logging():
    """
    Set up file logging with default configuration.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Default log file location
    log_dir = Path.home() / ".kurserver" / "logs"
    log_file = log_dir / "kurserver.log"
    
    return setup_logger(log_file=str(log_file))


def log_operation_start(logger, operation):
    """Log the start of an operation."""
    logger.info(f"Starting operation: {operation}")


def log_operation_success(logger, operation, duration=None):
    """Log successful completion of an operation."""
    if duration:
        logger.info(f"Operation completed successfully: {operation} (took {duration:.2f}s)")
    else:
        logger.info(f"Operation completed successfully: {operation}")


def log_operation_error(logger, operation, error):
    """Log operation failure."""
    logger.error(f"Operation failed: {operation} - {error}")


def log_system_info(logger, system_info):
    """Log system information."""
    logger.info("System Information:")
    for key, value in system_info.items():
        logger.info(f"  {key}: {value}")