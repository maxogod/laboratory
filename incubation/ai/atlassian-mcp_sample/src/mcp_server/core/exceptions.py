class AppError(Exception):
    """Base exception for atlassian-mcp."""


class ConfigurationError(AppError):
    """Raised when configuration is missing or invalid."""


class IntegrationError(AppError):
    """Base exception for integration errors."""


class JiraError(IntegrationError):
    """Base exception for Jira-related errors."""


class JiraAuthenticationError(JiraError):
    """Raised when authentication with Jira fails (401 status)."""


class JiraPermissionError(JiraError):
    """Raised when access is forbidden or permissions are missing (403 status)."""


class JiraNotFoundError(JiraError):
    """Raised when a Jira resource is not found (404 status)."""


class BitbucketError(IntegrationError):
    """Base exception for Bitbucket-related errors."""


class BitbucketAuthenticationError(BitbucketError):
    """Raised when authentication with Bitbucket fails (401 status)."""


class BitbucketPermissionError(BitbucketError):
    """Raised when access is forbidden or permissions are missing (403 status)."""


class BitbucketNotFoundError(BitbucketError):
    """Raised when a Bitbucket resource is not found (404 status)."""
