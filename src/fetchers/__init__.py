"""
Fetchers package for AI-RSS-Client
"""

from .api_client import AIRSSHubClient, APIError, create_client

__all__ = ['AIRSSHubClient', 'APIError', 'create_client']
