# AI-RSS-Client 墨水屏开发指引

> 基于现有三个墨水屏服务项目的最佳实践总结

**参考项目：**
- `epaper-with-ai-news` - AI 新闻墨水屏显示
- `epaper-with-raspberrypi` - 天气与诗词墨水屏显示

**文档版本：** 1.1
**创建时间：** 2025-12-26
**最后更新：** 2025-12-26 16:45（新增故障排查指南）
**适用墨水屏：** Waveshare 3.52 英寸 (240×360)

---

## 📋 目录

1. [项目架构设计](#1-项目架构设计)
2. [目录结构规范](#2-目录结构规范)
3. [核心模块设计](#3-核心模块设计)
4. [配置管理最佳实践](#4-配置管理最佳实践)
5. [服务化部署](#5-服务化部署)
6. [墨水屏显示规范](#6-墨水屏显示规范)
7. [错误处理与日志](#7-错误处理与日志)
8. [开发工作流](#8-开发工作流)
9. [墨水屏故障排查指南](#11-墨水屏故障排查指南) ⭐ 新增

---

## 1. 项目架构设计

### 1.1 解耦的服务架构

参考 `ai-news` 项目的成功实践，采用**内容获取**和**显示调度**分离的架构：

```
┌─────────────────────────────────────┐
│   Content Fetch Service             │
│   (内容获取服务)                     │
│                                      │
│   - 定时抓取 RSS                     │
│   - 内容处理和缓存                   │
│   - 独立运行，不阻塞显示             │
└─────────────────────────────────────┘
              ↓
        [共享数据存储]
              ↓
┌─────────────────────────────────────┐
│   Display Scheduler Service         │
│   (显示调度服务)                     │
│                                      │
│   - 定时更新墨水屏                   │
│   - 从缓存读取内容                   │
│   - 管理显示状态                     │
└─────────────────────────────────────┘
```

**优势：**
- 内容获取失败不影响显示
- 可以独立调整刷新频率
- 便于调试和维护
- 支持离线模式

### 1.2 服务配置参考

**Content Fetch Service**
```python
# 配置参数
interval_minutes: 10-20    # 内容获取间隔
enabled: true              # 是否启用
max_articles_per_fetch: 50 # 每次获取最大文章数
```

**Display Scheduler Service**
```python
# 配置参数
interval_minutes: 1-5      # 显示更新间隔
min_display_interval: 30   # 最小显示间隔（秒）
random_on_empty: true      # 内容为空时随机显示
```

---

## 2. 目录结构规范

### 2.1 推荐的目录结构

```
ai-rss-client/
├── config.yml                 # 主配置文件
├── README.md                  # 项目说明
├── requirements.txt           # Python 依赖
├── install.sh                 # 安装脚本
│
├── src/                       # 源代码目录
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── main.py                # 主程序入口
│   │
│   ├── models/                # 数据模型
│   │   ├── __init__.py
│   │   └── rss_models.py      # RSS 数据模型
│   │
│   ├── fetchers/              # 内容获取
│   │   ├── __init__.py
│   │   ├── rss_fetcher.py     # RSS 抓取器
│   │   └── api_client.py      # API 客户端
│   │
│   ├── processors/            # 内容处理
│   │   ├── __init__.py
│   │   ├── content_processor.py
│   │   └── cache_manager.py   # 缓存管理
│   │
│   ├── display/               # 显示相关
│   │   ├── __init__.py
│   │   ├── epaper_driver.py   # 墨水屏驱动封装
│   │   ├── layout_engine.py   # 布局引擎
│   │   ├── renderer.py        # 渲染器
│   │   └── fonts.py           # 字体管理
│   │
│   ├── services/              # 服务层
│   │   ├── __init__.py
│   │   ├── content_fetch_service.py
│   │   └── display_scheduler_service.py
│   │
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       ├── logger.py          # 日志工具
│       └── helpers.py
│
├── scripts/                   # 脚本目录
│   ├── content_fetch_service.py
│   ├── display_scheduler_service.py
│   ├── install.sh
│   └── status.sh              # 状态检查脚本
│
├── lib/                       # 第三方库
│   └── waveshare_epd/         # 墨水屏驱动库
│       ├── __init__.py
│       ├── epd3in52.py
│       └── epdconfig.py
│
├── data/                      # 数据目录
│   ├── cache/                 # 缓存文件
│   │   └── articles.json
│   └── logs/                  # 日志文件
│       └── service.log
│
├── tests/                     # 测试代码
│   ├── test_epaper.py
│   └── test_renderer.py
│
└── systemd/                   # Systemd 服务文件
    ├── ai-rss-content-fetch.service
    ├── ai-rss-display-scheduler.service
    └── ai-rss-content-fetch.timer
```

### 2.2 模块化设计原则

**参考项目实践：**

1. **配置模块** (`config.py`)
   - 使用 `dataclass` 定义配置结构
   - 支持从 YAML 文件加载
   - 环境变量覆盖支持

2. **显示模块** (`display/`)
   - `epaper_driver.py`: 封装硬件操作
   - `layout_engine.py`: 处理布局逻辑
   - `renderer.py`: 实际的图像渲染

3. **服务模块** (`services/`)
   - 每个服务独立运行
   - 支持守护进程和单次运行模式
   - 统一的启动参数

---

## 3. 核心模块设计

### 3.1 配置管理模块

**参考实现：** `epaper-with-ai-news/src/config.py`

```python
from dataclasses import dataclass
from pathlib import Path
import yaml

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
    """服务配置"""
    enabled: bool
    interval_minutes: int
    max_articles_per_fetch: int = 50

class Config:
    """配置管理器"""

    def __init__(self, config_path: str = None):
        config_path = config_path or "config.yml"
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        self.display = DisplayConfig(**config_data['display'])
        self.services = ServicesConfig(**config_data['services'])
        # ... 其他配置

    @staticmethod
    def setup_logging(config):
        """设置日志"""
        # ... 日志配置
```

**最佳实践：**
- ✅ 使用 `dataclass` 类型安全
- ✅ 配置分层管理
- ✅ 提供默认值
- ✅ 支持 YAML 配置文件

### 3.2 墨水屏驱动模块

**参考实现：** `epaper-with-ai-news/src/epaper_driver.py`

```python
import sys
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class EpaperDriver:
    """墨水屏驱动封装"""

    def __init__(self, lib_path: str = None):
        self.lib_path = Path(lib_path or "lib/waveshare_epd")
        self.epd = None
        self.is_initialized = False

        # 添加库路径
        if self.lib_path.exists():
            sys.path.insert(0, str(self.lib_path))

    def init_display(self) -> bool:
        """初始化显示器"""
        try:
            from waveshare_epd import epd3in52

            self.epd = epd3in52.EPD()
            self.epd.init()
            self.is_initialized = True

            logger.info("墨水屏初始化成功")
            return True

        except Exception as e:
            logger.error(f"墨水屏初始化失败: {e}")
            return False

    def display_image(self, image: Image.Image) -> bool:
        """显示图像"""
        if not self.is_initialized:
            logger.error("显示器未初始化")
            return False

        try:
            self.epd.display(self.epd.getbuffer(image))
            logger.info("图像显示成功")
            return True

        except Exception as e:
            logger.error(f"图像显示失败: {e}")
            return False

    def clear(self):
        """清屏"""
        if self.is_initialized and self.epd:
            self.epd.init()

    def sleep(self):
        """进入睡眠模式"""
        if self.is_initialized and self.epd:
            self.epd.sleep()

    def __del__(self):
        """析构时清理"""
        if self.epd:
            self.epd.sleep()
```

**最佳实践：**
- ✅ 封装底层硬件操作
- ✅ 统一的错误处理
- ✅ 自动资源管理 (`__del__`)
- ✅ 日志记录关键操作

### 3.3 布局引擎模块

**参考实现：** `epaper-with-ai-news/src/layout.py`

```python
from dataclasses import dataclass
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont

@dataclass
class LayoutRegion:
    """布局区域"""
    x: int
    y: int
    width: int
    height: int

    def get_center(self) -> Tuple[int, int]:
        """获取中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)

class LayoutEngine:
    """布局引擎"""

    def __init__(self, config):
        self.config = config
        self.display = config.display

        # 加载字体
        self.title_font = self._load_font(
            self.display.font_file,
            self.display.font_size_title
        )
        self.headline_font = self._load_font(
            self.display.font_file,
            self.display.font_size_headline
        )
        # ... 其他字体

        # 定义布局区域
        self._setup_regions()

    def _load_font(self, font_path: str, font_size: int):
        """加载字体（带回退）"""
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception as e:
            logger.warning(f"字体加载失败: {e}")
            # 尝试回退字体
            try:
                return ImageFont.truetype(
                    self.display.font_file_fallback,
                    font_size
                )
            except:
                return ImageFont.load_default()

    def _setup_regions(self):
        """设置布局区域"""
        margin = self.display.margin

        # Header 区域
        self.header_region = LayoutRegion(
            x=margin,
            y=margin,
            width=self.display.width - 2 * margin,
            height=self.display.title_height
        )

        # Content 区域
        self.content_region = LayoutRegion(
            x=margin,
            y=self.display.title_height + margin,
            width=self.display.width - 2 * margin,
            height=self.display.height -
                   self.display.title_height -
                   self.display.footer_height -
                   2 * margin
        )

        # Footer 区域
        self.footer_region = LayoutRegion(
            x=margin,
            y=self.display.height - self.display.footer_height - margin,
            width=self.display.width - 2 * margin,
            height=self.display.footer_height
        )

    def wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """自动换行"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test = ' '.join(current_line + [word])
            if font.getlength(test) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines
```

**最佳实践：**
- ✅ 区域化布局管理
- ✅ 字体加载带回退机制
- ✅ 自动换行算法
- ✅ 使用 `font.getlength()` 精确测量

### 3.4 服务模块

**参考实现：** `epaper-with-ai-news/scripts/display_scheduler_service.py`

```python
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display_scheduler import DisplayScheduler

logger = logging.getLogger(__name__)

class DisplaySchedulerService:
    """显示调度服务"""

    def __init__(self, config_path: str = None):
        self.config = Config(config_path)
        self.display_scheduler = DisplayScheduler(self.config)

        # 服务配置
        self.interval_minutes = self.config.display_scheduler.interval_minutes
        self.min_display_interval = self.config.display_scheduler.min_display_interval
        self.enabled = self.config.display_scheduler.enabled

        logger.info(f"服务初始化完成 (间隔: {self.interval_minutes} 分钟)")

    def run_once(self) -> bool:
        """运行一次更新"""
        if not self.enabled:
            logger.info("服务已禁用")
            return False

        try:
            logger.info(f"开始更新周期: {datetime.now().isoformat()}")
            success = self.display_scheduler.update_display(save_debug=False)

            if success:
                logger.info("显示更新成功")
            else:
                logger.warning("显示更新周期完成，但无内容变更")

            return success

        except Exception as e:
            logger.error(f"显示更新失败: {e}")
            return False

    def run_daemon(self):
        """以守护进程方式运行"""
        if not self.enabled:
            logger.info("服务已禁用，退出")
            return

        logger.info("启动显示调度守护进程")
        logger.info(f"每 {self.interval_minutes} 分钟更新一次显示")

        try:
            while True:
                start_time = time.time()

                # 运行更新周期
                self.run_once()

                # 计算睡眠时间
                cycle_time = time.time() - start_time
                sleep_time = max(
                    self.min_display_interval,
                    (self.interval_minutes * 60) - cycle_time
                )

                logger.info(f"下次更新在 {int(sleep_time)} 秒后")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("服务被用户中断")
        except Exception as e:
            logger.error(f"服务崩溃: {e}")
            raise

def main():
    """主函数"""
    try:
        # 设置日志
        config = Config()
        setup_logging(config)

        # 创建并运行服务
        service = DisplaySchedulerService()

        if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
            # 守护进程模式
            service.run_daemon()
        else:
            # 单次运行
            success = service.run_once()
            sys.exit(0 if success else 1)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**最佳实践：**
- ✅ 支持守护进程和单次运行模式
- ✅ 智能的睡眠时间计算
- ✅ 优雅的异常处理
- ✅ 详细的日志记录
- ✅ 命令行参数支持

---

## 4. 配置管理最佳实践

### 4.1 YAML 配置文件示例

```yaml
# config.yml

display:
  width: 240
  height: 360
  rotation: 0
  font_file: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
  font_file_fallback: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
  font_size_title: 18
  font_size_headline: 16
  font_size_summary: 15
  font_size_meta: 9
  line_spacing: 1
  margin: 6
  title_height: 35
  footer_height: 20

services:
  enabled: true
  interval_minutes: 10
  max_articles_per_fetch: 50
  daily_limit: 300

display_scheduler:
  enabled: true
  interval_minutes: 1
  min_display_interval: 30
  random_on_empty: true
  mark_as_read_after_display: true

logging:
  level: "INFO"
  logfile: "data/logs/service.log"
  max_log_size: 10485760  # 10MB
  backup_count: 5

network:
  timeout_seconds: 10
  retries: 3
  retry_delay: 5
```

### 4.2 配置加载和验证

```python
from pathlib import Path
import yaml
from typing import Optional

class Config:
    """配置管理器"""

    @staticmethod
    def load(config_path: Optional[str] = None) -> 'Config':
        """加载配置"""
        config_path = config_path or "config.yml"

        if not Path(config_path).exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        # 验证必需的配置节
        Config._validate(config_data)

        return Config(config_data)

    @staticmethod
    def _validate(config_data: dict):
        """验证配置"""
        required_sections = ['display', 'services', 'logging']
        for section in required_sections:
            if section not in config_data:
                raise ValueError(f"缺少配置节: {section}")

    def __init__(self, config_data: dict):
        # ... 初始化配置对象
```

---

## 5. 服务化部署

### 5.1 Systemd 服务文件

**参考：** `ai-news-display-scheduler.service`

```ini
[Unit]
Description=AI-RSS Display Scheduler Service
Documentation=https://github.com/ai-rss-client
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/scripts/display_scheduler_service.py --daemon
WorkingDirectory=/path/to/project
User=admin
Group=admin
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-rss-display-scheduler

# 安全设置
ReadWritePaths=/var/log /tmp /path/to/project
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

### 5.2 服务管理脚本

```bash
#!/bin/bash
# install.sh

PROJECT_DIR="/home/admin/Github/AI-RSS-Client"
SERVICES=(
    "ai-rss-content-fetch.service"
    "ai-rss-display-scheduler.service"
)

echo "安装 AI-RSS-Client 服务..."

# 停止现有服务
for service in "${SERVICES[@]}"; do
    sudo systemctl stop "$service" 2>/dev/null || true
done

# 复制服务文件
for service in "${SERVICES[@]}"; do
    sudo cp "systemd/$service" /etc/systemd/system/
    sudo chmod 644 "/etc/systemd/system/$service"
done

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
for service in "${SERVICES[@]}"; do
    sudo systemctl enable "$service"
    echo "✅ 已启用服务: $service"
done

# 启动服务
for service in "${SERVICES[@]}"; do
    sudo systemctl start "$service"
    echo "✅ 已启动服务: $service"
done

echo "安装完成！"
echo "使用以下命令查看状态："
echo "  sudo systemctl status ai-rss-display-scheduler.service"
```

### 5.3 服务管理最佳实践

**启动和停止服务：**
```bash
# 启动所有服务
sudo systemctl start ai-rss-*

# 停止所有服务
sudo systemctl stop ai-rss-*

# 重启服务
sudo systemctl restart ai-rss-display-scheduler.service

# 查看状态
sudo systemctl status ai-rss-*
```

**查看日志：**
```bash
# 实时查看服务日志
sudo journalctl -u ai-rss-display-scheduler.service -f

# 查看最近 100 行
sudo journalctl -u ai-rss-display-scheduler.service -n 100

# 查看日志文件
tail -f data/logs/service.log
```

**调试模式：**
```bash
# 直接运行（不使用 systemd）
/path/to/venv/bin/python scripts/display_scheduler_service.py

# 单次运行
/path/to/venv/bin/python scripts/display_scheduler_service.py
```

---

## 6. 墨水屏显示规范

### 6.1 显示参数建议

基于 `docs/EPAPER_QUICK_GUIDE.md` 的实践经验：

```python
# 3.52 英寸墨水屏 (240×360) 最佳参数

DISPLAY_CONFIG = {
    # 字号设置
    'title_size': 18,        # 标题
    'headline_size': 16,     # 小标题
    'summary_size': 15,      # 正文
    'meta_size': 9,          # 元数据（时间、来源）

    # 布局
    'margin': 6,             # 边距（4-8px）
    'line_spacing': 1,       # 行间距（1-2px）

    # 区域高度
    'header_height': 35,     # 标题区域
    'footer_height': 20,     # 页脚区域

    # 刷新策略
    'min_refresh_interval': 30,   # 最小刷新间隔（秒）
    'max_refresh_interval': 300,  # 最大刷新间隔（秒）
}
```

### 6.2 文本渲染最佳实践

**自动换行：**
```python
def wrap_text(text: str, font, max_width: int) -> List[str]:
    """智能换行"""
    # 使用 font.getlength() 精确测量
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test = ' '.join(current_line + [word])
        if font.getlength(test) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines
```

**文本截断：**
```python
def truncate_text(text: str, font, max_width: int, suffix="...") -> str:
    """截断超长文本"""
    if font.getlength(text) <= max_width:
        return text

    while text and font.getlength(text + suffix) > max_width:
        text = text[:-1]

    return text + suffix
```

**单色模式：**
```python
# 创建图像（1位模式，白色背景）
image = Image.new('1', (width, height), 1)
draw = ImageDraw.Draw(image)

BLACK = 0
WHITE = 1

# 只用纯色
draw.text((x, y), "Text", fill=BLACK, font=font)
```

---

## 7. 错误处理与日志

### 7.1 统一的日志设置

**参考实现：** `epaper-with-ai-news/src/config.py`

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(config):
    """设置日志系统"""
    log_level = getattr(logging, config.logging.level.upper())
    log_file = config.logging.logfile

    # 创建日志目录
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.logging.max_log_size,
        backupCount=config.logging.backup_count
    )
    file_handler.setLevel(log_level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### 7.2 错误处理模式

**服务级错误处理：**
```python
def run_daemon(self):
    """守护进程运行"""
    logger.info("启动服务守护进程")

    try:
        while True:
            try:
                # 执行服务逻辑
                self.run_once()

            except Exception as e:
                # 单次循环的错误不应终止整个服务
                logger.error(f"运行周期失败: {e}")
                # 继续运行，等待下一个周期

            # 休眠
            time.sleep(self.interval_minutes * 60)

    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.critical(f"服务崩溃: {e}")
        raise
```

**模块级错误处理：**
```python
def display_image(self, image: Image.Image) -> bool:
    """显示图像"""
    try:
        if not self.is_initialized:
            raise RuntimeError("显示器未初始化")

        self.epd.display(self.epd.getbuffer(image))
        logger.info("图像显示成功")
        return True

    except Exception as e:
        logger.error(f"图像显示失败: {e}")
        return False
```

---

## 8. 开发工作流

### 8.1 开发环境设置

```bash
# 1. 克隆项目
cd /home/admin/Github/AI-RSS-Client

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置文件
cp config.yml.example config.yml
# 编辑 config.yml

# 5. 测试墨水屏
sudo venv/bin/python tests/test_epaper.py
```

### 8.2 调试工作流

```bash
# 1. 停止所有服务
sudo systemctl stop ai-rss-*

# 2. 直接运行服务（查看实时输出）
venv/bin/python scripts/display_scheduler_service.py

# 3. 查看日志
tail -f data/logs/service.log

# 4. 测试完成后恢复服务
sudo systemctl start ai-rss-*
```

### 8.3 测试流程

```bash
# 1. 软件模式测试（仅生成图像）
venv/bin/python tests/test_epaper.py

# 2. 硬件模式测试（需要 sudo）
sudo venv/bin/python tests/test_epaper_hardware.py

# 3. 服务集成测试
sudo systemctl start ai-rss-display-scheduler.service
sudo journalctl -u ai-rss-display-scheduler.service -f
```

### 8.4 部署流程

```bash
# 1. 安装服务和依赖
sudo ./install.sh

# 2. 验证服务状态
sudo systemctl status ai-rss-*

# 3. 查看服务日志
sudo journalctl -u ai-rss-display-scheduler.service -n 50

# 4. 测试显示更新
sudo systemctl restart ai-rss-display-scheduler.service
```

---

## 9. 代码示例集合

### 9.1 完整的服务模板

**Display Scheduler Service 模板：**

```python
#!/usr/bin/env python3
"""
Display Scheduler Service Template
显示调度服务模板
"""

import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.display_scheduler import DisplayScheduler

logger = logging.getLogger(__name__)

class DisplaySchedulerService:
    """显示调度服务"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = Config(config_path)
        self.display_scheduler = DisplayScheduler(self.config)

        # 服务配置
        self.interval_minutes = self.config.display_scheduler.interval_minutes
        self.min_display_interval = self.config.display_scheduler.min_display_interval
        self.enabled = self.config.display_scheduler.enabled

        logger.info(f"显示调度服务初始化完成")
        logger.info(f"更新间隔: {self.interval_minutes} 分钟")
        logger.info(f"最小间隔: {self.min_display_interval} 秒")
        logger.info(f"启用状态: {self.enabled}")

    def run_once(self) -> bool:
        """运行一次显示更新"""
        if not self.enabled:
            logger.info("服务已禁用")
            return False

        try:
            logger.info(f"开始更新周期: {datetime.now().isoformat()}")
            success = self.display_scheduler.update_display()

            if success:
                logger.info("✅ 显示更新成功")
            else:
                logger.warning("⚠️ 显示更新完成，但无内容变更")

            return success

        except Exception as e:
            logger.error(f"❌ 显示更新失败: {e}", exc_info=True)
            return False

    def run_daemon(self):
        """以守护进程方式运行"""
        if not self.enabled:
            logger.info("服务已禁用，退出")
            return

        logger.info("=" * 60)
        logger.info("启动显示调度守护进程")
        logger.info("=" * 60)
        logger.info(f"更新间隔: {self.interval_minutes} 分钟")

        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                logger.info(f"\n=== 周期 #{cycle_count} ===")

                start_time = time.time()

                # 运行更新周期
                self.run_once()

                # 计算睡眠时间
                cycle_time = time.time() - start_time
                sleep_time = max(
                    self.min_display_interval,
                    (self.interval_minutes * 60) - cycle_time
                )

                logger.info(f"下次更新在 {int(sleep_time/60)} 分 {int(sleep_time%60)} 秒后")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("\n服务被用户中断 (Ctrl+C)")
        except Exception as e:
            logger.critical(f"服务崩溃: {e}", exc_info=True)
            raise

def main():
    """主函数"""
    try:
        # 设置日志
        config = Config()
        setup_logging(config)

        # 创建并运行服务
        service = DisplaySchedulerService()

        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == '--daemon':
                # 守护进程模式
                service.run_daemon()
            elif command == '--once':
                # 单次运行
                success = service.run_once()
                sys.exit(0 if success else 1)
            else:
                print(f"未知命令: {command}")
                print("用法:")
                print("  --daemon  以守护进程方式运行")
                print("  --once    单次运行")
                sys.exit(1)
        else:
            # 默认：单次运行
            success = service.run_once()
            sys.exit(0 if success else 1)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 10. 常见问题和解决方案

### 10.1 GPIO 占用问题

**问题：** `OSError: [Errno 16] Device or resource busy`

**解决方案：**
```bash
# 1. 查找占用进程
sudo ps aux | grep -E "epaper|weather|news"

# 2. 停止相关服务
sudo systemctl stop ai-rss-* weather-poetry-display.service

# 3. 或直接终止进程
sudo kill -9 <PID>
```

### 10.2 字体加载失败

**问题：** 字体文件不存在或加载失败

**解决方案：**
```python
# 使用回退字体
def load_font(primary_path: str, fallback_path: str, size: int):
    try:
        return ImageFont.truetype(primary_path, size)
    except:
        try:
            return ImageFont.truetype(fallback_path, size)
        except:
            return ImageFont.load_default()
```

### 10.3 服务不更新

**问题：** 服务运行但墨水屏不更新

**检查步骤：**
```bash
# 1. 检查服务状态
sudo systemctl status ai-rss-display-scheduler.service

# 2. 查看服务日志
sudo journalctl -u ai-rss-display-scheduler.service -n 100

# 3. 检查配置
cat config.yml | grep enabled

# 4. 手动运行测试
venv/bin/python scripts/display_scheduler_service.py --once
```

---

## 11. 墨水屏故障排查指南

> 基于实际开发经验的完整故障排查流程和解决方案

### 11.1 故障排查方法论

墨水屏显示问题的排查应该遵循**从软件到硬件、从简单到复杂**的原则：

```
1. 软件验证
   ↓
2. 驱动检查
   ↓
3. 资源冲突
   ↓
4. 硬件测试
```

### 11.2 快速诊断流程图

```mermaid
graph TD
    A[墨水屏不显示/不更新] --> B{软件模式能生成图像吗?}
    B -->|能| C[软件正常，问题在硬件层]
    B -->|不能| D[检查图像生成代码]

    C --> E{有其他服务运行吗?}
    E -->|有| F[停止所有竞争服务]
    E -->|没有| G[检查驱动初始化]

    F --> G
    G --> H{初始化序列完整吗?}
    H -->|不完整| I[添加完整初始化序列]
    H -->|完整| J{调用了refresh吗?}

    I --> J
    J -->|没有| K[添加refresh()调用]
    J -->|有| L[检查硬件连接]

    K --> M[测试验证]
    L --> M
```

### 11.3 常见问题诊断清单

#### ✅ 第一步：软件验证

**目的：** 确认图像生成代码正常工作

```bash
# 1. 使用 Mock 模式测试（不依赖硬件）
venv/bin/python tests/test_driver.py --test basic

# 2. 检查生成的调试图像
ls -lh data/debug_current_view.png
file data/debug_current_view.png

# 3. 如果调试图像正常，说明图像生成逻辑没问题
```

**预期结果：**
- 生成的 PNG 图像尺寸正确（240×360）
- 图像内容符合预期
- 文件大小合理（1-10KB）

#### ✅ 第二步：资源冲突检查

**目的：** 确认没有其他进程占用 GPIO/SPI 资源

```bash
# 1. 检查运行中的服务
sudo systemctl | grep -E "ai-news|weather|epaper|display"

# 2. 检查相关进程
ps aux | grep -E "python.*epaper|python.*weather|python.*news" | grep -v grep

# 3. 检查 GPIO/SPI 设备占用
sudo lsof | grep -E "spidev|gpiomem"

# 4. 检查 crontab 任务
crontab -l | grep -E "epaper|weather|news"
```

**解决方案：**

```bash
# 停止所有竞争服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# 禁用服务（防止自动重启）
sudo systemctl disable ai-news-display-scheduler.service
sudo systemctl disable weather-poetry-display.service

# 终止残留进程
sudo kill -9 $(ps aux | grep -E "python.*epaper" | grep -v grep | awk '{print $2}')
```

#### ✅ 第三步：驱动初始化检查

**目的：** 确认驱动程序正确初始化墨水屏

**关键检查点：**

1. **模块导入**
   ```python
   # 检查 __init__.py 是否为空
   ls -lh lib/waveshare_epd/__init__.py

   # 文件大小应该 > 0 字节
   # 如果是 0 字节，添加至少一行内容：
   # __version__ = "1.0.0"
   ```

2. **sys.path 配置**
   ```python
   # 错误：添加 lib/waveshare_epd/
   sys.path.insert(0, "lib/waveshare_epd")  # ❌

   # 正确：添加 lib/（让 Python 自动导入 waveshare_epd）
   sys.path.insert(0, "lib")  # ✅
   ```

3. **初始化序列**
   ```python
   # Waveshare 3.52寸墨水屏的完整初始化序列：
   epd.init()                      # 基本初始化
   epd.display_NUM(epd.WHITE)      # 清屏到白色
   epd.lut_GC()                    # 加载全刷新查找表
   epd.refresh()                   # 执行刷新
   time.sleep(2)                   # 等待刷新完成
   ```

**测试代码：** `tests/test_original_init.py`

```python
#!/usr/bin/env python3
"""使用原有程序的初始化方式测试"""

from waveshare_epd import epd3in52
import time

epd = epd3in52.EPD()
epd.init()

# 关键：完整的初始化序列
epd.display_NUM(epd.WHITE)
epd.lut_GC()
epd.refresh()
time.sleep(2)

print("初始化完成，屏幕应该是白色")
```

#### ✅ 第四步：显示函数检查

**目的：** 确认图像数据正确发送并刷新到屏幕

**常见错误：**

```python
# ❌ 错误：只发送数据，不刷新
buffer = epd.getbuffer(image)
epd.display(buffer)
# 缺少 refresh()！

# ✅ 正确：发送数据 + 刷新
buffer = epd.getbuffer(image)
epd.display(buffer)    # 发送数据到墨水屏
epd.refresh()          # 触发屏幕刷新 ← 关键！
time.sleep(2)          # 等待刷新完成
```

**验证方法：**

```python
# 创建明显的测试图案
# 全黑 vs 全白交替显示，确认屏幕在变化

test_patterns = [
    Image.new('1', (240, 360), 0),    # 全黑
    Image.new('1', (240, 360), 255),  # 全白
]

for img in test_patterns:
    epd.display(epd.getbuffer(img))
    epd.refresh()
    time.sleep(3)
```

**测试代码：** `tests/test_auto_patterns.py`

### 11.4 实际排障案例

#### 案例1：屏幕一直显示白屏

**现象：**
- 程序运行无错误
- 日志显示"图像已发送"
- 但屏幕始终是白色

**排查过程：**

1. ✅ 软件验证：调试图像生成正常
2. ✅ 资源检查：无冲突服务
3. ✅ 初始化：使用了完整序列
4. ❌ **发现根本原因：`display()` 后缺少 `refresh()`**

**问题代码：**
```python
def _hardware_display(self, image: Image.Image) -> bool:
    buffer = self.epd.getbuffer(image)
    self.epd.display(buffer)  # 只发送数据
    # 缺少 refresh()！
    logger.info("✅ 图像已发送至墨水屏")  # 误导性日志
```

**解决方案：**
```python
def _hardware_display(self, image: Image.Image) -> bool:
    buffer = self.epd.getbuffer(image)
    self.epd.display(buffer)     # 发送数据
    self.epd.refresh()           # ← 添加刷新调用
    time.sleep(2)                # 等待刷新完成
    logger.info("✅ 图像已显示至墨水屏")
```

**教训：**
- `display()` 只是发送数据到墨水屏缓冲区
- **必须**调用 `refresh()` 才能触发屏幕刷新
- 日志消息应该准确反映实际状态

#### 案例2：模块导入失败

**现象：**
```
ImportError: No module named 'waveshare_epd'
```

**排查过程：**

1. 检查 `lib/waveshare_epd/__init__.py`：
   ```bash
   ls -lh lib/waveshare_epd/__init__.py
   # -rw-r--r-- 1 admin admin 0 12月 26 15:30 __init__.py
   #         ^ 文件大小为 0！
   ```

2. **发现根本原因：** `__init__.py` 文件为空（0 字节）

**解决方案：**
```bash
# 添加至少一行内容到 __init__.py
echo "__version__ = '1.0.0'" > lib/waveshare_epd/__init__.py
```

**教训：**
- Python 包的 `__init__.py` 不能为空文件
- 至少需要包含包的元数据或版本号

#### 案例3：sys.path 配置错误

**现象：**
```
ImportError: lib/waveshare_epd is not a package
```

**问题代码：**
```python
lib_abs_path = Path("lib/waveshare_epd").resolve()
sys.path.insert(0, str(lib_abs_path))  # ❌ 错误
from waveshare_epd import epd3in52     # 失败
```

**原因分析：**
- 添加 `lib/waveshare_epd/` 到路径后
- Python 无法识别 `waveshare_epd` 为包（因为已经在这个目录内）

**解决方案：**
```python
lib_abs_path = Path("lib").resolve()   # ✅ 添加父目录
sys.path.insert(0, str(lib_abs_path))
from waveshare_epd import epd3in52     # 成功
```

### 11.5 调试工具和技巧

#### 1. 分步调试脚本

创建 `tests/test_debug_step_by_step.py`：

```python
#!/usr/bin/env python3
"""分步调试墨水屏显示"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from waveshare_epd import epd3in52
from PIL import Image
import time

print("步骤1: 创建驱动实例")
epd = epd3in52.EPD()
print("✅ 驱动创建成功")

print("\n步骤2: 初始化")
epd.init()
print("✅ init() 完成")

print("\n步骤3: 清屏")
epd.display_NUM(epd.WHITE)
print("✅ display_NUM(WHITE) 完成")

print("\n步骤4: 加载查找表")
epd.lut_GC()
print("✅ lut_GC() 完成")

print("\n步骤5: 刷新")
epd.refresh()
print("✅ refresh() 完成")

print("\n等待2秒...")
time.sleep(2)

print("\n步骤6: 创建测试图像")
img = Image.new('1', (240, 360), 0)  # 全黑
print("✅ 图像创建完成")

print("\n步骤7: 发送到屏幕")
buffer = epd.getbuffer(img)
epd.display(buffer)
print("✅ display() 完成")

print("\n步骤8: 刷新屏幕")
epd.refresh()
print("✅ refresh() 完成")

print("\n等待3秒...")
time.sleep(3)

print("\n步骤9: 睡眠")
epd.sleep()
print("✅ sleep() 完成")

print("\n✅ 所有步骤完成！")
```

#### 2. 资源监控脚本

创建 `scripts/check_resources.sh`：

```bash
#!/bin/bash
echo "=== 墨水屏资源检查 ==="
echo ""

echo "1. 运行中的服务："
sudo systemctl | grep -E "ai-news|weather|epaper|display" || echo "  无相关服务"
echo ""

echo "2. 相关进程："
ps aux | grep -E "python.*epaper|python.*weather|python.*news" | grep -v grep || echo "  无相关进程"
echo ""

echo "3. GPIO/SPI 占用："
sudo lsof | grep -E "spidev|gpiomem" || echo "  无设备占用"
echo ""

echo "4. Crontab 任务："
crontab -l | grep -E "epaper|weather|news" || echo "  无相关任务"
echo ""

echo "=== 检查完成 ==="
```

#### 3. 自动化测试脚本

创建 `tests/test_comprehensive.sh`：

```bash
#!/bin/bash

echo "=== 墨水屏综合测试 ==="
echo ""

# 测试1：Mock 模式
echo "测试1：Mock 模式（软件模拟）"
venv/bin/python tests/test_driver.py --test basic
if [ $? -eq 0 ]; then
    echo "✅ Mock 模式测试通过"
else
    echo "❌ Mock 模式测试失败"
    exit 1
fi
echo ""

# 测试2：资源检查
echo "测试2：资源冲突检查"
bash scripts/check_resources.sh
echo ""

# 测试3：硬件初始化
echo "测试3：硬件初始化测试"
sudo venv/bin/python tests/test_original_init.py
if [ $? -eq 0 ]; then
    echo "✅ 初始化测试通过"
else
    echo "❌ 初始化测试失败"
    exit 1
fi
echo ""

# 测试4：图案切换
echo "测试4：图案切换测试"
sudo venv/bin/python tests/test_auto_patterns.py
if [ $? -eq 0 ]; then
    echo "✅ 图案切换测试通过"
else
    echo "❌ 图案切换测试失败"
    exit 1
fi
echo ""

echo "=== 所有测试通过 ==="
```

### 11.6 预防措施

#### 开发阶段

1. **使用 Mock 模式进行早期开发**
   ```python
   driver = create_driver()  # 自动检测硬件
   # 开发时 Mock 模式，部署时硬件模式
   ```

2. **添加详细的调试日志**
   ```python
   logger.debug(f"初始化序列: init() -> display_NUM() -> lut_GC() -> refresh()")
   logger.debug(f"图像尺寸: {image.size}, 模式: {image.mode}")
   logger.debug(f"发送数据 -> 调用 refresh() -> 等待 {delay} 秒")
   ```

3. **使用上下文管理器**
   ```python
   with create_driver() as driver:
       driver.display_image(img)
   # 自动清理资源
   ```

#### 部署阶段

1. **systemd 服务配置**
   ```ini
   [Service]
   # 防止服务堆积
   Restart=on-failure
   RestartSec=10

   # 资源限制
   PrivateTmp=yes
   DevicePolicy=auto
   ```

2. **添加健康检查**
   ```python
   def health_check():
       try:
           driver = create_driver()
           driver.init_display()
           driver.sleep()
           return True
       except Exception as e:
           logger.error(f"健康检查失败: {e}")
           return False
   ```

3. **定期资源检查**
   ```bash
   # 添加到 crontab
   */5 * * * * /path/to/check_resources.sh >> /var/log/epaper_resources.log 2>&1
   ```

### 11.7 故障排查快速参考卡

```bash
# ===== 问题：屏幕不显示/不更新 =====

# Step 1: 快速检查（30秒）
sudo systemctl stop ai-news-* weather-*              # 停止所有服务
sudo venv/bin/python tests/test_auto_patterns.py     # 运行图案测试

# Step 2: 如果 Step 1 失败，检查资源（1分钟）
bash scripts/check_resources.sh                      # 检查资源占用

# Step 3: 分步调试（2分钟）
sudo venv/bin/python tests/test_debug_step_by_step.py

# Step 4: 查看详细日志
tail -100 data/logs/service.log                       # 应用日志
sudo journalctl -u ai-rss-* -n 50                    # 服务日志

# ===== 常见错误 =====

# ImportError: No module named 'waveshare_epd'
echo "__version__ = '1.0.0'" > lib/waveshare_epd/__init__.py

# OSError: [Errno 16] Device or resource busy
sudo systemctl stop ai-news-* weather-*
sudo kill -9 $(ps aux | grep python.*epaper | awk '{print $2}')

# 屏幕一直白屏
# 检查代码中是否调用了 epd.refresh()！

# ===== 验证修复 =====
sudo venv/bin/python tests/test_all_black.py         # 应该显示黑底白字
```

### 11.8 联系和支持

**内部资源：**
- 项目 Wiki：`docs/`
- 测试报告：`EPAPER_TEST_SUMMARY.md`
- 参考项目：
  - `epaper-with-ai-news`
  - `epaper-with-raspberrypi`

**外部资源：**
- [Waveshare 官方文档](https://www.waveshare.com/wiki/)
- [Raspberry Pi GPIO 文档](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Python PIL/Pillow 文档](https://pillow.readthedocs.io/)

---

## 12. 最佳实践总结

### ✅ DO（推荐做法）

1. **使用配置文件** - 所有可配置参数都在 `config.yml` 中
2. **分层架构** - 服务层、业务层、驱动层分离
3. **统一日志** - 使用 Python logging 模块，输出到文件和 journal
4. **错误处理** - 优雅降级，不要让单次错误终止服务
5. **资源管理** - 使用 `__del__` 和 `try/finally` 确保资源释放
6. **守护进程** - 支持 `--daemon` 和 `--once` 两种模式
7. **字体回退** - 提供多级字体回退机制
8. **精确测量** - 使用 `font.getlength()` 而非估算
9. **单色模式** - 墨水屏使用 1位模式，只有黑/白
10. **服务解耦** - 内容获取和显示调度分离

### ❌ DON'T（避免做法）

1. **不要硬编码配置** - 所有配置应在 `config.yml`
2. **不要忽略异常** - 至少记录日志
3. **不要频繁刷新** - 墨水屏刷新慢，设置合理间隔
4. **不要阻塞主循环** - 长时间操作应该异步化
5. **不要估算文本宽度** - 使用 `font.getlength()`
6. **不要忘记资源清理** - 特别是墨水屏 sleep()
7. **不要混用颜色** - 墨水屏只支持单色
8. **不要跳过字体回退** - 始终提供 fallback
9. **不要在服务中使用 print** - 使用 logger
10. **不要让服务崩溃退出** - 捕获所有异常

---

## 12. 参考资源

### 项目参考
- **AI News 项目:** `/home/admin/Github/epaper-with-ai-news`
- **天气诗词项目:** `/home/admin/Github/epaper-with-raspberrypi`
- **当前项目:** `/home/admin/Github/AI-RSS-Client`

### 文档参考
- `docs/EPAPER_QUICK_GUIDE.md` - 墨水屏编程快速指南
- `EPAPER_TEST_README.md` - 测试说明文档
- `EPAPER_TEST_SUMMARY.md` - 测试总结报告

### 技术文档
- [Pillow 文档](https://pillow.readthedocs.io/)
- [systemd 服务管理](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Python logging](https://docs.python.org/3/library/logging.html)

---

## 附录：快速启动模板

### A. 最小服务模板

```python
#!/usr/bin/env python3
"""Minimal Service Template"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging(Config())

    try:
        # 你的服务逻辑
        logger.info("服务运行中...")
        # ...

    except Exception as e:
        logger.error(f"服务错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### B. 最小配置模板

```yaml
# config.yml
display:
  width: 240
  height: 360
  font_file: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

services:
  enabled: true
  interval_minutes: 10

logging:
  level: "INFO"
  logfile: "data/logs/service.log"
```

---

**文档版本：** 1.0
**最后更新：** 2025-12-26
**维护者：** AI-RSS-Client 开发团队
