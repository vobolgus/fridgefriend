from app.core.analytics_client import AmplitudeClient, AnalyticsInterface, NoopAnalytics
from app.core.config import Settings, settings

_amplitude_client: AnalyticsInterface | None = None


def get_settings() -> Settings:
    return settings


def get_analytics_client() -> AnalyticsInterface:
    global _amplitude_client
    if _amplitude_client is None:
        if settings.AMPLITUDE_API_KEY:
            _amplitude_client = AmplitudeClient(api_key=settings.AMPLITUDE_API_KEY)
        else:
            _amplitude_client = NoopAnalytics()
    return _amplitude_client
