# AI-RSS 墨水屏客户端 — 交接文档

> 最近更新：2026-08-06｜ 接手对象：后续维护本树莓派墨水屏 RSS 项目的人 / AI

## 0. 现状

后端 `8.134.202.27:8000`（AI-RSS-Hub）**已恢复**：服务进程在线、RSS 内容抓取正常（最新文章为当日）。树莓派客户端各项改进（健康探针、发布日期、footer、扫码引导）均已上线并合并到 `main`，服务运行中。

**当前主要问题（2026-08-06 修正认知）**：经核实，项目设计上**一篇文章只生成一种摘要**（中文 `summary` 或英文 `summary_en`，非两者皆有）。后端最新数据：中文 `summary` 基本为空、英文 `summary_en` 覆盖约 39%，属正常设计而非故障。客户端已适配此设计——**任一摘要存在即单栏显示，两者皆无才显示扫码引导**，故"墨水屏显示扫码引导"对客户端而言已不构成问题。剩余的"部分文章两种摘要都没有"是后端 LLM 覆盖率问题，由后端自行优化，**客户端无阻塞**。

## 1. 待办（按优先级）

### P1（原 P0，已降级）— 后端摘要覆盖率（可选优化）
客户端已适配单摘要设计（见下"已完成的工作"），不再阻塞显示。后端若想提升覆盖率（目前英文 `summary_en` ~39%、中文 `summary` 基本为空），可到 `8.134.202.27` 排查 LLM 摘要任务：是否报错/限流、是否覆盖老文章、是否补齐中文通道。这是后端自有的优化项，**客户端无需配合**。

### P1 — 可选清理
- `data/` 运行时文件 `git rm --cached`（见已知坑 3）。
- `CLAUDE.md` 过时（见已知坑 4），建议更新。

## 2. 已完成的工作（均在 `main`）

| 提交 | 内容 |
|---|---|
| `8477c10` | 单摘要文章单栏显示，修复纯英文摘要误显扫码引导、纯中文摘要两栏重复 |
| `21aca55` | 无内容文章改为中英双语扫码引导提示 |
| `284a8e0` | footer 字号 7→11px，去除与标题区重复的日期 |
| `b988ec6` | 标题下方添加文章发布日期，修复 footer 时间恒为 00:00 |
| `ed481a4` | 交接文档（本文） |
| `be638d1` | 离线角标改为反白标签，修复 ⚠ 字形缺失不可见 |
| `7209813` | 后端健康探针 + 后端排查 SOP |

> 早先在 `feat/backend-health-monitor` 分支开发，已 fast-forward 合并到 `main` 并删除该分支。GitHub：`goodniuniu/AI-RSS-Client`。

## 3. 健康探针（已上线）

- 后台线程每 **60s** `GET {base_url}/api/health`（超时 3s、不重试）。
- 连续失败 **2 次**才判离线（防抖）；翻转打 `WARNING`（下线）/ `INFO`（恢复）。
- 离线时 Header 左上角显示反白"离线"标签。
- **服务重启后约 60–90s 才显示角标**（乐观初值 + 防抖，属正常）。
- 调参：`config.yml` → `health_monitor`。后端排查见 [`backend-recovery-sop.md`](backend-recovery-sop.md)。

## 4. 屏幕布局（当前）

```
┌──────────────────────────┐
│⚠离线  16:08 周三 27°C 雾 │ header（离线时左上角反白标签）
├──────────────────────────┤
│ 文章标题（最多2行）       │
│ 2026-08-05 07:15         │ 标题下方发布日期（raw_publish_timestamp）
│ ────────────────────     │
│ 中文摘要 / AI 摘要生成中… │ 有 summary 显示摘要，否则扫码引导
│ English summary / Summa.. │
│      [ 二维码 ]           │ 扫码看原文
├──────────────────────────┤
│ 科技               IP:… │ footer（来源 + IP，11px）
└──────────────────────────┘
```

## 5. 代码地图

| 文件 | 作用 | 接手关注 |
|---|---|---|
| `src/models/article.py` | 文章模型 | `raw_publish_timestamp`（完整时间戳）、`display_content`（无内容时返回扫码引导） |
| `src/display/renderer.py` | 渲染 | `_draw_publish_date`（标题下日期）、`_draw_footer`（11px）、`_draw_header`（离线角标） |
| `src/services/health_monitor.py` | 健康探针 | 调参：周期/超时/阈值 |
| `src/services/display_scheduler.py` | 调度 | `update_display` 组装 article_dict |
| `src/services/display_service.py` | 显示守护 | 探针启停 |
| `src/config.py` / `config.yml` | 配置 | `health_monitor` 节；`display.footer_height` 影响 footer 字号上限 |
| `docs/backend-recovery-sop.md` | 后端排查 SOP | 交给后端运维 |

## 6. 运维命令速查

```bash
# 实时日志 / 探针告警
journalctl -u ai-rss-client-display.service -f
journalctl -u ai-rss-client-display.service --since "10 min ago" | grep -E "后端离线|后端恢复"

# 重启客户端（改代码/配置后）
sudo systemctl restart ai-rss-client-display.service

# 手动同步文章 + 统计 summary 缺失
python3 main.py fetch --base-url http://8.134.202.27:8000
python3 -c "import sqlite3;c=sqlite3.connect('data/articles.db');print('有summary:',c.execute(\"SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary!=''\").fetchone()[0],'/ 共',c.execute('SELECT COUNT(*) FROM articles').fetchone()[0])"

# 测后端
curl -m8 -o /dev/null -w "%{http_code}\n" http://8.134.202.27:8000/api/health
```

## 7. 已知坑 / 注意事项

1. **summary ~50% 缺失（P0）**：后端 AI 摘要只覆盖一半文章，`/api/articles` 又不返回 `content`，客户端对无内容文章用扫码引导兜底。根因在后端，见第 1 节。
2. **字体字形坑**：文泉驿微米黑不含 `⚠`(U+26A0) 等 Unicode 符号，PIL 画成豆腐块。屏幕文字**只用纯中文/ASCII**。离线角标因此踩过坑（已修）。改 UI 务必注意。
3. **`data/` 运行时文件被 git 误跟踪**：`articles.db`/`offline_cache.json`/`debug_*.png` 等已在 `.gitignore`，但加规则前就被跟踪，`git status` 长期显示改动。提交**务必精确 `git add <文件>`，勿用 `git add -A`**。彻底清理：`git rm --cached data/articles.db data/offline_cache.json`。
4. **`CLAUDE.md` 过时**：仍写"frontend 未实现"，与实际（Python 墨水屏客户端）不符，建议更新。
5. **renderer 内 base_url 硬编码**：`src/display/renderer.py` 二维码处 `base_url = "http://8.134.202.27:8000"` 写死，与健康探针取自 api client 不统一。改地址时注意同步。
6. **服务重启后离线角标延迟**：约 60–90s（防抖），正常。

## 8. 环境信息

- 设备：树莓派（`raspberrypi`），Linux 6.1.0-rpi7-rpi-v8
- 项目：`/home/admin/Github/AI-RSS-Client`
- 服务：`ai-rss-client-display.service`（显示）、`ai-rss-client-fetch.service`（内容同步，每 20min）
- 后端：`8.134.202.27:8000`（AI-RSS-Hub，FastAPI + uvicorn，独立公网服务器）
- GitHub：`goodniuniu/AI-RSS-Client`（SSH），分支 `main`
- 硬件：Waveshare 3.52" 240×360 墨水屏
