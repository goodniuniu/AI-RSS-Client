#!/usr/bin/env python3
"""
AI-RSS-Client Main Program
E-paper RSS reader frontend for AI-RSS-Hub
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config, setup_logging
from src.services import ContentManager, DisplayScheduler
from src.fetchers import create_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_api_connection(base_url: str, api_token: str = None):
    """Test API connection"""
    print("Testing API connection...")

    try:
        client = create_client(base_url=base_url, api_token=api_token)

        # Health check
        health = client.health_check()
        print(f"✓ Health check: {health.get('status')}")

        # Get status
        status = client.get_status()
        print(f"✓ System status: {status.get('status')}")
        print(f"  - Database: {status.get('database')}")
        print(f"  - LLM configured: {status.get('llm_configured')}")
        print(f"  - Fetch interval: {status.get('fetch_interval_hours')} hours")

        # Test article fetch
        articles = client.get_articles(limit=5)
        print(f"✓ Fetched {len(articles)} articles")
        if articles:
            print(f"  - Latest: {articles[0].display_title}")

        client.close()
        print("\n✓ API connection test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ API connection test FAILED: {e}")
        return False


def fetch_content(base_url: str, api_token: str = None, limit: int = 50):
    """Fetch content from API"""
    print("Fetching content from API...")

    try:
        client = create_client(base_url=base_url, api_token=api_token)
        content_manager = ContentManager(api_client=client)

        # Fetch articles
        success = content_manager.fetch_and_process_content()

        if success:
            # Show status
            stats = content_manager.get_status()
            print(f"\n✓ Content fetched successfully")
            print(f"  - Total summaries: {stats.get('total_summaries')}")
            print(f"  - Undisplayed: {stats.get('undisplayed_count')}")
            print(f"  - API connected: {stats.get('api_connected')}")
        else:
            print("\n✗ Content fetch failed")

        content_manager.close()
        return success

    except Exception as e:
        print(f"\n✗ Failed to fetch content: {e}")
        return False


def run_display(base_url: str, api_token: str = None, interval: int = 1,
                cycles: int = None, test_only: bool = False):
    """Run display scheduler"""
    print("Starting display scheduler...")

    try:
        # Create components
        client = create_client(base_url=base_url, api_token=api_token)
        content_manager = ContentManager(api_client=client)
        scheduler = DisplayScheduler(
            content_manager=content_manager,
            display_interval_minutes=interval
        )

        if test_only:
            # Run test display
            print("\nRunning TEST display only...")
            scheduler.test_display()
            print("\n✓ Test display completed")
        else:
            # Run full scheduler
            if cycles:
                print(f"\nRunning for {cycles} display cycles...")
            else:
                print("\nRunning indefinitely (press Ctrl+C to stop)...")

            scheduler.run_daemon(cycles=cycles)

        scheduler.close()
        return True

    except Exception as e:
        print(f"\n✗ Display scheduler failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_status(base_url: str, api_token: str = None):
    """Show system status"""
    print("AI-RSS-Client Status\n" + "=" * 50)

    try:
        client = create_client(base_url=base_url, api_token=api_token)
        content_manager = ContentManager(api_client=client)

        # API status
        print("\n[API Connection]")
        if client.test_connection():
            print("✓ API: Connected")
            status = client.get_status()
            print(f"  Status: {status.get('status')}")
            print(f"  Database: {status.get('database')}")
        else:
            print("✗ API: Disconnected")

        # Cache status
        print("\n[Cache]")
        cache_stats = content_manager.cache.get_stats()
        print(f"  Total articles: {cache_stats.get('total_articles', 0)}")
        print(f"  Undisplayed: {cache_stats.get('undisplayed_count', 0)}")
        print(f"  With summary: {cache_stats.get('with_summary_count', 0)}")
        print(f"  Favorites: {cache_stats.get('favorite_count', 0)}")
        print(f"  Latest: {cache_stats.get('latest_published', 'N/A')}")

        # Content manager status
        print("\n[Content Manager]")
        cm_status = content_manager.get_status()
        print(f"  Last fetch: {cm_status.get('last_fetch_time', 'Never')}")
        print(f"  Last count: {cm_status.get('last_fetch_count', 0)}")
        print(f"  Fetch interval: {cm_status.get('fetch_interval_minutes')} minutes")

        print("\n" + "=" * 50)

        content_manager.close()
        return True

    except Exception as e:
        print(f"\n✗ Failed to get status: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AI-RSS-Client - E-paper RSS Reader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test API connection
  python main.py test-api

  # Fetch content from API
  python main.py fetch

  # Run display scheduler (1 minute intervals)
  python main.py run

  # Run for 5 test cycles
  python main.py run --cycles 5

  # Show status
  python main.py status

  # Test display hardware
  python main.py test-display
        """
    )

    parser.add_argument('command', choices=['test-api', 'fetch', 'run', 'status', 'test-display'],
                       help='Command to run')

    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='AI-RSS-Hub API base URL (default: http://localhost:8000)')
    parser.add_argument('--api-token', default=None,
                       help='API token for protected endpoints')
    parser.add_argument('--interval', type=float, default=0.5,
                       help='Display interval in minutes (default: 0.5, i.e., 30 seconds)')
    parser.add_argument('--cycles', type=int, default=None,
                       help='Number of display cycles (default: infinite)')
    parser.add_argument('--limit', type=int, default=50,
                       help='Number of articles to fetch (default: 50)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Execute command
    if args.command == 'test-api':
        success = test_api_connection(args.base_url, args.api_token)
        sys.exit(0 if success else 1)

    elif args.command == 'fetch':
        success = fetch_content(args.base_url, args.api_token, args.limit)
        sys.exit(0 if success else 1)

    elif args.command == 'run':
        success = run_display(args.base_url, args.api_token, args.interval, args.cycles)
        sys.exit(0 if success else 1)

    elif args.command == 'status':
        success = show_status(args.base_url, args.api_token)
        sys.exit(0 if success else 1)

    elif args.command == 'test-display':
        success = run_display(args.base_url, args.api_token, test_only=True)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
