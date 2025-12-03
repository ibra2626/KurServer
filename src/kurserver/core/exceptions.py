"""
Custom exception classes for KurServer CLI.
"""


class KurServerError(Exception):
    """Base exception class for KurServer CLI errors."""
    
    def __init__(self, message, suggestion=None):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
    
    def __str__(self):
        if self.suggestion:
            return f"{self.message}\nSuggestion: {self.suggestion}"
        return self.message


class SystemRequirementError(KurServerError):
    """Raised when system requirements are not met."""
    
    def __init__(self, requirement, current_value=None):
        message = f"System requirement not met: {requirement}"
        if current_value:
            message += f" (current: {current_value})"
        suggestion = "Please ensure you're running on a supported Ubuntu system with sudo access."
        super().__init__(message, suggestion)


class PermissionError(KurServerError):
    """Raised when insufficient permissions for an operation."""
    
    def __init__(self, operation):
        message = f"Insufficient permissions for: {operation}"
        suggestion = "Please run with sudo or check your user permissions."
        super().__init__(message, suggestion)


class PackageInstallationError(KurServerError):
    """Raised when package installation fails."""
    
    def __init__(self, package_name, error_details=None):
        message = f"Failed to install package: {package_name}"
        if error_details:
            message += f"\nDetails: {error_details}"
        suggestion = f"Check your internet connection and try running 'sudo apt update' first."
        super().__init__(message, suggestion)


class ServiceError(KurServerError):
    """Raised when service operations fail."""
    
    def __init__(self, service_name, operation, error_details=None):
        message = f"Failed to {operation} service: {service_name}"
        if error_details:
            message += f"\nDetails: {error_details}"
        suggestion = f"Check service logs with 'sudo journalctl -u {service_name}' for more information."
        super().__init__(message, suggestion)


class ConfigurationError(KurServerError):
    """Raised when configuration operations fail."""
    
    def __init__(self, config_file, operation, error_details=None):
        message = f"Failed to {operation} configuration: {config_file}"
        if error_details:
            message += f"\nDetails: {error_details}"
        suggestion = "Check file permissions and ensure configuration syntax is correct."
        super().__init__(message, suggestion)


class ValidationError(KurServerError):
    """Raised when input validation fails."""
    
    def __init__(self, field_name, value, constraint):
        message = f"Invalid value for {field_name}: '{value}'"
        suggestion = f"Value must: {constraint}"
        super().__init__(message, suggestion)


class GitHubError(KurServerError):
    """Raised when GitHub operations fail."""
    
    def __init__(self, operation, error_details=None):
        message = f"GitHub operation failed: {operation}"
        if error_details:
            message += f"\nDetails: {error_details}"
        suggestion = "Check your GitHub token and repository permissions."
        super().__init__(message, suggestion)