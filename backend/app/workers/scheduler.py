"""APScheduler integration for periodic ingestion jobs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..core.settings import Settings, get_settings

JobHandler = Callable[[], Awaitable[None] | None]


class SchedulerService:
    """Wrapper around APScheduler to manage recurring jobs."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the scheduler service.

        Args:
            settings: Application settings containing scheduler configuration.
        """

        self._scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    def add_daily_job(self, func: JobHandler, *, hour: int = 3) -> None:
        """Register a daily job at the specified hour.

        Args:
            func: Callable executed on schedule. Supports sync and async callables.
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


def create_scheduler_service(*, settings: Settings | None = None) -> SchedulerService:
    """Factory for generating scheduler service instances.

    Args:
        settings: Optional settings override for the service. Defaults to the global configuration.

    Returns:
        SchedulerService: Configured scheduler service instance.
    """

    resolved_settings = settings or get_settings()
    return SchedulerService(settings=resolved_settings)
