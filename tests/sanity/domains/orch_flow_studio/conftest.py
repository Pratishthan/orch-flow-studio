# ABOUTME: Pytest fixtures for Orch Flow Studio domain sanity tests.

import pytest

from tests.helpers import orch_flow_studio_tools_registered


@pytest.fixture
def orch_flow_studio_registered():
    """Register Orch Flow Studio tools; reset after test."""
    yield from orch_flow_studio_tools_registered()
