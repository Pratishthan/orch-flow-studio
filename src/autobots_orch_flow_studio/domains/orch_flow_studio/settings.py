# ABOUTME: Orch Flow Studio domain-specific settings.
# ABOUTME: Extends AppSettings with orch_flow_studio-specific configuration (default city, joke category, etc.).

from pydantic import Field

from autobots_orch_flow_studio.configs.settings import AppSettings, init_app_settings


class OrchFlowStudioSettings(AppSettings):
    """Orch Flow Studio domain settings.
    Extends AppSettings with orch_flow_studio-specific configuration."""

    # Orch Flow Studio-specific settings
    default_city: str = Field(default="London", description="Default city for weather lookups")
    default_joke_category: str = Field(default="general", description="Default joke category")

    # Override app_name default for orch_flow_studio domain
    app_name: str = Field(default="orch_flow_studio", description="Application name")


def get_orch_flow_studio_settings() -> OrchFlowStudioSettings:
    """Get orch_flow_studio settings instance."""
    return OrchFlowStudioSettings()


def init_orch_flow_studio_settings() -> OrchFlowStudioSettings:
    """Initialize orch_flow_studio settings and register with shared-lib.

    Chains: orch_flow_studio → app → dynagent

    Returns:
        The initialized OrchFlowStudioSettings instance.

    Call at app startup.
    """
    s = get_orch_flow_studio_settings()
    init_app_settings(s)
    return s
