"""
Monitoring utilities for system metrics and statistics
"""

import time
from datetime import datetime
from dataclasses import dataclass, field

from sqlalchemy import func, select

from config import config as app_config
from logger import get_logger
from utils import utc_now
from app.db.models import UserState


log = get_logger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data structure."""

    uptime_seconds: float
    requests_processed: int
    errors_encountered: int
    trusted_users: int
    spam_messages_blocked: int
    ai_requests_made: int
    ai_enabled: bool
    antispam_queue_size: int
    antispam_workers: int
    timestamp: datetime = field(default_factory=utc_now)


class SystemMonitor:
    """Monitor system metrics and statistics."""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.spam_blocked_count = 0
        self.ai_requests_count = 0
        self._last_metrics = {}

    def increment_request_count(self):
        """Increment the request counter."""
        self.request_count += 1

    def increment_error_count(self):
        """Increment the error counter."""
        self.error_count += 1

    def increment_spam_blocked_count(self):
        """Increment the spam blocked counter."""
        self.spam_blocked_count += 1

    def increment_ai_requests_count(self):
        """Increment the AI requests counter."""
        self.ai_requests_count += 1

    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time

    async def get_system_metrics(
        self, db_session=None, antispam_service=None
    ) -> SystemMetrics:
        """Get system metrics for admin panel display."""

        trusted_users = 0

        if db_session:
            try:

                trusted_users_result = await db_session.execute(
                    select(func.count(UserState.id)).where(
                        UserState.valid_messages >= app_config.bot.min_valid_messages  # noqa: E501
                    )
                )
                trusted_users = trusted_users_result.scalar()
            except Exception as e:
                log.warning("Could not retrieve database metrics: %s", e)

        antispam_queue_size = 0
        antispam_workers = 0
        ai_enabled = False

        if antispam_service:
            try:
                antispam_queue_size = antispam_service.queue.qsize()
                antispam_workers = antispam_service.workers
                ai_enabled = antispam_service.enable_ai_check
            except Exception as e:
                log.warning("Could not retrieve antispam metrics: %s", e)

        metrics = SystemMetrics(
            uptime_seconds=self.get_uptime(),
            requests_processed=self.request_count,
            errors_encountered=self.error_count,
            trusted_users=trusted_users,
            spam_messages_blocked=self.spam_blocked_count,
            ai_requests_made=self.ai_requests_count,
            ai_enabled=ai_enabled,
            antispam_queue_size=antispam_queue_size,
            antispam_workers=antispam_workers,
        )

        self._last_metrics = metrics
        return metrics

    def format_metrics_for_admin(self, metrics: SystemMetrics) -> str:
        """Format metrics for display in Telegram admin panel."""

        uptime_seconds = int(metrics.uptime_seconds)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        uptime_str = f"{days}d {hours}h {minutes}m"

        report = (
            "📊 <b>System Metrics Report</b>\n\n"
            f"⏱️ <b>Uptime:</b> {uptime_str}\n"
            f"📥 <b>Messages Processed:</b> {metrics.requests_processed}\n"
            f"❌ <b>Errors Encountered:</b> {metrics.errors_encountered}\n"
            f"🛡️ <b>Spam Blocked:</b> {metrics.spam_messages_blocked}\n"
            f"✅ <b>Trusted Users:</b> {metrics.trusted_users}\n"
            f"<b>AI Enabled:</b> {'Yes' if metrics.ai_enabled else 'No'}\n"
            f"<b>AI Requests:</b> {metrics.ai_requests_made}\n"
            f"<b>Queue Size:</b> {metrics.antispam_queue_size}\n"
            f"<b>Workers:</b> {metrics.antispam_workers}\n"
        )

        return report


system_monitor = SystemMonitor()
