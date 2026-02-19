# ABOUTME: Shared test fixture helpers importable by domain-level conftest.py files.

from collections.abc import Generator


def orch_flow_studio_tools_registered() -> Generator[None, None, None]:
    """Register Orch Flow Studio tools for testing; reset after use.

    Usage in conftest.py:
        from tests.helpers import orch_flow_studio_tools_registered

        @pytest.fixture
        def orch_flow_studio_registered():
            yield from orch_flow_studio_tools_registered()
    """
    from autobots_devtools_shared_lib.dynagent import AgentMeta
    from autobots_devtools_shared_lib.dynagent.tools.tool_registry import (
        _reset_usecase_tools,
    )

    from autobots_orch_flow_studio.domains.orch_flow_studio.tools import register_orch_flow_studio_tools

    _reset_usecase_tools()
    AgentMeta.reset()
    register_orch_flow_studio_tools()
    yield
    _reset_usecase_tools()
    AgentMeta.reset()
