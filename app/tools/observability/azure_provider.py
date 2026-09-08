from datetime import timedelta, datetime, timezone

from azure.identity.aio import DefaultAzureCredential
from azure.monitor.query.aio import LogsQueryClient
from azure.monitor.query import LogsQueryStatus

from app.agents.observation.schemas import (
    LogEntry,
    MetricSnapshot,
    TraceEntry,
    ExceptionEntry,
)

from app.tools.observability.provider import (
    ObservabilityProvider,
)

class AzureApplicationInsightsProvider(
    ObservabilityProvider
):

    def __init__(self, resource_id: str):

        self.resource_id = resource_id

        self.credential = DefaultAzureCredential()

        self.client = LogsQueryClient(
            self.credential
        )

    async def get_logs(
        self,
        service: str,
        minutes: int
    ) -> list[LogEntry]:

        query = """
        AppTraces
        | where TimeGenerated > ago({minutes}m)
        | where AppRoleName == "{service}"
        | project
            TimeGenerated,
            SeverityLevel,
            Message,
            AppRoleName
        | order by TimeGenerated desc
        """.format(
            minutes=minutes,
            service=service
        )

        response = await self.client.query_resource(
            self.resource_id,
            query,
            timespan=timedelta(minutes=minutes)
        )

        if response.status != LogsQueryStatus.SUCCESS:
            return []

        logs = []

        for table in response.tables:

            for row in table.rows:

                data = dict(
                    zip(table.columns, row)
                )

                logs.append(
                    LogEntry(
                        timestamp=data["TimeGenerated"],
                        level=str(
                            data.get(
                                "SeverityLevel",
                                "INFO"
                            )
                        ),
                        message=data.get(
                            "Message",
                            ""
                        ),
                        service=service
                    )
                )

        return logs

    async def get_metrics(
        self,
        service: str,
        minutes: int
    ) -> MetricSnapshot:

        # For the first implementation we can derive
        # request/error/latency metrics from AppRequests.

        query = """
        AppRequests
        | where TimeGenerated > ago({minutes}m)
        | where AppRoleName == "{service}"
        | summarize
            request_count=count(),
            error_count=countif(Success == false),
            p50=percentile(DurationMs, 50),
            p95=percentile(DurationMs, 95)
        """.format(
            minutes=minutes,
            service=service
        )

        response = await self.client.query_resource(
            self.resource_id,
            query,
            timespan=timedelta(minutes=minutes)
        )

        request_count = 0
        error_count = 0
        p50 = 0
        p95 = 0

        if response.status == LogsQueryStatus.SUCCESS:

            for table in response.tables:

                for row in table.rows:

                    data = dict(
                        zip(table.columns, row)
                    )

                    request_count = (
                        data.get("request_count") or 0
                    )

                    error_count = (
                        data.get("error_count") or 0
                    )

                    p50 = data.get("p50") or 0
                    p95 = data.get("p95") or 0

        error_rate = (
            (error_count / request_count) * 100
            if request_count
            else 0
        )

        return MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            service=service,

            request_count=request_count,
            error_count=error_count,

            error_rate=error_rate,

            latency_p50_ms=float(p50),
            latency_p95_ms=float(p95),

            # We'll connect these later to Azure Monitor
            cpu_percent=0,
            memory_percent=0
        )

    async def get_traces(
        self,
        service: str,
        minutes: int
    ) -> list[TraceEntry]:

        query = """
        AppRequests
        | where TimeGenerated > ago({minutes}m)
        | where AppRoleName == "{service}"
        | project
            TimeGenerated,
            Id,
            OperationName,
            DurationMs,
            Success
        | order by TimeGenerated desc
        | take 100
        """.format(
            minutes=minutes,
            service=service
        )

        response = await self.client.query_resource(
            self.resource_id,
            query,
            timespan=timedelta(minutes=minutes)
        )

        traces = []

        if response.status == LogsQueryStatus.SUCCESS:

            for table in response.tables:

                for row in table.rows:

                    data = dict(
                        zip(table.columns, row)
                    )

                    traces.append(
                        TraceEntry(
                            timestamp=data["TimeGenerated"],
                            trace_id=str(
                                data.get("Id", "")
                            ),
                            span_id="request",
                            service=service,
                            operation=data.get(
                                "OperationName",
                                "unknown"
                            ),
                            duration_ms=float(
                                data.get(
                                    "DurationMs",
                                    0
                                )
                            ),
                            status=(
                                "OK"
                                if data.get("Success")
                                else "ERROR"
                            )
                        )
                    )

        return traces

    async def get_exceptions(
        self,
        service: str,
        minutes: int
    ) -> list[ExceptionEntry]:

        query = """
        AppExceptions
        | where TimeGenerated > ago({minutes}m)
        | where AppRoleName == "{service}"
        | project
            TimeGenerated,
            Type,
            OuterMessage,
            OperationName
        | order by TimeGenerated desc
        | take 100
        """.format(
            minutes=minutes,
            service=service
        )

        response = await self.client.query_resource(
            self.resource_id,
            query,
            timespan=timedelta(minutes=minutes)
        )

        exceptions = []

        if response.status == LogsQueryStatus.SUCCESS:

            for table in response.tables:

                for row in table.rows:

                    data = dict(
                        zip(table.columns, row)
                    )

                    exceptions.append(
                        ExceptionEntry(
                            timestamp=data["TimeGenerated"],
                            service=service,
                            exception_type=data.get(
                                "Type",
                                "UnknownException"
                            ),
                            message=data.get(
                                "OuterMessage",
                                ""
                            ),
                            operation=data.get(
                                "OperationName"
                            )
                        )
                    )

        return exceptions

    async def close(self):

        await self.client.close()

        await self.credential.close()