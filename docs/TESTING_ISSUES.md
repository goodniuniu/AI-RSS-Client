# 测试中发现的问题清单

**日期**: 2026-01-04
**状态**: 需要修复

---

## 🔴 关键问题

### 1. DisplayScheduler中的导入错误

**文件**: `src/services/display_scheduler.py:14`

**错误**:
```python
from ..display.renderer import ArticleRenderer  # ✗ 类不存在
```

**应该是**:
```python
from ..display.renderer import ContentRenderer  # ✓
```

**影响**: 无法导入DisplayScheduler模块

**修复优先级**: 高

**修复方案**:
```python
# display_scheduler.py 第14行
# 从：
from ..display.renderer import ArticleRenderer

# 改为：
from ..display.renderer import ContentRenderer
```

---

### 2. DisplayScheduler中的类名错误

**文件**: `src/services/display_scheduler.py`

**错误**:
```python
self.renderer: Optional[ArticleRenderer] = None  # ✗
self.renderer = Optional[ArticleRenderer] = None  # ✗
```

**应该是**:
```python
self.renderer: Optional[ContentRenderer] = None  # ✓
```

**修复**: 将所有 `ArticleRenderer` 替换为 `ContentRenderer`

---

## ⚠️ 次要问题

### 3. LayoutEngine初始化参数类型错误

**影响范围**: 显示调度器初始化

**问题**: LayoutEngine期望line_spacing是float，但可能传入了Config对象

**修复示例**:
```python
# 错误的用法
layout_engine = LayoutEngine(config)  # ✗

# 正确的用法
layout_engine = LayoutEngine(line_spacing=1.0)  # ✓
```

---

## 📝 配置建议

### 4. API地址配置

**当前问题**:
- 默认API地址: localhost:8000
- 实际API地址: http://8.134.202.27:8000

**建议修改** `config.yml`:
```yaml
api:
  base_url: "http://8.134.202.27:8000"  # 更新为实际地址
  timeout: 10
  retry_attempts: 3
  retry_delay: 2
```

或使用环境变量：
```bash
export AI_RSS_API_URL="http://8.134.202.27:8000"
```

---

## ✅ 修复优先级

1. **立即修复** (阻止系统运行):
   - [ ] 修复 display_scheduler.py 中的导入错误
   - [ ] 修复 ArticleRenderer → ContentRenderer 类名

2. **尽快修复** (影响功能):
   - [ ] 修复 LayoutEngine 初始化参数
   - [ ] 更新 config.yml 中的API地址

3. **可选改进**:
   - [ ] 添加单元测试用例
   - [ ] 完善错误处理

---

## 🔧 快速修复脚本

```bash
# 修复导入错误
cd /home/admin/Github/AI-RSS-Client

# 1. 修复 display_scheduler.py
sed -i 's/ArticleRenderer/ContentRenderer/g' src/services/display_scheduler.py

# 2. 更新 config.yml 中的API地址（可选）
sed -i 's|http://localhost:8000|http://8.134.202.27:8000|g' config.yml

# 3. 验证修复
python3 -c "from src.services import DisplayScheduler; print('✓ Import successful')"
```

---

## 📊 修复验证

修复后运行以下命令验证：

```bash
# 1. 测试导入
python3 -c "from src.services import DisplayScheduler; print('✓ DisplayScheduler import OK')"

# 2. 测试初始化
python3 -c "
from src.services import DisplayScheduler, ContentManager
from src.fetchers import create_client

client = create_client(base_url='http://8.134.202.27:8000')
cm = ContentManager(api_client=client)
scheduler = DisplayScheduler(content_manager=cm)
print('✓ Scheduler initialization OK')
"

# 3. 测试状态查询
python3 main.py status --base-url http://8.134.202.27:8000
```

---

**最后更新**: 2026-01-04
**状态**: 待修复
