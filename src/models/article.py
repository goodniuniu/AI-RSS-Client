"""
Article data model for AI-RSS-Client
Corresponds to the Article model in AI-RSS-Hub backend
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class ArticleStatus(Enum):
    """Article display status"""
    NEW = "new"              # Never displayed
    DISPLAYED = "displayed"  # Has been displayed at least once
    FAVORITE = "favorite"    # Marked as favorite


@dataclass
class Article:
    """
    Article model representing a news article from AI-RSS-Hub

    Backend fields (from API):
    - id: Unique article ID
    - feed_id: ID of the RSS feed this article belongs to
    - title: Article title
    - link: URL to the original article
    - content: Full article content (optional)
    - summary: AI-generated summary (optional)
    - summary_en: AI-generated English summary (optional)
    - feed_name: RSS feed name (optional)
    - feed_category: RSS feed category (optional)
    - feed_url: RSS feed URL (optional)
    - published_at: Publication timestamp (optional)
    - created_at: Database creation timestamp

    Frontend fields (local):
    - displayed_at: Last time this article was displayed on e-paper
    - display_count: Number of times displayed
    - is_favorite: Whether user marked as favorite
    - status: Current display status
    """
    # Backend fields
    id: int
    feed_id: int
    title: str
    link: str
    content: Optional[str] = None
    summary: Optional[str] = None
    summary_en: Optional[str] = None  # 英文摘要
    feed_name: Optional[str] = None  # 来源名称
    feed_category: Optional[str] = None  # 来源分类
    feed_url: Optional[str] = None  # 来源RSS URL
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    qr_code_url: Optional[str] = None  # 二维码图片URL（相对路径）

    # Frontend fields (not from API)
    displayed_at: Optional[str] = None
    display_count: int = 0
    is_favorite: bool = False
    status: ArticleStatus = ArticleStatus.NEW

    def __post_init__(self):
        """Validate and normalize article data"""
        # Ensure title is not empty
        if not self.title or not self.title.strip():
            self.title = "Untitled Article"

        # Ensure link is not empty
        if not self.link or not self.link.strip():
            self.link = "https://example.com"

        # Parse and validate timestamps
        if self.created_at:
            try:
                # Try to parse ISO format timestamp
                datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                self.created_at = None

        if self.published_at:
            try:
                datetime.fromisoformat(self.published_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                self.published_at = None

    @property
    def display_title(self) -> str:
        """Get title for display (with truncation if too long)"""
        max_length = 100
        if len(self.title) > max_length:
            return self.title[:max_length] + "..."
        return self.title

    @property
    def display_content(self) -> str:
        """Get content for display (prefer summary over full content)"""
        # Prefer AI-generated summary
        if self.summary and self.summary.strip():
            return self.summary.strip()

        # Fall back to full content
        if self.content and self.content.strip():
            # Truncate if too long
            max_length = 500
            content = self.content.strip()
            if len(content) > max_length:
                return content[:max_length] + "..."
            return content

        # No content available
        return "No content available."

    @property
    def display_content_en(self) -> str:
        """Get English content for display"""
        # Prefer English summary
        if self.summary_en and self.summary_en.strip():
            return self.summary_en.strip()

        # Fall back to Chinese summary
        return self.display_content

    @property
    def display_date(self) -> str:
        """Get formatted date for display"""
        if self.published_at:
            try:
                dt = datetime.fromisoformat(self.published_at.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass

        if self.created_at:
            try:
                dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass

        return "Unknown date"

    @property
    def raw_publish_timestamp(self) -> Optional[str]:
        """原始发布时间戳（含时分秒），优先 published_at、回退 created_at。

        与 display_date 不同：保留完整时间，避免下游格式化时把时分误显示为 00:00。
        两者皆无时返回 None。
        """
        return self.published_at or self.created_at

    @property
    def is_read(self) -> bool:
        """Check if article has been displayed"""
        return self.status != ArticleStatus.NEW

    @property
    def has_content(self) -> bool:
        """Check if article has any content (summary or full)"""
        return bool(
            (self.summary and self.summary.strip()) or
            (self.content and self.content.strip())
        )

    def mark_as_displayed(self):
        """Mark article as displayed"""
        self.status = ArticleStatus.DISPLAYED
        self.displayed_at = datetime.now().isoformat()
        self.display_count += 1

    def mark_as_favorite(self):
        """Mark article as favorite"""
        self.is_favorite = True
        self.status = ArticleStatus.FAVORITE

    def to_dict(self) -> dict:
        """Convert article to dictionary (for JSON serialization)"""
        return {
            'id': self.id,
            'feed_id': self.feed_id,
            'title': self.title,
            'link': self.link,
            'content': self.content,
            'summary': self.summary,
            'summary_en': self.summary_en,
            'feed_name': self.feed_name,
            'feed_category': self.feed_category,
            'feed_url': self.feed_url,
            'published_at': self.published_at,
            'created_at': self.created_at,
            'qr_code_url': self.qr_code_url,
            'displayed_at': self.displayed_at,
            'display_count': self.display_count,
            'is_favorite': self.is_favorite,
            'status': self.status.value if isinstance(self.status, ArticleStatus) else self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Article':
        """Create Article from dictionary (from API or cache)"""
        # Extract backend fields
        article = cls(
            id=data['id'],
            feed_id=data['feed_id'],
            title=data['title'],
            link=data['link'],
            content=data.get('content'),
            summary=data.get('summary'),
            summary_en=data.get('summary_en'),
            feed_name=data.get('feed_name'),
            feed_category=data.get('feed_category'),
            feed_url=data.get('feed_url'),
            published_at=data.get('published_at'),
            created_at=data.get('created_at'),
            qr_code_url=data.get('qr_code_url'),
        )

        # Extract frontend fields if present
        if 'displayed_at' in data:
            article.displayed_at = data['displayed_at']
        if 'display_count' in data:
            article.display_count = data['display_count']
        if 'is_favorite' in data:
            article.is_favorite = data['is_favorite']
        if 'status' in data:
            # Handle both string and enum
            status_value = data['status']
            if isinstance(status_value, str):
                try:
                    article.status = ArticleStatus(status_value)
                except ValueError:
                    article.status = ArticleStatus.NEW
            else:
                article.status = status_value

        return article

    @classmethod
    def from_api_response(cls, data: dict) -> 'Article':
        """Create Article from AI-RSS-Hub API response"""
        return cls(
            id=data['id'],
            feed_id=data['feed_id'],
            title=data['title'],
            link=data['link'],
            content=data.get('content'),
            summary=data.get('summary'),
            summary_en=data.get('summary_en'),
            feed_name=data.get('feed_name'),
            feed_category=data.get('feed_category'),
            feed_url=data.get('feed_url'),
            published_at=data.get('published_at'),
            created_at=data.get('created_at'),
            qr_code_url=data.get('qr_code_url'),
        )

    def __repr__(self) -> str:
        """String representation of article"""
        return f"Article(id={self.id}, title='{self.title[:50]}...', status={self.status.value})"
