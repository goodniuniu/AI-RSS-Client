#!/usr/bin/env python3
"""
Configuration Management
配置管理模块

基于 DEVELOPMENT_GUIDE.md 第3章和第4章实现
"""

import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)


@dataclass
class DisplayConfig:
    """显示配置"""
    width: int
    height: int
    rotation: int
    font_file: str
    font_file_fallback: str
    font_size_title: int
    font_size_headline: int
    font_size_summary: int
    font_size_meta: int
    line_spacing: int
    margin: int
    title_height: int
    footer_height: int


@dataclass
class ServicesConfig:
    """内容获取服务配置"""
    enabled: bool
    interval_minutes: int
    max_articles_per_fetch: int
    daily_limit: int


@dataclass
class DisplaySchedulerConfig:
    """显示调度服务配置"""
    enabled: bool
    interval_minutes: int
    min_display_interval: int
    random_on_empty: bool
    mark_as_read_after_display: bool


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str
    logfile: str
    max_log_size: int
    backup_count: int


@dataclass
class NetworkConfig:
    """网络配置"""
    timeout_seconds: int
    retries: int
    retry_delay: int


class Config:
    """配置管理器

    基于 DEVELOPMENT_GUIDE.md 第3.1节实现
    支持从 YAML 文件加载配置，并提供类型安全的访问
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 "config.yml"
        """
        self.config_path = config_path or "config.yml"
        self._load()

    def _load(self):
        """加载并解析配置文件"""
        path = Path(self.config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {path.absolute()}\n"
                f"请确保 config.yml 文件存在且包含必需的配置节"
            )

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # 验证必需字段
            self._validate(data)

            # 映射到 Dataclass（类型安全）
            self.display = DisplayConfig(**data['display'])
            self.services = ServicesConfig(**data['services'])
            self.display_scheduler = DisplaySchedulerConfig(**data['display_scheduler'])
            self.logging = LoggingConfig(**data['logging'])
            self.network = NetworkConfig(**data['network'])

            logger.info(f"配置加载成功: {self.config_path}")

        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误: {e}")
            raise ValueError(f"配置文件格式错误: {e}")
        except TypeError as e:
            logger.error(f"配置字段类型错误: {e}")
            raise ValueError(f"配置文件包含无效的字段类型: {e}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    @staticmethod
    def _validate(data: Dict[str, Any]):
        """
        验证配置完整性

        Args:
            data: 配置数据字典

        Raises:
            ValueError: 如果缺少必需的配置节
        """
        required_sections = [
            'display',
            'services',
            'display_scheduler',
            'logging',
            'network'
        ]

        missing = [s for s in required_sections if s not in data]
        if missing:
            raise ValueError(
                f"配置文件缺少必需的节: {', '.join(missing)}\n"
                f"请参考 DEVELOPMENT_GUIDE.md 第4章的配置文件示例"
            )

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        加载配置的工厂方法

        Args:
            config_path: 可选的配置文件路径

        Returns:
            Config: 配置对象
        """
        return cls(config_path)


def setup_logging(config: Config) -> logging.Logger:
    """
    设置日志系统

    基于 DEVELOPMENT_GUIDE.md 第7.1节实现
    支持文件轮转和控制台输出

    Args:
        config: 配置对象

    Returns:
        logging.Logger: 配置好的根日志记录器
    """
    log_level = getattr(logging, config.logging.level.upper())
    log_file = config.logging.logfile

    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.logging.max_log_size,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"日志系统初始化完成 (级别: {config.logging.level})")
    logger.info(f"日志文件: {log_file}")

    return root_logger


# 测试代码
if __name__ == "__main__":
    import sys

    try:
        # 加载配置
        cfg = Config("config.yml")

        # 设置日志
        setup_logging(cfg)

        # 验证配置
        logger.info("=" * 60)
        logger.info("配置验证")
        logger.info("=" * 60)
        logger.info(f"显示分辨率: {cfg.display.width}x{cfg.display.height}")
        logger.info(f"字体文件: {cfg.display.font_file}")
        logger.info(f"字号设置: 标题={cfg.display.font_size_title}, "
                   f"正文={cfg.display.font_size_summary}")
        logger.info(f"内容获取间隔: {cfg.services.interval_minutes} 分钟")
        logger.info(f"显示更新间隔: {cfg.display_scheduler.interval_minutes} 分钟")
        logger.info(f"日志文件: {cfg.logging.logfile}")
        logger.info("=" * 60)

        print("✅ 配置模块测试通过")
        sys.exit(0)

    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        sys.exit(1)
