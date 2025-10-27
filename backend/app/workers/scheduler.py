"""APScheduler integration for periodic ingestion jobs."""

from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..core.settings import get_settings


class SchedulerService:
    """Wrapper around APScheduler to manage recurring jobs."""

    def __init__(self) -> None:
        settings = get_settings()
        self._scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    def add_daily_job(self, func: Callable[[], None], *, hour: int = 3) -> None:
        """Register a daily job at the specified hour.

        Args:
            func: Callable executed on schedule.
            hour: Hour of the day in scheduler timezone.
        """

        self._scheduler.add_job(func, "cron", hour=hour, id=f"daily-{func.__name__}")

    def start(self) -> None:
        """Start the underlying scheduler."""

        if not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self) -> None:
        """Shut down the scheduler gracefully."""

        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)


scheduler_service = SchedulerService()
