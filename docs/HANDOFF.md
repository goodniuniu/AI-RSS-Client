# AI-RSS 墨水屏客户端 — 交接文档

> 交接日期：2026-08-05 ｜ 接手对象：后续维护本树莓派墨水屏 RSS 项目的人 / AI

## 0. 一句话现状

后端服务器 `8.134.202.27:8000`（AI-RSS-Hub）已断连 **7 天以上**。树莓派客户端本身正常，但因拿不到新数据只能反复显示同一篇缓存旧文章（看起来像"屏幕没更新"）。**已上线后端健康探针让这类故障在屏幕上可见，但根本修复仍需到后端服务器重启服务。**

## 1. 最高优先级待办（P0）

**到 `8.134.202.27` 重启 8000 端口的 AI-RSS-Hub 后端服务。**

详细步骤见 [`docs/backend-recovery-sop.md`](backend-recovery-sop.md)（按 systemd / docker / pm2 / 裸进程分别给了命令）。

恢复验证（在树莓派跑）：

```bash
curl -m8 -o /dev/null -w "%{http_code}\n" http://8.134.202.27:8000/api/health   # 期望 200
journalctl -u ai-rss-client-display.service -n 30 --no-pager | grep 后端         # 期望看到"✅ 后端恢复在线"
```

后端恢复后：屏幕"离线"角标自动消失，新文章约 20 分钟内推送上来。

## 2. 本次已完成的工作

| # | 内容 | 提交 |
|---|---|---|
| 1 | 诊断"屏幕没更新"根因 = 后端断连（非硬件故障） | — |
| 2 | 新增后端健康探针 `src/services/health_monitor.py` | `7209813` |
| 3 | 渲染器加"离线"角标（反白标签） | `7209813` → `be638d1` |
| 4 | 配置新增可选 `health_monitor` 节 | `7209813` |
| 5 | 后端排查 SOP `docs/backend-recovery-sop.md` | `7209813` |

均在分支 **`feat/backend-health-monitor`**（已推 GitHub，与 origin 同步）。
- PR 创建链接：https://github.com/goodniuniu/AI-RSS-Client/pull/new/feat/backend-health-monitor
- 可选：合并到 `main`，或开 PR 走评审。

## 3. 健康探针工作原理

- 后台守护线程每 **60s** `GET {base_url}/api/health`（超时 3s，不重试）。
- 连续失败 **2 次**才判离线（防抖，避免网络抖动误报）。
- 状态翻转打日志：下线 `WARNING`（含上次成功时间、错误详情）、恢复 `INFO`。
- 离线时：`DisplayScheduler` 每个 cycle（~30s）读 `is_online` 传给 `ContentRenderer`，在 Header 左上角画**反白标签**（白底黑字"离线"）。
- **服务每次重启后，探针从"乐观在线"重新开始，约 60–90s 后才会再次判离线并显示角标**——这是正常的防抖行为，不是 bug。重启后若没立刻看到角标，多等 1 分钟。

## 4. 代码地图

| 文件 | 作用 | 接手时关注 |
|---|---|---|
| `src/services/health_monitor.py` | 探针核心（新） | 调参：周期 / 超时 / 阈值 |
| `src/services/display_service.py` | 显示守护进程 | 创建/启停探针（`__init__` / `run_daemon` / `close`） |
| `src/services/display_scheduler.py` | 每 cycle 渲染 + 推送 | `update_display()` 读 `is_online` 传渲染器 |
| `src/display/renderer.py` | 画图 | `_draw_header(backend_online=)` 画角标 |
| `src/config.py` | 配置 | `HealthMonitorConfig` dataclass（可选节） |
| `config.yml` | 运行配置 | `health_monitor:` 节 |
| `docs/backend-recovery-sop.md` | 后端排查 SOP（新） | 交给后端运维 |

## 5. 配置调参（`config.yml` → `health_monitor`）

```yaml
health_monitor:
  enabled: true
  check_interval_seconds: 60   # 探测周期（秒）
  request_timeout_seconds: 3   # 单次探测超时（秒）
  failure_threshold: 2         # 连续失败 N 次才判离线（防抖）
```

改完执行 `sudo systemctl restart ai-rss-client-display.service` 生效。

## 6. 运维命令速查

```bash
# 实时跟踪日志
journalctl -u ai-rss-client-display.service -f

# 看探针告警
journalctl -u ai-rss-client-display.service --since "10 min ago" | grep -E "后端离线|后端恢复"

# 重启客户端（改代码 / 配置后）
sudo systemctl restart ai-rss-client-display.service

# 手动测后端可达性
curl -m8 -o /dev/null -w "%{http_code}\n" http://8.134.202.27:8000/api/health

# 单独测探针逻辑（不碰硬件 / 不影响运行中的服务）
cd /home/admin/Github/AI-RSS-Client
PYTHONPATH=. python3 -c "from src.services.health_monitor import BackendHealthMonitor as M; m=M('http://8.134.202.27:8000'); m.update(); m.update(); print('online=', m.is_online); print(m.get_status())"
```

## 7. 已知坑 / 注意事项

1. **字体字形坑**：文泉驿微米黑不含 `⚠`（U+26A0）等 Unicode 符号，PIL 会画成豆腐块。屏幕文字**只用纯中文 / ASCII**。角标第一版因此不可见，已修（`be638d1`）。后续改 UI 务必注意。
2. **`data/` 运行时文件被 git 误跟踪**：`articles.db`、`offline_cache.json`、`debug_*.png` 等虽已写进 `.gitignore`，但在加忽略规则前就被跟踪，`git status` 会长期显示其改动。提交时**务必精确 `git add <文件>`，勿用 `git add -A`**。彻底清理：`git rm --cached data/articles.db data/offline_cache.json` 另起一个提交。
3. **`CLAUDE.md` 已过时**：它仍写"frontend 未实现"，与实际（已实现的 Python 墨水屏客户端）不符，参考时注意，建议后续更新或替换。
4. **renderer 内 base_url 硬编码**：`src/display/renderer.py` 加载二维码处 `base_url = "http://8.134.202.27:8000"` 是写死的，与健康探针从 api client 取 base_url 不统一。后续可改为从配置注入，避免改地址时漏改。
5. **服务重启后角标延迟**：见第 3 节，约 60–90s 才显示，属正常防抖。

## 8. 环境信息

- 设备：树莓派（hostname `raspberrypi`），Linux 6.1.0-rpi7-rpi-v8
- 项目路径：`/home/admin/Github/AI-RSS-Client`
- systemd 服务：`ai-rss-client-display.service`（`python3 main.py run --base-url http://8.134.202.27:8000`）
- 后端：`8.134.202.27:8000`（AI-RSS-Hub，FastAPI + uvicorn，独立公网服务器）
- GitHub：`goodniuniu/AI-RSS-Client`（SSH），当前分支 `feat/backend-health-monitor`
- 显示硬件：Waveshare 3.52" 240×360 墨水屏
