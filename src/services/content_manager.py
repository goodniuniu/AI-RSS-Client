"""
Content Manager for AI-RSS-Client
Handles content fetching from API and cache management
"""

import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..fetchers import AIRSSHubClient
from ..processors import ArticleCache
from ..models import Article
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContentManager:
    """
    Content Manager - Main content orchestration layer

    Responsibilities:
    - Fetch articles from AI-RSS-Hub API
    - Manage local cache
    - Track reading state
    - Provide articles for display
    - Handle offline mode
    """

    def __init__(self, api_client: AIRSSHubClient = None,
                 cache: ArticleCache = None,
                 fetch_interval_minutes: int = 20,
                 batch_size: int = 200,  # 增加默认值到200
                 max_cached_articles: int = 1000,  # 增加默认值到1000
                 display_days: int = 3):  # 新增display_days参数
        """
        Initialize content manager

        Args:
            api_client: API client instance (created if None)
            cache: Article cache instance (created if None)
            fetch_interval_minutes: Interval between fetches
            batch_size: Number of articles to fetch per batch
            max_cached_articles: Maximum articles to cache
        """
        # Create API client if not provided
        if api_client is None:
            api_client = AIRSSHubClient()

        # Create cache if not provided
        if cache is None:
            cache = ArticleCache(max_articles=max_cached_articles)

        self.api_client = api_client
        self.cache = cache
        self.fetch_interval_minutes = fetch_interval_minutes
        self.batch_size = batch_size
        self.display_days = display_days  # 循环播放的天数

        # State tracking
        self.last_fetch_time: Optional[datetime] = None
        self.last_fetch_count: int = 0
        self.is_fetching: bool = False

        logger.info(f"Content manager initialized (batch_size={batch_size}, "
                   f"max_cached={max_cached_articles}, display_days={display_days})")

    def fetch_and_process_content(self, category: str = None, days: int = None,
                                   start_date: str = None, end_date: str = None,
                                   incremental: bool = False, feed_id: int = None) -> bool:
        """
        Fetch new content from API and update cache with enhanced filtering

        Args:
            category: Filter by category
            days: Fetch articles from last N days
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            incremental: If True, only fetch articles newer than last cached article
            feed_id: Filter by specific RSS feed ID

        Returns:
            True if successful, False otherwise
        """
        if self.is_fetching:
            logger.warning("Already fetching, skipping")
            return False

        self.is_fetching = True
        try:
            logger.info("Starting content fetch cycle")

            # Check API connection
            if not self.api_client.test_connection():
                logger.error("API connection test failed")
                return False

            # Fetch articles from API with enhanced filtering
            fetch_params = {
                'limit': self.batch_size
            }

            # Build fetch parameters
            if incremental:
                # Incremental mode: only get articles newer than last cached
                last_article = self.cache.get_latest_article()
                if last_article and last_article.published_at:
                    fetch_params['after'] = last_article.published_at
                    logger.info(f"Incremental fetch: getting articles after {last_article.published_at}")
                else:
                    # No cached articles, fetch recent articles
                    fetch_params['days'] = days or self.fetch_interval_minutes // 1440  # Convert minutes to days if needed
                    logger.info(f"No cached articles, fetching recent {fetch_params.get('days', 'all')} articles")
            elif start_date or end_date:
                # Date range mode
                if start_date:
                    fetch_params['start_date'] = start_date
                if end_date:
                    fetch_params['end_date'] = end_date
                logger.info(f"Date range fetch: {start_date} to {end_date}")
            else:
                # Default: use days parameter
                fetch_params['days'] = days or 3

            # Add optional filters
            if category:
                fetch_params['category'] = category
            if feed_id:
                fetch_params['feed_id'] = feed_id

            logger.info(f"Fetching articles with params: {fetch_params}")
            articles = self.api_client.get_articles(**fetch_params)

            if not articles:
                logger.warning("No articles returned from API")
                return False

            # Add to cache
            added_count = self.cache.add_articles(articles)

            # Update state
            self.last_fetch_time = datetime.now()
            self.last_fetch_count = added_count

            logger.info(f"Content fetch completed: {added_count} new articles added")
            return True

        except Exception as e:
            logger.error(f"Content fetch failed: {e}")
            return False

        finally:
            self.is_fetching = False

    def get_article_for_display(self) -> Optional[Article]:
        """
        Get an article for display on e-paper

        Selection strategy (真正的循环播放):
        1. 优先选择最久未显示的文章（按displayed_at ASC排序）
        2. 如果从未显示过的文章，随机选择一篇
        3. 这样实现真正的轮询，避免重复显示同一篇

        Returns:
            Article object or None if no articles available
        """
        try:
            # 策略1: 获取最近display_days天内最久未显示的文章（实现轮询）
            recent_articles = self.cache.get_articles_by_display_time(limit=200, days=self.display_days)

            if recent_articles:
                # 选择第一篇（最久未显示的）
                article = recent_articles[0]
                logger.info(f"Selected article (least recently displayed): {article.display_title} "
                          f"(last displayed: {article.displayed_at or 'Never'})")
                return article

            # 策略2: 如果没有最近的文章，随机选择一篇'new'状态的文章
            new_articles = self.cache.get_undisplayed_articles(limit=1)

            if new_articles:
                article = new_articles[0]
                logger.info(f"Selected new article: {article.display_title}")
                return article

            # 策略3: 兜底方案，随机选择任意文章
            article = self.cache.get_random_article()
            if article:
                logger.info(f"Selected random article: {article.display_title}")
                return article

            logger.warning("No articles available for display")
            return None

        except Exception as e:
            logger.error(f"Failed to get article for display: {e}")
            return None

    def mark_as_displayed(self, article_id: int) -> bool:
        """
        Mark article as displayed

        Args:
            article_id: Article ID

        Returns:
            True if successful
        """
        try:
            success = self.cache.mark_as_displayed(article_id)
            if success:
                logger.debug(f"Marked article {article_id} as displayed")
            return success
        except Exception as e:
            logger.error(f"Failed to mark article as displayed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get content manager status

        Returns:
            Dict with status information
        """
        cache_stats = self.cache.get_stats()

        status = {
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_fetch_count': self.last_fetch_count,
            'is_fetching': self.is_fetching,
            'fetch_interval_minutes': self.fetch_interval_minutes,
            'api_connected': False,
            'total_summaries': cache_stats.get('with_summary_count', 0),
            'undisplayed_count': cache_stats.get('undisplayed_count', 0),
        }

        # Test API connection
        try:
            status['api_connected'] = self.api_client.test_connection()
        except Exception:
            status['api_connected'] = False

        return status

    def should_fetch(self) -> bool:
        """
        Check if it's time to fetch new content

        Returns:
            True if should fetch now
        """
        if self.last_fetch_time is None:
            # Never fetched
            return True

        time_since_fetch = (datetime.now() - self.last_fetch_time).total_seconds()
        return time_since_fetch >= (self.fetch_interval_minutes * 60)

    def get_recent_articles(self, limit: int = 50, days: int = None,
                            undisplayed_only: bool = False) -> List[Article]:
        """
        Get recent articles from cache

        Args:
            limit: Maximum number of articles
            days: Only return articles from last N days
            undisplayed_only: Only return undisplayed articles

        Returns:
            List of Article objects
        """
        try:
            if undisplayed_only:
                return self.cache.get_undisplayed_articles(limit=limit)
            else:
                return self.cache.get_recent_articles(limit=limit, days=days)
        except Exception as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []

    def force_refresh(self) -> bool:
        """
        Force immediate content refresh

        Returns:
            True if successful
        """
        logger.info("Forcing content refresh")
        return self.fetch_and_process_content()

    def trigger_backend_fetch(self) -> bool:
        """
        Trigger backend to fetch from RSS sources

        This calls the API's manual fetch endpoint to immediately
        fetch new content from RSS sources.

        Returns:
            True if successful
        """
        try:
            logger.info("Triggering backend RSS fetch")
            result = self.api_client.trigger_fetch()

            stats = result.get('stats', {})
            logger.info(f"Backend fetch result: {stats.get('successful_feeds')}/{stats.get('total_feeds')} feeds, "
                       f"{stats.get('total_articles')} articles")

            return True

        except Exception as e:
            logger.error(f"Failed to trigger backend fetch: {e}")
            return False

    def fetch_by_feed(self, feed_id: int, limit: int = None) -> bool:
        """
        Fetch articles from a specific RSS feed

        Args:
            feed_id: RSS feed ID to fetch from
            limit: Maximum number of articles to fetch (default: use batch_size)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Fetching articles from feed ID: {feed_id}")
        return self.fetch_and_process_content(feed_id=feed_id)

    def fetch_by_date_range(self, start_date: str, end_date: str, limit: int = None) -> bool:
        """
        Fetch articles from a specific date range

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of articles to fetch (default: use batch_size)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Fetching articles from {start_date} to {end_date}")
        return self.fetch_and_process_content(start_date=start_date, end_date=end_date)

    def fetch_incremental(self) -> bool:
        """
        Fetch only new articles (incremental update)

        This method only fetches articles that are newer than the latest
        cached article, reducing bandwidth and processing time.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Fetching incremental articles")
        return self.fetch_and_process_content(incremental=True)

    def get_offline_articles(self, limit: int = 50) -> List[Article]:
        """
        Get articles for offline display

        Returns articles from cache (works without network)

        Args:
            limit: Maximum number of articles

        Returns:
            List of Article objects
        """
        logger.info("Getting offline articles from cache")
        return self.cache.get_recent_articles(limit=limit)

    def clear_cache(self):
        """Clear all cached content"""
        logger.warning("Clearing cache")
        self.cache.clear()
        self.last_fetch_time = None
        self.last_fetch_count = 0

    def close(self):
        """Close connections and cleanup"""
        if self.api_client:
            self.api_client.close()
        logger.info("Content manager closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
