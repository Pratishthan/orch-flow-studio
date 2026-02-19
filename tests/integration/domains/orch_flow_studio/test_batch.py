# ABOUTME: Integration tests for Orch Flow Studio batch processing.

import pytest

from autobots_orch_flow_studio.domains.orch_flow_studio.orch_flow_studio_batch import orch_flow_studio_batch


@pytest.fixture(autouse=True)
def setup_orch_flow_studio(orch_flow_studio_registered):
    """Ensure Orch Flow Studio tools are registered before each test."""
    pass


def test_orch_flow_studio_batch_invalid_agent():
    """Test that orch_flow_studio_batch raises error for non-batch-enabled agents."""
    with pytest.raises(ValueError, match="not enabled for batch processing"):
        orch_flow_studio_batch("welcome_agent", ["test prompt"], user_id="test_user")


def test_orch_flow_studio_batch_empty_records(orch_flow_studio_registered):
    """Test that orch_flow_studio_batch raises error for empty records."""
    with pytest.raises(ValueError, match="records must not be empty"):
        orch_flow_studio_batch("joke_agent", [], user_id="test_user")


@pytest.mark.skipif(
    True,
    reason="Requires GOOGLE_API_KEY and full agent setup - run manually",
)
def test_orch_flow_studio_batch_joke_agent_smoke(orch_flow_studio_registered):
    """Smoke test for joke_agent batch processing."""
    prompts = [
        "Tell me a programming joke",
        "What's a funny dad joke?",
    ]

    result = orch_flow_studio_batch("joke_agent", prompts)

    assert result.total == 2
    assert len(result.results) == 2
    # In real execution, we'd expect successes, but this is marked as manual-only
