"""
Cache management for AI-RSS-Client
Handles local storage of articles and reading state
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models import Article, Feed, ArticleStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CacheError(Exception):
    """Cache operation error"""
    pass


class ArticleCache:
    """
    Article cache with SQLite backend and JSON backup

    Features:
    - SQLite database for fast queries
    - JSON backup for offline recovery
    - Reading state tracking
    - Automatic cleanup of old articles
    """

    def __init__(self, db_path: str = "data/articles.db",
                 backup_path: str = "data/offline_cache.json",
                 max_articles: int = 1000,
                 retention_days: int = 30):
        """
        Initialize article cache

        Args:
            db_path: Path to SQLite database file
            backup_path: Path to JSON backup file
            max_articles: Maximum number of articles to cache
            retention_days: Days to keep articles before cleanup
        """
        self.db_path = db_path
        self.backup_path = backup_path
        self.max_articles = max_articles
        self.retention_days = retention_days

        # Create data directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        logger.info(f"Article cache initialized: {db_path}")

    def _init_db(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY,
                    feed_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    published_at TEXT,
                    created_at TEXT,

                    -- Frontend fields
                    displayed_at TEXT,
                    display_count INTEGER DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'new',

                    -- Metadata
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(id)
                )
            ''')

            # Feeds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feeds (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT,

                    -- Metadata
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(id)
                )
            ''')

            # Indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_published
                ON articles(published_at DESC)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_status
                ON articles(status)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_displayed
                ON articles(displayed_at DESC)
            ''')

            conn.commit()
            conn.close()

            logger.debug("Database schema initialized")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise CacheError(f"Database initialization failed: {e}")

    def add_articles(self, articles: List[Article]) -> int:
        """
        Add articles to cache

        Args:
            articles: List of Article objects

        Returns:
            Number of articles added (excluding duplicates)
        """
        if not articles:
            return 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            added_count = 0
            for article in articles:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO articles
                        (id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                         displayed_at, display_count, is_favorite, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.id,
                        article.feed_id,
                        article.title,
                        article.link,
                        article.content,
                        article.summary,
                        article.summary_en,
                        article.published_at,
                        article.created_at,
                        article.displayed_at,
                        article.display_count,
                        article.is_favorite,
                        article.status.value if isinstance(article.status, ArticleStatus) else article.status
                    ))
                    added_count += 1

                except sqlite3.IntegrityError:
                    # Article already exists, skip
                    pass

            conn.commit()
            conn.close()

            logger.info(f"Added {added_count}/{len(articles)} articles to cache")

            # Cleanup if needed
            self._cleanup_if_needed()

            # Update backup
            self._update_backup()

            return added_count

        except sqlite3.Error as e:
            logger.error(f"Failed to add articles: {e}")
            raise CacheError(f"Failed to add articles: {e}")

    def get_article(self, article_id: int) -> Optional[Article]:
        """
        Get article by ID

        Args:
            article_id: Article ID

        Returns:
            Article object or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                       displayed_at, display_count, is_favorite, status
                FROM articles
                WHERE id = ?
            ''', (article_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_article(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            return None

    def get_undisplayed_articles(self, limit: int = 50) -> List[Article]:
        """
        Get articles that haven't been displayed yet

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of Article objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                       displayed_at, display_count, is_favorite, status
                FROM articles
                WHERE status = 'new'
                ORDER BY published_at DESC, created_at DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            articles = [self._row_to_article(row) for row in rows]
            logger.debug(f"Found {len(articles)} undisplayed articles")
            return articles

        except sqlite3.Error as e:
            logger.error(f"Failed to get undisplayed articles: {e}")
            return []

    def get_recent_articles(self, limit: int = 50, days: int = None) -> List[Article]:
        """
        Get recent articles

        Args:
            limit: Maximum number of articles to return
            days: Only return articles from last N days

        Returns:
            List of Article objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute('''
                    SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                           displayed_at, display_count, is_favorite, status
                    FROM articles
                    WHERE published_at >= ?
                    ORDER BY published_at DESC, created_at DESC
                    LIMIT ?
                ''', (cutoff_date, limit))
            else:
                cursor.execute('''
                    SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                           displayed_at, display_count, is_favorite, status
                    FROM articles
                    ORDER BY published_at DESC, created_at DESC
                    LIMIT ?
                ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            articles = [self._row_to_article(row) for row in rows]
            logger.debug(f"Found {len(articles)} recent articles")
            return articles

        except sqlite3.Error as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []

    def get_random_displayed_article(self) -> Optional[Article]:
        """
        Get a random article that has been displayed before

        Returns:
            Article object or None if no displayed articles
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                       displayed_at, display_count, is_favorite, status
                FROM articles
                WHERE status != 'new'
                ORDER BY RANDOM()
                LIMIT 1
            ''')

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_article(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to get random article: {e}")
            return None

    def get_articles_by_display_time(self, limit: int = 50, days: int = None) -> List[Article]:
        """
        Get articles sorted by displayed_at (oldest first for round-robin)

        Args:
            limit: Maximum number of articles to return
            days: Only return articles from last N days (None for all time)

        Returns:
            List of Article objects sorted by displayed_at ASC (oldest first)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute('''
                    SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                           displayed_at, display_count, is_favorite, status
                    FROM articles
                    WHERE published_at >= ?
                    ORDER BY
                        CASE WHEN displayed_at IS NULL THEN 0 ELSE 1 END,
                        displayed_at ASC
                    LIMIT ?
                ''', (cutoff_date, limit))
            else:
                cursor.execute('''
                    SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                           displayed_at, display_count, is_favorite, status
                    FROM articles
                    ORDER BY
                        CASE WHEN displayed_at IS NULL THEN 0 ELSE 1 END,
                        displayed_at ASC
                    LIMIT ?
                ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            articles = [self._row_to_article(row) for row in rows]
            logger.debug(f"Found {len(articles)} articles by display time")
            return articles

        except sqlite3.Error as e:
            logger.error(f"Failed to get articles by display time: {e}")
            return []

    def get_random_article(self) -> Optional[Article]:
        """
        Get a completely random article

        Returns:
            Article object or None if no articles
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, feed_id, title, link, content, summary, summary_en, published_at, created_at,
                       displayed_at, display_count, is_favorite, status
                FROM articles
                ORDER BY RANDOM()
                LIMIT 1
            ''')

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_article(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Failed to get random article: {e}")
            return None

    def mark_as_displayed(self, article_id: int) -> bool:
        """
        Mark article as displayed (更新显示时间，但不改变status以支持循环播放)

        Args:
            article_id: Article ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 只更新displayed_at和display_count，不改变status
            # 这样可以实现循环播放，同时记录显示时间
            cursor.execute('''
                UPDATE articles
                SET displayed_at = ?,
                    display_count = display_count + 1
                WHERE id = ?
            ''', (datetime.now().isoformat(), article_id))

            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()

            if affected_rows > 0:
                logger.debug(f"Updated article {article_id} display time (count incremented)")
                # Update backup
                self._update_backup()
                return True

            return False

        except sqlite3.Error as e:
            logger.error(f"Failed to mark article as displayed: {e}")
            return False

    def mark_as_favorite(self, article_id: int) -> bool:
        """
        Mark article as favorite

        Args:
            article_id: Article ID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE articles
                SET is_favorite = 1,
                    status = 'favorite'
                WHERE id = ?
            ''', (article_id,))

            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()

            if affected_rows > 0:
                logger.debug(f"Marked article {article_id} as favorite")
                self._update_backup()
                return True

            return False

        except sqlite3.Error as e:
            logger.error(f"Failed to mark article as favorite: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total articles
            cursor.execute('SELECT COUNT(*) FROM articles')
            total_articles = cursor.fetchone()[0]

            # Undisplayed articles
            cursor.execute('SELECT COUNT(*) FROM articles WHERE status = "new"')
            undisplayed_count = cursor.fetchone()[0]

            # Favorite articles
            cursor.execute('SELECT COUNT(*) FROM articles WHERE is_favorite = 1')
            favorite_count = cursor.fetchone()[0]

            # Articles with summary
            cursor.execute('SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ""')
            with_summary_count = cursor.fetchone()[0]

            # Latest cached article
            cursor.execute('SELECT MAX(published_at) FROM articles')
            latest_published = cursor.fetchone()[0]

            conn.close()

            stats = {
                'total_articles': total_articles,
                'undisplayed_count': undisplayed_count,
                'displayed_count': total_articles - undisplayed_count,
                'favorite_count': favorite_count,
                'with_summary_count': with_summary_count,
                'latest_published': latest_published,
                'cache_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            }

            return stats

        except sqlite3.Error as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    def _cleanup_if_needed(self):
        """Clean up old articles if cache is full"""
        try:
            # Check current count
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM articles')
            count = cursor.fetchone()[0]

            if count > self.max_articles:
                logger.info(f"Cache full ({count} > {self.max_articles}), cleaning up...")

                # Delete oldest articles (excluding favorites)
                cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()

                cursor.execute('''
                    DELETE FROM articles
                    WHERE is_favorite = 0
                    AND published_at < ?
                    ORDER BY published_at ASC
                    LIMIT ?
                ''', (cutoff_date, count - self.max_articles))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Deleted {deleted_count} old articles")

            conn.close()

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup cache: {e}")

    def _update_backup(self):
        """Update JSON backup file"""
        try:
            articles = self.get_recent_articles(limit=self.max_articles)

            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'total_articles': len(articles),
                'articles': [article.to_dict() for article in articles]
            }

            with open(self.backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Backup updated: {len(articles)} articles")

        except Exception as e:
            logger.error(f"Failed to update backup: {e}")

    def restore_from_backup(self) -> int:
        """
        Restore articles from JSON backup

        Returns:
            Number of articles restored
        """
        if not os.path.exists(self.backup_path):
            logger.warning(f"Backup file not found: {self.backup_path}")
            return 0

        try:
            with open(self.backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            articles = [Article.from_dict(item) for item in backup_data.get('articles', [])]

            if articles:
                restored_count = self.add_articles(articles)
                logger.info(f"Restored {restored_count} articles from backup")
                return restored_count

            return 0

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return 0

    def _row_to_article(self, row) -> Article:
        """Convert database row to Article object"""
        return Article(
            id=row[0],
            feed_id=row[1],
            title=row[2],
            link=row[3],
            content=row[4],
            summary=row[5],
            summary_en=row[6],  # English summary
            published_at=row[7],
            created_at=row[8],
            displayed_at=row[9],
            display_count=row[10],
            is_favorite=bool(row[11]),
            status=ArticleStatus(row[12]) if row[12] else ArticleStatus.NEW
        )

    def clear(self):
        """Clear all cached data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM articles')
            cursor.execute('DELETE FROM feeds')

            conn.commit()
            conn.close()

            logger.info("Cache cleared")

            # Also remove backup
            if os.path.exists(self.backup_path):
                os.remove(self.backup_path)
                logger.info("Backup file removed")

        except sqlite3.Error as e:
            logger.error(f"Failed to clear cache: {e}")
            raise CacheError(f"Failed to clear cache: {e}")
