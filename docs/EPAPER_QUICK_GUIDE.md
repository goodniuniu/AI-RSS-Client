# 墨水屏输出编程 - 核心要点

> Claude AI 编写墨水屏显示应用的快速参考

## 🎯 最关键的5条规则

### 1. 屏幕极小，精确到像素
```
典型尺寸: 240×360 (3.52寸)
- 不能浪费1个像素
- 边距: 4-8px
- 行间距: 1-2px
- 最小字号: 9px
```

### 2. 单色显示，高对比度
```python
# 必须使用PIL的1位模式
image = Image.new('1', (width, height), 1)  # 1=白色
draw = ImageDraw.Draw(image)

# 只用纯色
BLACK = 0
WHITE = 1
draw.text((x, y), "Text", fill=BLACK, font=font)

# 禁用抖动
image = image.convert('1', dither=Image.NONE)
```

### 3. 自动换行是必须的
```python
def wrap_text(text, font, max_width):
    """智能换行算法"""
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

### 4. 测量实际宽度，不要估算
```python
# ❌ 错误
width = len(text) * font_size * 0.6

# ✅ 正确
bbox = font.getbbox(text)
width = bbox[2] - bbox[0]
# 或
width = font.getlength(text)
```

### 5. 刷新慢，一次性完整渲染
```python
# ❌ 错误：逐条显示
for item in items:
    render(item)
    display()  # 太慢！

# ✅ 正确：一次性渲染
image = create_full_image(items)
display(image)  # 一次显示
```

## 📐 标准布局模板

```
┌──────────────────┐
│ Header (35px)    │  标题+时间
├──────────────────┤
│ Content          │  主要内容
│ (自适应)         │  占80-90%
├──────────────────┤
│ Footer (20px)    │  页码/状态
└──────────────────┘

计算：
content_h = screen_h - header_h - footer_h - 2*margin
```

## 🔤 字号选择

```python
# 基于屏幕宽度推荐
if screen_w <= 250:  # 小屏
    title = 16, body = 12, meta = 8
elif screen_w <= 400:  # 中屏
    title = 18, body = 14, meta = 9
else:  # 大屏
    title = 24, body = 16, meta = 12

# 硬性下限
MIN_SIZE = 9
```

## ⚡ 性能要点

### 刷新间隔
```python
MIN_INTERVAL = 300  # 5分钟
# 不要更频繁，墨水屏刷新慢
```

### 内存管理
```python
# 显示后立即释放
epd.display(epd.getbuffer(image))
del draw
image.close()
epd.sleep()
```

### 批量操作
```python
# 按颜色分组，减少状态切换
for item in black_items:
    draw.text(pos, item.text, fill=0)
for item in gray_items:
    draw.text(pos, item.text, fill=1)
```

## ⚠️ 绝对避免的错误

### 1. 字号太小
```python
# ❌ 6px不可读
font = load_font(6)

# ✅ 最小9px
font = load_font(max(size, 9))
```

### 2. 不检查边界
```python
# ❌ 可能超出屏幕
draw.text((x, y), long_text, font=font)

# ✅ 测量并裁剪
if font.getlength(text) > max_width:
    text = truncate(text, font, max_width)
draw.text((x, y), text, font=font)
```

### 3. 使用颜色/灰度
```python
# ❌ 不支持
draw.text(pos, text, fill=(128, 128, 128))

# ✅ 只用纯色
draw.text(pos, text, fill=0)  # 黑色
```

### 4. 过度刷新
```python
# ❌ 每秒刷新
while True:
    update()
    sleep(1)

# ✅ 合理间隔
while True:
    update()
    sleep(300)  # 5分钟
```

## 📝 代码模板

### 最小渲染器

```python
from PIL import Image, ImageDraw, ImageFont

class SimpleRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14
        )

    def render(self, text):
        # 创建图像
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)

        # 换行
        lines = self.wrap_text(text, self.font, self.width - 12)

        # 渲染
        y = 10
        for line in lines:
            draw.text((6, y), line, font=self.font, fill=0)
            y += self.font.getbbox(line)[3] + 1

        return image

    def wrap_text(self, text, font, max_width):
        # 实现换行（见上文）
        pass
```

### 使用示例

```python
# 创建渲染器
renderer = SimpleRenderer(240, 360)

# 渲染内容
image = renderer.render("Hello World!")

# 显示
epd.display(epd.getbuffer(image))
epd.sleep()

# 释放
image.close()
```

## ✅ 开发检查清单

编码前确认：
- [ ] 知道屏幕分辨率
- [ ] 确定最小字号
- [ ] 设计好布局
- [ ] 规划好刷新策略

编码时注意：
- [ ] 使用实际宽度测量
- [ ] 实现自动换行
- [ ] 处理内容截断
- [ ] 优化内存使用

测试时验证：
- [ ] 长文本正确换行
- [ ] 超长内容正确截断
- [ ] 最小字号可读
- [ ] 对比度足够

## 🚀 快速开始

```bash
# 1. 复制精简库
bash scripts/copy_epaper_lib.sh /path/to/project

# 2. 使用模板代码
python3 -c "
from PIL import Image, ImageDraw, ImageFont

# 创建测试图像
img = Image.new('1', (240, 360), 1)
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

draw.text((10, 10), 'Test!', font=font, fill=0)
img.save('test.png')
print('✅ Image created')
"
```

---

**完整文档**: `docs/EPAPER_OUTPUT_GUIDE.md`
**项目参考**: `src/layout.py`, `src/render.py`
