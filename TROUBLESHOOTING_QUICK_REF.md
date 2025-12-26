# 墨水屏故障排查快速参考卡

> 快速定位和解决墨水屏显示问题

**版本：** 1.0
**更新时间：** 2025-12-26

---

## 🔴 问题：屏幕不显示/不更新

### 30秒快速诊断

```bash
# Step 1: 停止所有竞争服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# Step 2: 运行图案测试（屏幕应该切换6个不同图案）
sudo venv/bin/python tests/test_auto_patterns.py
```

**预期结果：** 屏幕显示：全黑 → 全白 → 棋盘格 → 条纹 → 上下反色 → 左右反色

---

## 🟡 问题：ImportError

### 错误：`No module named 'waveshare_epd'`

**原因：** `__init__.py` 文件为空

```bash
# 解决方案
echo "__version__ = '1.0.0'" > lib/waveshare_epd/__init__.py
```

### 错误：`lib/waveshare_epd is not a package`

**原因：** sys.path 配置错误

**检查代码：**
```python
# ❌ 错误
sys.path.insert(0, "lib/waveshare_epd")

# ✅ 正确
sys.path.insert(0, "lib")
```

---

## 🟠 问题：GPIO 资源占用

### 错误：`OSError: [Errno 16] Device or resource busy`

**快速解决：**
```bash
# 停止所有服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# 终止残留进程
sudo kill -9 $(ps aux | grep -E "python.*epaper" | grep -v grep | awk '{print $2}')

# 验证清理
bash scripts/check_resources.sh
```

---

## 🟢 问题：屏幕一直白屏

### 根本原因：缺少 `refresh()` 调用

**检查代码：**
```python
# ❌ 错误：只发送数据
buffer = epd.getbuffer(image)
epd.display(buffer)

# ✅ 正确：发送数据 + 刷新
buffer = epd.getbuffer(image)
epd.display(buffer)
epd.refresh()    # ← 必须调用！
time.sleep(2)
```

**验证修复：**
```bash
sudo venv/bin/python tests/test_all_black.py
# 应该显示黑底白字 "BLACK"
```

---

## 📋 完整诊断流程

```bash
# 1. 资源检查（1分钟）
bash scripts/check_resources.sh

# 2. 分步调试（2分钟）
sudo venv/bin/python tests/test_debug_step_by_step.py

# 3. 综合测试（5分钟）
bash tests/test_comprehensive.sh

# 4. 查看日志
tail -100 data/logs/service.log
sudo journalctl -u ai-rss-* -n 50
```

---

## 🛠️ 调试工具

| 工具 | 用途 | 命令 |
|------|------|------|
| **资源检查** | 检查 GPIO/SPI 占用 | `bash scripts/check_resources.sh` |
| **分步调试** | 定位具体失败步骤 | `sudo venv/bin/python tests/test_debug_step_by_step.py` |
| **图案测试** | 验证显示功能 | `sudo venv/bin/python tests/test_auto_patterns.py` |
| **综合测试** | 自动化全部测试 | `bash tests/test_comprehensive.sh` |

---

## 📚 详细文档

- **完整故障排查指南：** `DEVELOPMENT_GUIDE.md` 第11章
- **显示控制指南：** `DISPLAY_CONTROL_GUIDE.md`
- **开发指南：** `DEVELOPMENT_GUIDE.md`

---

## ✅ 验证清单

- [ ] Mock 模式测试通过（生成调试图像）
- [ ] 资源检查无冲突
- [ ] 初始化序列完整
- [ ] `display()` 后调用了 `refresh()`
- [ ] 图案切换测试通过
- [ ] 屏幕能正确显示不同内容

---

## 🆘 获取帮助

**内部资源：**
- 参考项目：`epaper-with-ai-news`, `epaper-with-raspberrypi`
- 测试报告：`EPAPER_TEST_SUMMARY.md`

**外部资源：**
- [Waveshare 官方文档](https://www.waveshare.com/wiki/)
- [Raspberry Pi GPIO 文档](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)

---

**提示：** 90% 的墨水屏问题都是以下三个原因之一：
1. 其他服务占用 GPIO
2. 缺少 `refresh()` 调用
3. `__init__.py` 文件为空

先检查这三项，通常能快速解决问题！
