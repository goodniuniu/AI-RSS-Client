"""
Backend Health Monitor
后端健康监控模块

周期性探测 AI-RSS-Hub 后端的可达性，维护在线/离线状态。
当状态发生翻转时记录日志（下线告警 / 恢复通知），供显示层
在墨水屏角标上提示"后端离线"，避免后端静默挂掉时长时间无人察觉。

设计要点：
- 轻量探测：GET {base_url}/api/health，短超时、不重试，避免阻塞显示主循环。
- 防抖：连续失败达到 failure_threshold 次才判定离线，避免偶发网络抖动误报。
- 线程安全：内部状态读写加锁。
- 可独立后台线程周期探测（start/stop），也可由调用方手动调用 update()。
"""

import threading
from datetime import datetime
from typing import Optional, Dict, Any

import requests

from ..utils.logger import get_logger

logger = get_logger(__name__)


class BackendHealthMonitor:
    """轻量后端健康探针。"""

    def __init__(self,
                 base_url: str,
                 check_interval_seconds: int = 60,
                 request_timeout_seconds: int = 3,
                 failure_threshold: int = 2,
                 health_endpoint: str = "/api/health"):
        """
        Args:
            base_url: 后端基础 URL，例如 http://8.134.202.27:8000
            check_interval_seconds: 后台线程探测周期（秒），最小 5
            request_timeout_seconds: 单次探测请求超时（秒），最小 1
            failure_threshold: 连续失败多少次才判定为离线（防抖），最小 1
            health_endpoint: 健康检查端点路径
        """
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
        self.health_endpoint = health_endpoint
        self.check_interval = max(5, int(check_interval_seconds))
        self.timeout = max(1, int(request_timeout_seconds))
        self.failure_threshold = max(1, int(failure_threshold))

        # 受锁保护的状态
        self._lock = threading.Lock()
        self._online: bool = True             # 乐观初值：假设在线，首次探测后修正
        self._consecutive_failures: int = 0
        self._last_check: Optional[datetime] = None
        self._last_success: Optional[datetime] = None
        self._last_error: Optional[str] = None

        # 后台线程
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------ #
    # 探测
    # ------------------------------------------------------------------ #
    def _probe(self) -> bool:
        """执行一次 HTTP 探测，返回后端是否健康。不抛异常。"""
        url = f"{self.base_url}{self.health_endpoint}"
        try:
            response = requests.get(url, timeout=self.timeout, allow_redirects=False)
            return response.status_code < 400
        except requests.exceptions.RequestException as e:
            # 连接拒绝 / 超时 / DNS 失败等，都视为不可达
            self._last_error = f"{type(e).__name__}: {e}"
            return False
        except Exception as e:  # 兜底：任何意外都不应让探针崩溃
            self._last_error = f"{type(e).__name__}: {e}"
            return False

    def update(self) -> bool:
        """执行一次探测并更新内部状态；返回当前是否判定为在线。

        状态翻转（在线↔离线）时记录日志。
        """
        online_now = self._probe()
        now = datetime.now()

        with self._lock:
            self._last_check = now
            prev_online = self._online  # 探测前的判定状态

            if online_now:
                self._consecutive_failures = 0
                self._last_success = now
                self._last_error = None
                new_online = True
            else:
                self._consecutive_failures += 1
                # 达到阈值才判定离线，否则保持原状（在线乐观、防抖）
                if self._consecutive_failures >= self.failure_threshold:
                    new_online = False
                else:
                    new_online = prev_online

            # 状态翻转告警
            if new_online != prev_online:
                if new_online:
                    logger.info(
                        f"✅ 后端恢复在线: {self.base_url} "
                        f"(上次成功: {self._fmt(self._last_success)})"
                    )
                else:
                    logger.warning(
                        f"⚠️ 后端离线: {self.base_url} "
                        f"(连续失败 {self._consecutive_failures}/{self.failure_threshold}, "
                        f"上次成功: {self._fmt(self._last_success)}, "
                        f"最近错误: {self._last_error})"
                    )

            self._online = new_online
            return self._online

    # ------------------------------------------------------------------ #
    # 后台线程
    # ------------------------------------------------------------------ #
    def start(self):
        """启动后台探测线程（守护线程，进程退出时自动结束）。"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="BackendHealthMonitor", daemon=True
        )
        self._thread.start()
        logger.info(
            f"后端健康监控已启动 (每 {self.check_interval}s 探测 {self.base_url}{self.health_endpoint})"
        )

    def _run(self):
        """后台循环：先立即探测一次，之后按周期探测。"""
        try:
            self.update()
        except Exception as e:
            logger.error(f"健康探测异常: {e}")

        # _stop_event.wait 超时返回 False（继续循环），被 stop 置位返回 True（退出）
        while not self._stop_event.wait(self.check_interval):
            try:
                self.update()
            except Exception as e:
                logger.error(f"健康探测异常: {e}")

    def stop(self):
        """停止后台探测线程。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("后端健康监控已停止")

    # ------------------------------------------------------------------ #
    # 状态访问
    # ------------------------------------------------------------------ #
    @property
    def is_online(self) -> bool:
        """当前是否判定后端在线（线程安全）。"""
        with self._lock:
            return self._online

    def get_status(self) -> Dict[str, Any]:
        """返回健康状态快照（线程安全）。"""
        with self._lock:
            return {
                "base_url": self.base_url,
                "online": self._online,
                "consecutive_failures": self._consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "last_check": self._fmt(self._last_check),
                "last_success": self._fmt(self._last_success),
                "last_error": self._last_error,
                "check_interval_seconds": self.check_interval,
            }

    @staticmethod
    def _fmt(dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat(timespec="seconds") if dt else None
