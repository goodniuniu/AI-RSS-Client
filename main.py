#!/usr/bin/env python3
"""
AI-RSS-Client Main Entry Point
墨水屏 RSS 阅读器 - 主启动入口

这是项目的启动入口，负责根据命令行参数启动相应的服务。
实际的业务逻辑在各个 Service 类中实现。
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.services import ContentManager, ContentFetchService, DisplayService
from src.fetchers import create_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_api_connection(base_url: str, api_token: str = None) -> bool:
    """测试API连接"""
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


def fetch_content_once(base_url: str, api_token: str = None, limit: int = 50) -> bool:
    """执行一次性内容获取"""
    print("Fetching content from API...")

    try:
        config = Config()

        client = create_client(base_url=base_url, api_token=api_token)
        content_manager = ContentManager(
            api_client=client,
            max_cached_articles=config.services.max_cached_articles,
            batch_size=config.services.max_articles_per_fetch,
            fetch_interval_minutes=config.services.interval_minutes,
            display_days=config.display_scheduler.display_days
        )

        # 根据配置选择获取策略
        if config.services.incremental_fetch:
            success = content_manager.fetch_incremental()
        elif config.services.fetch_feed_ids:
            success = False
            for feed_id in config.services.fetch_feed_ids:
                if content_manager.fetch_by_feed(feed_id):
                    success = True
        else:
            success = content_manager.fetch_and_process_content(
                days=config.services.fetch_days
            )

        if success:
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


def run_fetch_daemon(base_url: str, api_token: str = None, cycles: int = None) -> bool:
    """启动内容获取守护进程"""
    print("Starting Content Fetch Service...")

    try:
        config = Config()
        service = ContentFetchService(
            config=config,
            base_url=base_url,
            api_token=api_token
        )

        service.run_daemon(cycles=cycles)
        return True

    except Exception as e:
        print(f"\n✗ Content fetch service failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_display_daemon(base_url: str, api_token: str = None,
                       interval: float = 0.5, cycles: int = None,
                       test_only: bool = False) -> bool:
    """启动显示守护进程"""
    if test_only:
        print("Starting Display Service (TEST mode)...")
    else:
        print("Starting Display Service...")

    try:
        config = Config()
        service = DisplayService(
            config=config,
            base_url=base_url,
            api_token=api_token,
            display_interval_minutes=interval
        )

        if test_only:
            success = service.run_test_display()
            if success:
                print("\n✓ Test display completed")
            else:
                print("\n✗ Test display failed")
            return success
        else:
            service.run_daemon(cycles=cycles)
            return True

    except Exception as e:
        print(f"\n✗ Display service failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_status(base_url: str, api_token: str = None) -> bool:
    """显示系统状态"""
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
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='AI-RSS-Client - E-paper RSS Reader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Commands:
  test-api        Test API connection
  fetch           Fetch content once
  fetch-daemon    Start content fetch service (daemon)
  run             Start display service (alias for display-daemon)
  display-daemon  Start display service (daemon)
  status          Show system status
  test-display    Test e-paper display once

Examples:
  # Test API
  python main.py test-api

  # Fetch content once
  python main.py fetch

  # Start content fetch service (runs every 20 minutes)
  python main.py fetch-daemon

  # Start display service (updates every 30 seconds)
  python main.py run

  # Start display service with custom interval
  python main.py run --interval 1.0

  # Run for 5 test cycles
  python main.py run --cycles 5

  # Show status
  python main.py status

  # Test display hardware
  python main.py test-display

Services Architecture:
  - ContentFetchService:独立的内容获取进程
  - DisplayService:独立的显示进程
  - 两个服务可以独立运行、重启和监控
        """
    )

    parser.add_argument(
        'command',
        choices=[
            'test-api',
            'fetch',
            'fetch-daemon',
            'run',
            'display-daemon',
            'status',
            'test-display'
        ],
        help='Command to run'
    )

    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='AI-RSS-Hub API base URL (default: http://localhost:8000)')
    parser.add_argument('--api-token', default=None,
                       help='API token for protected endpoints')
    parser.add_argument('--interval', type=float, default=0.5,
                       help='Display interval in minutes (default: 0.5, i.e., 30 seconds)')
    parser.add_argument('--cycles', type=int, default=None,
                       help='Number of cycles (default: infinite)')
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
        success = fetch_content_once(args.base_url, args.api_token, args.limit)
        sys.exit(0 if success else 1)

    elif args.command == 'fetch-daemon':
        success = run_fetch_daemon(args.base_url, args.api_token, args.cycles)
        sys.exit(0 if success else 1)

    elif args.command in ['run', 'display-daemon']:
        success = run_display_daemon(
            args.base_url,
            args.api_token,
            args.interval,
            args.cycles,
            test_only=(args.command == 'test-display')
        )
        sys.exit(0 if success else 1)

    elif args.command == 'status':
        success = show_status(args.base_url, args.api_token)
        sys.exit(0 if success else 1)

    elif args.command == 'test-display':
        success = run_display_daemon(
            args.base_url,
            args.api_token,
            test_only=True
        )
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
