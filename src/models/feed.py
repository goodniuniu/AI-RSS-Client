"""
Feed data model for AI-RSS-Client
Corresponds to the Feed model in AI-RSS-Hub backend
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Feed:
    """
    Feed model representing an RSS source from AI-RSS-Hub

    Backend fields (from API):
    - id: Unique feed ID
    - name: Feed name
    - url: RSS feed URL
    - category: Feed category (e.g., 'tech', 'news')
    - is_active: Whether feed is actively being fetched
    - created_at: Database creation timestamp
    """
    id: int
    name: str
    url: str
    category: str
    is_active: bool
    created_at: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize feed data"""
        # Ensure name is not empty
        if not self.name or not self.name.strip():
            self.name = "Unnamed Feed"

        # Ensure URL is not empty
        if not self.url or not self.url.strip():
            self.url = "https://example.com/feed"

        # Ensure category is not empty
        if not self.category or not self.category.strip():
            self.category = "general"

    @property
    def display_name(self) -> str:
        """Get feed name for display"""
        return self.name

    @property
    def display_category(self) -> str:
        """Get formatted category for display"""
        return self.category.upper() if self.category else "GENERAL"

    def to_dict(self) -> dict:
        """Convert feed to dictionary (for JSON serialization)"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Feed':
        """Create Feed from dictionary (from API or cache)"""
        return cls(
            id=data['id'],
            name=data['name'],
            url=data['url'],
            category=data['category'],
            is_active=data['is_active'],
            created_at=data.get('created_at'),
        )

    @classmethod
    def from_api_response(cls, data: dict) -> 'Feed':
        """Create Feed from AI-RSS-Hub API response"""
        return cls(
            id=data['id'],
            name=data['name'],
            url=data['url'],
            category=data['category'],
            is_active=data['is_active'],
            created_at=data.get('created_at'),
        )

    def __repr__(self) -> str:
        """String representation of feed"""
        return f"Feed(id={self.id}, name='{self.name}', category={self.category}, active={self.is_active})"
