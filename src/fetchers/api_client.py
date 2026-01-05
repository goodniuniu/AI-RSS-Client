"""
AI-RSS-Hub API Client
Handles all communication with the AI-RSS-Hub backend
"""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models import Article, Feed
from ..utils.logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """API error exception"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AIRSSHubClient:
    """
    AI-RSS-Hub API Client

    Handles communication with the AI-RSS-Hub backend API.
    Implements all API endpoints with error handling and retry logic.
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = None,
                 timeout: int = 30, retry_attempts: int = 3, retry_delay: int = 2):
        """
        Initialize API client

        Args:
            base_url: Base URL of AI-RSS-Hub API (default: http://localhost:8000)
            api_token: Optional API token for protected endpoints
            timeout: Request timeout in seconds (default: 30)
            retry_attempts: Number of retry attempts for failed requests (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        logger.info(f"API client initialized: {self.base_url}")

    def _request(self, method: str, endpoint: str, requires_auth: bool = False,
                 **kwargs) -> Dict[str, Any]:
        """
        Send HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., '/api/articles')
            requires_auth: Whether to include API token
            **kwargs: Additional arguments for requests.request

        Returns:
            Parsed JSON response

        Raises:
            APIError: If request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})

        # Add authentication header if required
        if requires_auth:
            if not self.api_token:
                raise APIError("API token required for this endpoint, but not provided")

            headers['X-API-Token'] = self.api_token
            logger.debug(f"Adding auth header for {endpoint}")

        # Add timeout
        kwargs.setdefault('timeout', self.timeout)

        # Retry logic
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Request: {method} {url} (attempt {attempt + 1}/{self.retry_attempts})")

                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )

                # Handle HTTP errors
                if response.status_code == 401:
                    raise APIError("Unauthorized: Invalid or missing API token", 401)

                if response.status_code == 403:
                    raise APIError("Forbidden: API token rejected", 403)

                if response.status_code == 429:
                    # Rate limit - wait and retry
                    if attempt < self.retry_attempts - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        raise APIError("Rate limit exceeded", 429)

                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', response.text)
                    except ValueError:
                        error_msg = response.text

                    raise APIError(error_msg, response.status_code)

                # Parse JSON response
                return response.json()

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Request timeout: {e}")

            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Connection error: {e}")

            except APIError as e:
                # Don't retry API errors (4xx errors)
                raise e

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")

            # Wait before retry
            if attempt < self.retry_attempts - 1:
                import time
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        # All retries failed
        error_msg = f"Request failed after {self.retry_attempts} attempts: {last_error}"
        logger.error(error_msg)
        raise APIError(error_msg)

    def health_check(self) -> Dict[str, str]:
        """
        Check API health status

        GET /api/health

        Returns:
            Dict with status and message
            Example: {"status": "ok", "message": "AI-RSS-Hub is running"}
        """
        try:
            logger.debug("Health check")
            response = self._request('GET', '/api/health')
            logger.info(f"Health check: {response.get('status')}")
            return response
        except APIError as e:
            logger.error(f"Health check failed: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get system status

        GET /api/status

        Returns:
            Dict with system status information
            Example: {
                "status": "running",
                "scheduler": {...},
                "database": "...",
                "fetch_interval_hours": 1,
                "llm_configured": true
            }
        """
        try:
            logger.debug("Fetching system status")
            response = self._request('GET', '/api/status')
            logger.info(f"System status: {response.get('status')}")
            return response
        except APIError as e:
            logger.error(f"Failed to get status: {e}")
            raise

    def get_feeds(self, active_only: bool = False) -> List[Feed]:
        """
        Get list of RSS feeds

        GET /api/feeds?active_only=true

        Args:
            active_only: Only return active feeds

        Returns:
            List of Feed objects
        """
        try:
            params = {'active_only': 'true'} if active_only else {}
            logger.debug(f"Fetching feeds (active_only={active_only})")

            response_data = self._request('GET', '/api/feeds', params=params)

            feeds = [Feed.from_api_response(item) for item in response_data]
            logger.info(f"Fetched {len(feeds)} feeds")
            return feeds

        except APIError as e:
            logger.error(f"Failed to fetch feeds: {e}")
            raise

    def add_feed(self, name: str, url: str, category: str = 'tech',
                 is_active: bool = True) -> Feed:
        """
        Add new RSS feed

        POST /api/feeds (requires authentication)

        Args:
            name: Feed name
            url: Feed URL
            category: Feed category
            is_active: Whether feed is active

        Returns:
            Created Feed object
        """
        try:
            data = {
                'name': name,
                'url': url,
                'category': category,
                'is_active': is_active
            }

            logger.info(f"Adding feed: {name} ({url})")
            response_data = self._request(
                'POST',
                '/api/feeds',
                requires_auth=True,
                json=data
            )

            feed = Feed.from_api_response(response_data)
            logger.info(f"Successfully added feed: {feed.name} (ID: {feed.id})")
            return feed

        except APIError as e:
            logger.error(f"Failed to add feed: {e}")
            raise

    def get_articles(self, limit: int = 50, category: str = None,
                     days: int = None, start_date: str = None, end_date: str = None,
                     after: str = None, before: str = None, since: str = None,
                     feed_id: int = None) -> List[Article]:
        """
        Get list of articles with enhanced filtering

        GET /api/articles?limit=50&category=tech&days=7&start_date=2026-01-01&end_date=2026-01-05

        Args:
            limit: Maximum number of articles to return (1-200)
            category: Filter by category
            days: Only return articles from last N days
            start_date: Start date (ISO 8601 format: YYYY-MM-DD)
            end_date: End date (ISO 8601 format: YYYY-MM-DD)
            after: Get articles after this timestamp (ISO 8601 format)
            before: Get articles before this timestamp (ISO 8601 format)
            since: Get articles since this date (ISO 8601 format: YYYY-MM-DD)
            feed_id: Filter by specific RSS feed ID

        Returns:
            List of Article objects
        """
        try:
            params = {'limit': limit}

            # Add optional parameters
            if category:
                params['category'] = category
            if days:
                params['days'] = days
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if after:
                params['after'] = after
            if before:
                params['before'] = before
            if since:
                params['since'] = since
            if feed_id:
                params['feed_id'] = feed_id

            logger.debug(f"Fetching articles: {params}")
            response_data = self._request('GET', '/api/articles', params=params)

            articles = [Article.from_api_response(item) for item in response_data]

            # Log summary
            with_summary = sum(1 for a in articles if a.summary)
            logger.info(f"Fetched {len(articles)} articles ({with_summary} with summaries)")

            return articles

        except APIError as e:
            logger.error(f"Failed to fetch articles: {e}")
            raise

    def trigger_fetch(self) -> Dict[str, Any]:
        """
        Manually trigger RSS fetch

        POST /api/feeds/fetch (requires authentication)

        Returns:
            Dict with fetch results and statistics
            Example: {
                "status": "success",
                "message": "...",
                "stats": {
                    "total_feeds": 3,
                    "successful_feeds": 3,
                    "total_articles": 15,
                    ...
                }
            }
        """
        try:
            logger.info("Triggering manual fetch")
            response = self._request('POST', '/api/feeds/fetch', requires_auth=True)

            stats = response.get('stats', {})
            logger.info(f"Fetch completed: {response.get('message')}")
            logger.info(f"Stats: {stats.get('successful_feeds')}/{stats.get('total_feeds')} feeds, "
                       f"{stats.get('total_articles')} articles")

            return response

        except APIError as e:
            logger.error(f"Failed to trigger fetch: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test connection to API

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.health_check()
            logger.info("API connection test successful")
            return True
        except APIError as e:
            logger.error(f"API connection test failed: {e}")
            return False

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
            logger.debug("API client session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function for creating client
def create_client(base_url: str = "http://localhost:8000",
                  api_token: str = None,
                  **kwargs) -> AIRSSHubClient:
    """
    Create and configure API client

    Args:
        base_url: Base URL of AI-RSS-Hub API
        api_token: API token for protected endpoints
        **kwargs: Additional client configuration

    Returns:
        Configured AIRSSHubClient instance
    """
    return AIRSSHubClient(base_url=base_url, api_token=api_token, **kwargs)
