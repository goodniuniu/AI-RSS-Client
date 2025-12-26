# 开发指引快速参考

> 完整文档请参考：`DEVELOPMENT_GUIDE.md`

---

## 🚀 快速开始

### 项目结构
```
ai-rss-client/
├── config.yml              # 配置文件
├── src/                    # 源代码
│   ├── config.py           # 配置管理
│   ├── display/            # 显示模块
│   ├── services/           # 服务模块
│   └── ...
├── scripts/                # 服务脚本
├── lib/waveshare_epd/      # 墨水屏库
└── systemd/                # 服务文件
```

### 环境设置
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📐 核心架构

### 解耦的服务架构
```
Content Fetch Service (内容获取)
        ↓
    [共享缓存]
        ↓
Display Scheduler Service (显示调度)
```

**优势：** 独立运行、互不阻塞、便于调试

### 目录结构规范
```
src/
├── config.py          # 配置管理 (dataclass)
├── display/
│   ├── epaper_driver.py    # 硬件封装
│   ├── layout_engine.py    # 布局引擎
│   └── renderer.py         # 渲染器
├── services/
│   ├── content_fetch_service.py
│   └── display_scheduler_service.py
└── models/
    └── rss_models.py
```

---

## 🎨 墨水屏显示规范

### 3.52" 墨水屏 (240×360) 最佳参数
```python
DISPLAY = {
    'title_size': 18,      # 标题
    'headline_size': 16,   # 小标题
    'summary_size': 15,    # 正文
    'meta_size': 9,        # 元数据

    'margin': 6,           # 边距
    'line_spacing': 1,     # 行间距

    'header_height': 35,   # 标题区域
    'footer_height': 20,   # 页脚区域

    'min_refresh': 30,     # 最小刷新间隔(秒)
    'max_refresh': 300,    # 最大刷新间隔(秒)
}
```

### 文本渲染要点
```python
# ✅ 精确测量
width = font.getlength(text)

# ❌ 估算（错误）
width = len(text) * font_size * 0.6

# 单色模式
image = Image.new('1', (width, height), 1)  # 1=白色
draw.text((x, y), text, fill=0, font=font)  # 0=黑色
```

### 自动换行算法
```python
def wrap_text(text, font, max_width):
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

---

## 📝 配置管理

### config.yml 示例
```yaml
display:
  width: 240
  height: 360
  font_file: "/usr/share/fonts/truetype/..."
  font_size_title: 18
  # ...

services:
  enabled: true
  interval_minutes: 10

logging:
  level: "INFO"
  logfile: "data/logs/service.log"
```

### 配置加载
```python
from dataclasses import dataclass
import yaml

@dataclass
class DisplayConfig:
    width: int
    height: int
    # ...

class Config:
    def __init__(self, path="config.yml"):
        with open(path) as f:
            data = yaml.safe_load(f)
        self.display = DisplayConfig(**data['display'])
```

---

## 🔧 服务化部署

### Systemd 服务文件
```ini
[Unit]
Description=AI-RSS Display Scheduler
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/service.py --daemon
WorkingDirectory=/path/to/project
User=admin
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 服务管理
```bash
# 安装服务
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-rss-*
sudo systemctl start ai-rss-*

# 查看状态
sudo systemctl status ai-rss-display-scheduler.service

# 查看日志
sudo journalctl -u ai-rss-display-scheduler.service -f
```

---

## 🛠️ 开发工作流

### 调试模式
```bash
# 1. 停止服务
sudo systemctl stop ai-rss-*

# 2. 直接运行
venv/bin/python scripts/display_scheduler_service.py

# 3. 查看日志
tail -f data/logs/service.log
```

### 测试流程
```bash
# 软件测试（生成图像）
venv/bin/python tests/test_epaper.py

# 硬件测试
sudo venv/bin/python tests/test_epaper_hardware.py

# 服务集成测试
sudo systemctl start ai-rss-display-scheduler.service
```

---

## ✅ 最佳实践

### DO（推荐）
- ✅ 使用配置文件
- ✅ 分层架构
- ✅ 统一日志
- ✅ 优雅降级
- ✅ 资源管理
- ✅ 字体回退
- ✅ 精确测量
- ✅ 单色模式
- ✅ 服务解耦

### DON'T（避免）
- ❌ 硬编码配置
- ❌ 忽略异常
- ❌ 频繁刷新
- ❌ 阻塞主循环
- ❌ 估算宽度
- ❌ 忘记清理
- ❌ 混用颜色
- ❌ 使用 print

---

## 🐛 常见问题

### GPIO 占用
```bash
# 查找并停止占用进程
sudo systemctl stop ai-rss-* weather-poetry-display.service
```

### 字体加载失败
```python
# 多级回退
try:
    font = ImageFont.truetype(primary, size)
except:
    try:
        font = ImageFont.truetype(fallback, size)
    except:
        font = ImageFont.load_default()
```

### 服务不更新
```bash
# 检查服务状态和日志
sudo systemctl status ai-rss-display-scheduler.service
sudo journalctl -u ai-rss-display-scheduler.service -n 100
```

---

## 📚 关键代码模式

### 服务模板
```python
class Service:
    def __init__(self):
        self.config = Config()
        self.enabled = self.config.services.enabled

    def run_once(self):
        if not self.enabled:
            return False
        # ... 服务逻辑
        return True

    def run_daemon(self):
        while True:
            self.run_once()
            time.sleep(self.interval * 60)

if __name__ == "__main__":
    service = Service()
    if '--daemon' in sys.argv:
        service.run_daemon()
    else:
        service.run_once()
```

### 墨水屏驱动
```python
class EpaperDriver:
    def init_display(self):
        from waveshare_epd import epd3in52
        self.epd = epd3in52.EPD()
        self.epd.init()
        self.is_initialized = True

    def display_image(self, image):
        self.epd.display(self.epd.getbuffer(image))

    def sleep(self):
        self.epd.sleep()
```

### 日志设置
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(config):
    logger = logging.getLogger()
    logger.setLevel(config.logging.level)

    handler = RotatingFileHandler(
        config.logging.logfile,
        maxBytes=config.logging.max_log_size,
        backupCount=config.logging.backup_count
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
```

---

## 📖 完整文档

详细内容请查看：**`DEVELOPMENT_GUIDE.md`**

包含：
- 完整架构设计
- 代码示例
- 部署流程
- 问题排查
- 最佳实践详解

---

**快速参考版本：** 1.0
**完整文档版本：** 1.0
**更新时间：** 2025-12-26
