from app.config.settings import settings

from app.tools.observability.mock_provider import (
    MockApplicationInsightsProvider,
)


def create_observability_provider():

    mode = settings.observability_mode.lower()

    if mode == "azure":

        from app.tools.observability.azure_provider import (
            AzureApplicationInsightsProvider,
        )

        if not settings.azure_application_insights_resource_id:
            raise ValueError(
                "AZURE_APPLICATION_INSIGHTS_RESOURCE_ID "
                "is required when OBSERVABILITY_MODE=azure"
            )

        return AzureApplicationInsightsProvider(
            settings.azure_application_insights_resource_id
        )

    if mode == "mock":

        return MockApplicationInsightsProvider()

    raise ValueError(
        f"Unsupported observability mode: {mode}"
    )