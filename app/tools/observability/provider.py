from abc import ABC, abstractmethod

from app.agents.observation.schemas import (
    LogEntry,
    MetricSnapshot,
    TraceEntry,
    ExceptionEntry,
)


class ObservabilityProvider(ABC):

    @abstractmethod
    async def get_logs(
        self,
        service: str,
        minutes: int,
    ) -> list[LogEntry]:
        raise NotImplementedError

    @abstractmethod
    async def get_metrics(
        self,
        service: str,
        minutes: int,
    ) -> MetricSnapshot:
        raise NotImplementedError

    @abstractmethod
    async def get_traces(
        self,
        service: str,
        minutes: int,
    ) -> list[TraceEntry]:
        raise NotImplementedError

    @abstractmethod
    async def get_exceptions(
        self,
        service: str,
        minutes: int,
    ) -> list[ExceptionEntry]:
        raise NotImplementedError