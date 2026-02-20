# ABOUTME: Utility to create prompt for flow kg extraction agent.

import json
import uuid
from pathlib import Path

from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    get_logger,
    init_tracing,
    set_conversation_id,
)
from autobots_devtools_shared_lib.dynagent import (
    AgentMeta,
    BatchResult,
    batch_invoker,
    get_batch_enabled_agents,
)
from dotenv import load_dotenv

from autobots_orch_flow_studio.configs.constants import (
    KB_PATH,
)

logger = get_logger(__name__)
load_dotenv()
init_tracing()

APP_NAME = "orch-flow-studio"


def _compose_user_message(schema: dict, kb_path: str) -> str:
    """Build the user message containing KB_PATH and the dereferenced schema."""
    return json.dumps({"kb_path": kb_path, "schema": schema})


def _fetch_flows_list(filename: str) -> list[str]:
    """List all file names in the designer_flows folder.

    Args:
        filename: Optional directory name under data (e.g. MER-12345---Party-Feature).
            If empty, uses data/designer_flows directly.

    Returns:
        List of file names in data/designer_flows/ or data/<filename>/designer_flows/.
    """
    data_root = Path("/Users/saurabh/Documents/server/orch-ai-studio/data")
    models_path = data_root / "designer_flows"
    if not models_path.is_dir():
        logger.warning("Models path is not a directory: %s", models_path)
        return []
    records = []
    for p in models_path.iterdir():
        text = f"folder_name: {filename}, file_name: {p.name}"
        records.append(text)
    logger.info("Flows list: %s", records)
    return records


def build_flow(
    session_id: str | None = None,
    filename: str = "",
) -> BatchResult:
    """Orchestrate the flow KG build pipeline (steps 1-2).

    1. Retrieve the flow KG Schema for the ``flow_kg_extraction`` agent.
    2. Invoke the ``schema_processor`` agent with the schema and KB_PATH
       as the user message.  The agent generates an extraction guide and
       writes it to the workspace via *write_file*.

    Args:
        session_id: Optional session ID for tracing (auto-generated if None).
        enable_tracing: Whether to enable Langfuse tracing (default True).

    Returns:
        The complete final state dict from the schema_processor agent execution.

    Raises:
        ValueError: If the schema cannot be retrieved or the agent name is invalid.
    """

    # --- Step 1: Get flow KG Schema ----------------------------------------
    logger.info("Step 1 - Retrieving flow KG Schema for agent 'flow_generator'")
    # --- Step 2: Invoke schema_processor agent -----------------------------
    agent_name = "flow_generator"
    logger.info(f"Step 2 - invoking '{agent_name}' agent with KB_PATH={KB_PATH}")

    if session_id is None:
        session_id = str(uuid.uuid4())
    set_conversation_id(session_id)

    logger.info(f"🔑 Generated session_id: {session_id}")

    init_tracing()

    # Prepare trace metadata
    trace_metadata = TraceMetadata(
        session_id=session_id,
        app_name=APP_NAME,
        user_id=agent_name,
        tags=[APP_NAME, agent_name, "sync"],
    )

    logger.info(f"Invoking SYNC agent '{agent_name}' for {APP_NAME}")
    records = _fetch_flows_list(filename)
    result = batch_invoker(
        agent_name,
        records,
        trace_metadata=trace_metadata,
    )

    logger.info(f"Prompt generated successfully for {APP_NAME}")
    return result


if __name__ == "__main__":
    logger.info("Running flow-kb-builder")
    build_flow(filename="MER-12345---Party-Feature")
    # models_list = _fetch_flows_list("MER-12345---Party-Feature")
    # logger.info(f"Models list: {models_list}")
