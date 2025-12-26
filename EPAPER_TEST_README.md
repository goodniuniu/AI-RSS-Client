# 墨水屏测试说明

本目录包含用于测试 3.52 英寸墨水屏（240×360 像素）的完整代码和测试结果。

## 环境准备

### 1. Python 虚拟环境

项目已配置 Python 虚拟环境 `venv/`，包含所有必需的依赖包。

### 2. 依赖包

已安装的依赖：
- `Pillow` - 图像处理库
- `spidev` - SPI 通信
- `gpiozero` - GPIO 控制
- `colorzero` - 颜色处理

## 测试代码

### 文件：`test_epaper.py`

完整的墨水屏测试程序，实现了 `docs/EPAPER_QUICK_GUIDE.md` 中的核心要点：

**核心功能：**
- ✅ 自动换行（智能文本折行算法）
- ✅ 文本宽度精确测量
- ✅ 单色高对比度显示（1位模式）
- ✅ 多种布局测试
- ✅ 硬件/软件模式自动切换

**测试场景：**
1. **基本文本显示** - 测试标题、内容、页脚布局
2. **长文本换行** - 测试自动换行功能
3. **多行布局** - 测试列表格式显示

## 运行测试

### 软件模式（仅生成图像）

```bash
source venv/bin/activate
python test_epaper.py
```

这将生成三个测试图像到 `output/` 目录。

### 硬件模式（需要墨水屏连接）

如果墨水屏已连接到树莓派，使用 root 权限运行：

```bash
sudo venv/bin/python test_epaper.py
```

注意：硬件模式需要 root 权限才能访问 GPIO。

## 测试结果

### 生成的图像

所有测试图像保存在 `output/` 目录：

1. `test_basic.png` - 基本显示测试
   - 标题："E-Paper Test"
   - 包含自动换行的长文本
   - 底部显示更新时间

2. `test_long_text.png` - 长文本换行测试
   - 测试 Lorem ipsum 文本
   - 验证自动换行算法

3. `test_multiline.png` - 多行布局测试
   - RSS 源列表格式
   - 5行条目显示

### 测试截图

查看 `output/` 目录中的 PNG 图像可以看到渲染效果。

## 代码实现亮点

### TextRenderer 类

```python
class TextRenderer:
    """文本渲染器 - 实现自动换行和文本测量"""
```

**核心方法：**

1. **`wrap_text()`** - 智能换行算法
   - 基于字体实际宽度测量
   - 支持中英文混合文本
   - 自动计算最大行宽

2. **`truncate_text()`** - 文本截断
   - 防止文本超出屏幕边界
   - 添加省略号后缀

3. **`render()`** - 完整页面渲染
   - 自动布局（标题、内容、页脚）
   - 1位单色模式（黑/白）
   - 高对比度显示

### 字号策略

根据屏幕宽度自动选择合适的字号：

```python
if width <= 250:  # 小屏 240×360
    title_size = 16
    body_size = 14
    meta_size = 10
```

### 布局计算

标准的 Header-Content-Footer 布局：

```
┌──────────────────┐
│ Header (35px)    │  标题
├──────────────────┤
│ Content          │  主要内容
│ (自适应)         │  自动换行
├──────────────────┤
│ Footer (20px)    │  时间/状态
└──────────────────┘
```

## 性能优化

1. **精确宽度测量** - 使用 `font.getlength()` 而非估算
2. **一次性渲染** - 完整渲染后再显示（墨水屏刷新慢）
3. **内存管理** - 使用后立即释放图像资源
4. **错误处理** - 优雅降级到软件模式

## 硬件说明

### 墨水屏型号
- Waveshare 3.52 英寸 E-Paper
- 分辨率：240×360 像素
- 单色显示（黑/白）

### GPIO 引脚配置

```python
RST_PIN  = 17  # 复位
DC_PIN   = 25  # 数据/命令
CS_PIN   = 8   # 片选
BUSY_PIN = 24  # 忙检测
PWR_PIN  = 18  # 电源
```

### 硬件库位置

墨水屏驱动库位于 `lib/waveshare_epd/`：
- `epd3in52.py` - 3.52寸墨水屏驱动
- `epdconfig.py` - 硬件配置
- `DEV_Config_64.so` - 配置库

## 常见问题

### Q: 为什么显示"软件模式"？

A: 这可能是因为：
1. 没有使用 sudo 运行（GPIO 需要权限）
2. 墨水屏硬件未连接
3. GPIO 被其他程序占用

软件模式下仍可以生成测试图像。

### Q: 如何查看生成的图像？

A: 使用任何图像查看器打开 `output/*.png` 文件，或使用命令：
```bash
ls -lh output/
file output/*.png
```

### Q: 如何在实际墨水屏上显示？

A: 确保硬件连接正确，然后使用：
```bash
sudo venv/bin/python test_epaper.py
```

## 扩展使用

### 自定义内容显示

可以修改 `test_epaper.py` 中的测试内容：

```python
title = "你的标题"
content = "你要显示的内容"
footer = "页脚信息"

renderer = TextRenderer(240, 360)
image = renderer.render(title, content, footer)
```

### 集成到项目

将 `TextRenderer` 类导入到你的项目：

```python
from test_epaper import TextRenderer

renderer = TextRenderer(240, 360)
image = renderer.render(title, content)
```

## 技术参考

- 完整文档：`docs/EPAPER_QUICK_GUIDE.md`
- 硬件驱动：`lib/waveshare_epd/`
- PIL/Pillow 文档：https://pillow.readthedocs.io/

## 总结

✅ 虚拟环境已配置
✅ 依赖包已安装
✅ 测试代码已编写
✅ 测试已成功执行
✅ 生成的图像符合预期

测试程序完全遵循了 `docs/EPAPER_QUICK_GUIDE.md` 中的5条核心规则，实现了高质量的墨水屏文本显示功能。
