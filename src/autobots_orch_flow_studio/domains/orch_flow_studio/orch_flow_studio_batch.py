# ABOUTME: Orch Flow Studio-scoped batch entry point — validates against Orch Flow Studio's agent set.
# ABOUTME: Delegates to dynagent's batch_invoker after the Orch Flow Studio gate passes.

import uuid

from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    get_logger,
    init_tracing,
    set_conversation_id,
)
from autobots_devtools_shared_lib.dynagent import BatchResult, batch_invoker
from dotenv import load_dotenv

from autobots_orch_flow_studio.domains.orch_flow_studio.settings import init_orch_flow_studio_settings

logger = get_logger(__name__)
load_dotenv()
init_orch_flow_studio_settings()

# Application name for tracing and identification
APP_NAME = "orch_flow_studio_batch"


def _get_orch_flow_studio_batch_agents() -> list[str]:
    """Load batch-enabled agents from agents.yaml."""
    from autobots_devtools_shared_lib.dynagent import get_batch_enabled_agents

    return get_batch_enabled_agents()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def orch_flow_studio_batch(agent_name: str, records: list[str], user_id: str) -> BatchResult:
    """Run a batch through dynagent, gated to Orch Flow Studio batch-enabled agents only.

    Args:
        agent_name: Must be a batch-enabled agent from agents.yaml.
        records:    Non-empty list of plain-string prompts.
        user_id:    User ID for tracing.

    Returns:
        BatchResult forwarded from batch_invoker.

    Raises:
        ValueError: If agent_name is not batch-enabled or records is empty.
    """
    session_id = str(uuid.uuid4())
    set_conversation_id(session_id)
    logger.info(
        f"orch_flow_studio_batch starting: agent={agent_name} records={len(records)} user_id={user_id}"
    )

    orch_flow_studio_agents = _get_orch_flow_studio_batch_agents()

    if agent_name not in orch_flow_studio_agents:
        raise ValueError(
            f"Agent '{agent_name}' is not enabled for batch processing. "
            f"Valid batch-enabled agents: {', '.join(orch_flow_studio_agents)}"
        )

    if not records:
        raise ValueError("records must not be empty")

    init_tracing()

    trace_metadata = TraceMetadata.create(
        session_id=session_id,
        app_name=f"{APP_NAME}_{agent_name}-batch_invoker",
        user_id=user_id,
        tags=[APP_NAME, agent_name, "batch"],
    )

    result = batch_invoker(
        agent_name,
        records,
        trace_metadata=trace_metadata,
    )

    logger.info(
        f"orch_flow_studio_batch complete: agent={agent_name} successes={len(result.successes)} "
        f"failures={len(result.failures)}"
    )

    return result


# ---------------------------------------------------------------------------
# Manual smoke runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from autobots_orch_flow_studio.domains.orch_flow_studio.tools import register_orch_flow_studio_tools

    register_orch_flow_studio_tools()

    smoke_prompts = [
        "Tell me a programming joke",
        "What's a funny dad joke about coding?",
        "Can you tell a knock-knock joke?",
        "Tell me a joke about debugging",
        "What's your best programming joke?",
        "Tell me a general joke",
        "Give me another programming joke",
        "What's a good dad joke?",
        "Tell me a joke about Python",
        "Can you tell me a funny joke about databases?",
    ]

    batch_result = orch_flow_studio_batch("joke_agent", smoke_prompts, "BATCH_USER")
    for record in batch_result.results:
        if record.success:
            logger.info(f"Record {record.index} succeeded:\n{record.output}\n")
        else:
            logger.error(f"Record {record.index} failed:\n{record.error}\n")
