# 后端摘要覆盖率排查清单

> 适用：后端 `8.134.202.27`（AI-RSS-Hub）｜ 关联客户端 `docs/HANDOFF.md` P1

## 0. 先建立正确认知（避免误判）

后端 `summarize_article_auto`（`app/services/summarizer.py:453`）按 `detect_content_language`
**对一篇文章只生成一种语言的摘要**：

| 内容语言判定 | 生成 | 落库 |
|---|---|---|
| 纯英文（英文源，如 TechCrunch） | 仅英文摘要 | `summary_en` 有值、`summary` 为空 |
| 纯中文（中文源） | 仅中文摘要 | `summary` 有值、`summary_en` 为空 |
| 混合 | 双语 | 两者都有 |

**所以"中文 `summary` 基本为空"是设计，不是故障**——英文 RSS 源的内容被判定为英文，
只该生成英文摘要。客户端已适配此设计（单摘要单栏显示）。**不要为英文文章强行补中文 summary，那是反设计。**

本清单真正要解决的是：**英文 `summary_en` 覆盖率仅 ~39%，61% 文章两种摘要都没有。**

## 1. 摘要生成机制（代码依据）

- 触发点：`rss_fetch_job`（每 `FETCH_INTERVAL_HOURS` 小时）抓取**新**文章后批量生成，
  调用链 `app/services/rss_fetcher.py:167` → `summarize_article_auto`。
- **只对本次新抓取的文章生成；入库时失败的老文章不会自动回补。**
- 落库逻辑（`rss_fetcher.py:177-185`）：zh/en 各自独立判断，含"失败/异常"字样或为空则不落库。
- 单条失败不影响其他：`asyncio.gather(..., return_exceptions=True)`（`rss_fetcher.py:170`）。

## 2. 39% 覆盖率可能的失败路径

| 路径 | 代码位置 | 结果 |
|---|---|---|
| 非限流异常（解析错、网络断、key 无效） | `_summarize_english_only` except → `return ""`（`summarizer.py:582-584`） | 不重试，不落库 |
| 429 限流 | `RateLimitError` 抛给 tenacity，重试 `SUMMARY_RETRY_ATTEMPTS` 次（退避 10–60s） | 5 次仍失败 → gather 捕获 → 跳过（`rss_fetcher.py:173-175`） |
| 超时 | `APITimeoutError`（`LLM_TIMEOUT=45`） | 同上，重试 |
| API key 失效 / 额度耗尽 | 所有调用失败 | 覆盖率断崖式下跌 |
| 老文章 | 入库时失败 | 永不回补 |

## 3. 排查命令（在 `8.134.202.27` 后端目录执行）

> 后端服务名以实际为准（看 `deploy.sh` 或 `systemctl list-units | grep -i rss`）；下文记作 `<svc>`。

### 3.1 数据库统计（表名以 `app/models` 为准，一般 `article` / `feed`）

```sql
-- 总体覆盖率
SELECT COUNT(*) total,
       SUM(CASE WHEN summary_en IS NOT NULL AND summary_en!='' THEN 1 ELSE 0 END) en,
       SUM(CASE WHEN summary    IS NOT NULL AND summary   !='' THEN 1 ELSE 0 END) zh,
       ROUND(100.0*SUM(CASE WHEN summary_en IS NOT NULL AND summary_en!='' THEN 1 ELSE 0 END)/COUNT(*)) en_pct
FROM article;

-- 按天：看是否某天起突降（指向部署/Key 问题）
SELECT DATE(created_at) d, COUNT(*) n,
       SUM(CASE WHEN summary_en IS NOT NULL AND summary_en!='' THEN 1 ELSE 0 END) en
FROM article GROUP BY DATE(created_at) ORDER BY d DESC LIMIT 14;

-- 按 feed：看是否某个源全失败（指向该源内容/抓取问题）
SELECT f.name, COUNT(*) n,
       SUM(CASE WHEN a.summary_en IS NOT NULL AND a.summary_en!='' THEN 1 ELSE 0 END) en
FROM article a JOIN feed f ON a.feed_id=f.id
GROUP BY f.id ORDER BY en ASC LIMIT 20;
```

### 3.2 日志失败原因（最直接）

```bash
# 失败类型分布
journalctl -u <svc> --since "24h ago" --no-pager \
  | grep -E "摘要生成失败|摘要生成异常|RateLimitError|429|超时|timeout|APITimeoutError" | tail -30

# 成功 vs 失败 计数
echo "成功:";  journalctl -u <svc> --since "24h ago" --no-pager | grep -cE "英文摘要生成成功"
echo "失败:";  journalctl -u <svc> --since "24h ago" --no-pager | grep -cE "英文摘要生成失败|摘要生成异常，跳过"
```

### 3.3 LLM 配置与连通性

```bash
grep -E "OPENAI_API_KEY|OPENAI_API_BASE|OPENAI_MODEL|LLM_TIMEOUT|MAX_CONCURRENT|SUMMARY_RETRY|FETCH_INTERVAL" .env
# 后端有 test_llm_connection（routes.py:223），看 /api/status 的 llm_configured 或直接调 /docs 里的测试接口
```

### 3.4 手动触发 + 实时观察

手动触发一次抓取，跟随日志看摘要阶段的成功/失败比：
```bash
# 触发（需 X-API-Token）
curl -X POST -H "X-API-Token: <token>" http://127.0.0.1:8000/api/feeds/fetch
journalctl -u <svc> -f | grep -E "摘要|summar|429|失败"
```

## 4. 可调项（提升覆盖率）

`.env` / `config.py`（括号为默认值）：

- `MAX_CONCURRENT_SUMMARIES`（3）：429 多就调低；富余就调高提吞吐。
- `SUMMARY_RETRY_ATTEMPTS`（5）：429 跨分钟窗口的重试次数，可适当上调。
- `LLM_TIMEOUT`（45）：长文章超时多就上调。
- `OPENAI_API_BASE` / `OPENAI_MODEL`（`gpt-3.5-turbo`）：换更稳/更便宜的兼容接口
  （代码注释提到可替换为 DeepSeek 等），注意 429 限流差异。

## 5. 老文章回补（可选，需写一次性脚本）

当前只对**新**文章生成摘要。若要让历史无摘要文章也有摘要，写脚本遍历
`summary_en IS NULL`（且内容为英文）的 article，复用 `summarize_article_auto` 回填：
参考 `rss_fetcher.py:148-189` 的批量 + 信号量 + 分批提交模式。

## 6. 排查顺序建议

1. 跑 3.2 看失败关键词 → 确定主因（429 / 超时 / key / 解析）。
2. 跑 3.1 按天统计 → 若某天起突降，对照那天是否有部署 / Key 变更。
3. 按主因调 4 中的对应配置，`./deploy.sh` 重新部署（仓库已固化校验-重启-验证流程）。
4. 触发一次抓取（3.4）验证成功率回升。
5. 视需要做 5 的老文章回补。

---

**客户端侧无需配合**：客户端已按单摘要设计适配（提交 `8477c10`），后端覆盖率提升后
下次同步（每 20min）自动显示更多英文摘要，无需客户端改动。
