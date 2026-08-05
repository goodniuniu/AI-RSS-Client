# 后端服务排查 SOP（目标服务器：8.134.202.27）

> 本文档供运维 / AI 执行：当树莓派墨水屏客户端报告后端 `http://8.134.202.27:8000`
> **Connection refused**（或屏幕角标显示"⚠离线"）时，按本流程排查并恢复后端服务。

## 背景

- 客户端（树莓派）通过 `http://8.134.202.27:8000` 访问 **AI-RSS-Hub** 后端（FastAPI + uvicorn）。
- 典型故障症状：主机 `ping` 通，但 **8000 端口无服务监听**（`Connection refused`），
  即后端进程未运行 / 已崩溃。
- 客户端表现：拉不到新文章（屏幕反复显示同一篇旧文章）、二维码加载失败、
  屏幕左上角出现"⚠离线"角标。

## 成功标准（验证用）

满足以下全部条件才算恢复：

```bash
sudo ss -ltnp | grep ':8000'                        # ① 端口在 LISTEN
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/health     # ② 返回 200
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/articles   # ③ 返回 200
```

④ 在树莓派侧确认（公网可达）：

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://8.134.202.27:8000/api/health   # 返回 200
```

> ⚠️ 这是生产服务：**先查日志找根因，再重启**（否则可能立刻再次崩溃）；
> 不要删数据；改配置前先备份。

---

## Step 1 · 确认现状

```bash
# 端口有没有人监听？（期望看到 LISTEN；若为空 = 服务没跑）
sudo ss -ltnp | grep ':8000'

# 有没有相关进程？
ps aux | grep -iE "uvicorn|gunicorn|fastapi|rss|ai-rss|main.py" | grep -v grep

# 系统最近有没有 OOM 杀进程？
sudo dmesg -T | grep -iE "killed process|out of memory|oom" | tail -20

# 最近系统级日志
sudo journalctl --since "7 days ago" --no-pager | grep -iE "rss|uvicorn|8000|killed" | tail -40
```

判断：

- `ss` 看不到 8000、`ps` 也没相关进程 → 服务确实没在跑，进 **Step 2** 定位启动方式。
- `dmesg` 有 OOM → 内存不足被杀，进 **Step 4** 看根因。

## Step 2 · 判断部署方式（四选一，命中即跳到对应小节）

```bash
sudo systemctl list-units --type=service --all | grep -iE "rss|ai-rss|article"   # ① systemd?
sudo docker ps -a | grep -iE "rss|ai-rss|8000|article"                            # ② docker?
command -v pm2 >/dev/null && sudo pm2 list                                        # ③ pm2?
ls -la ~ /opt /srv /home 2>/dev/null | grep -iE "rss|AI-RSS"                      # ④ 找项目目录
```

### 2A · systemd 服务

```bash
SERV=$(sudo systemctl list-units --type=service --all | grep -iE "rss|ai-rss|article" | awk '{print $1}' | head -1)
echo "服务名: $SERV"
sudo systemctl status "$SERV" --no-pager -l | head -40            # 状态 + 最近日志
sudo journalctl -u "$SERV" -n 200 --no-pager                      # 完整日志，重点看崩溃前最后几行
sudo systemctl restart "$SERV"                                    # 重启
sudo systemctl enable "$SERV"                                     # 确保开机自启
```

### 2B · Docker

```bash
CID=$(sudo docker ps -a | grep -iE "rss|ai-rss|8000" | awk '{print $1}' | head -1)
sudo docker ps -a --filter "id=$CID"                              # 看 STATUS（Exited? 重启次数?）
sudo docker logs --tail 200 "$CID"                                # 崩溃日志
sudo docker inspect "$CID" --format '{{.State.Status}} | OOM={{.State.OOMKilled}} | Restarts={{.RestartCount}}'
sudo docker start "$CID"                                          # 启动；反复崩再进 Step 4
```

### 2C · pm2

```bash
sudo pm2 list
sudo pm2 logs --lines 200 --nostream
sudo pm2 restart all       # 或指定 app 名
sudo pm2 save              # 保存进程列表（配合 pm2 startup 实现开机自启）
```

### 2D · 以上都没命中（裸进程 / nohup / screen / tmux 跑的）

项目根目录大概率含 `main.py` + `requirements.txt`：

```bash
# 找项目根（含 FastAPI/uvicorn 入口）
sudo find /home /opt /srv /root -maxdepth 4 -name "main.py" 2>/dev/null \
  | xargs grep -l -iE "fastapi|uvicorn" 2>/dev/null
# 看启动脚本 / README
ls <项目目录>; cat <项目目录>/README* 2>/dev/null; cat <项目目录>/start*.sh 2>/dev/null
```

找到启动方式后，**建议补一个 systemd unit 或 docker-compose 把它常态化**，否则下次服务器重启又会丢失。

## Step 3 · 验证恢复

回到 [成功标准](#成功标准验证用) 的四条命令，全部为 LISTEN / 200 即恢复。
客户端约 **20 分钟**（`services.interval_minutes`）同步一次新文章；屏幕角标"⚠离线"会在
探针连续探测成功后自动消失（默认 60s 探测周期）。

## Step 4 · 重启后又立刻崩 —— 看根因

按概率排序排查：

1. **OOM / 内存不足**：`sudo dmesg -T | grep -i oom`；`free -h`；小内存云主机易触发。
2. **端口被占**：`sudo ss -ltnp | grep ':8000'` 看是否别的进程抢占了 8000。
3. **配置 / 数据库问题**：日志搜 `OperationalError`、`no such table`、`Permission denied`、`Address already in use`。
4. **磁盘满**：`df -h`；满了会导致数据库写不进、服务起不来。
5. **依赖 / Python 环境损坏**：日志搜 `ImportError` / `ModuleNotFoundError` → 在对应 venv 里 `pip install -r requirements.txt`。

## Step 5 · 收尾

- 确认**开机自启**已开启：`systemctl enable` / `docker update --restart=always` / `pm2 startup && pm2 save`。
  避免服务器重启后又静默断连数天。
- 记录结论：崩溃原因、所做修复、是否需要后续加固（加 swap / 加监控告警）。

---

## 附：客户端侧的健康探针

客户端（`src/services/health_monitor.py`）现已内置后端健康探针：

- 默认每 60s 探测一次 `GET {base_url}/api/health`（超时 3s，连续失败 2 次判离线）。
- 离线时在墨水屏 header 左上角显示"⚠离线"角标，并在日志中记录 `WARNING`。
- 恢复时自动清除角标并记录 `INFO`。
- 可在 `config.yml` 的 `health_monitor` 节调整周期 / 阈值。
