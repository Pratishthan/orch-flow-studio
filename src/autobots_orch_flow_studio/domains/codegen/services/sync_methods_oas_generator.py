# ABOUTME: Utility to create prompt for node kg extraction agent.

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


def _fetch_models_list(filename: str) -> list[str]:
    """Fetch the list of model names from the input JSON file.

    Reads 1-models.json from data/<filename>/json/ and returns the top-level
    keys as a list of strings.

    Args:
        filename: Directory name under INPUT_DATA_BASE_PATH (e.g. MER-12345---Party-Feature).

    Returns:
        List of first-level keys from the JSON (model names).
    """
    models_path = Path(
        "/Users/saurabh/Documents/server/orch-ai-studio/data",
        filename,
        "json",
        "2-sync-methods.json",
    )
    with models_path.open(encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Models list: {data}")
    records = []
    for endpoint in data.keys():
        model_name = data[endpoint]["modelName"]
        text = f"folder_name: {filename}, model: {model_name} and endpoint: {endpoint}"
        records.append(text)
    return records


def build_sync_oas(
    session_id: str | None = None,
    filename: str = "",
) -> BatchResult:
    """Orchestrate the Node KG build pipeline (steps 1-2).

    1. Retrieve the Node KG Schema for the ``node_kg_extraction`` agent.
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

    # --- Step 1: Get Node KG Schema ----------------------------------------
    logger.info("Step 1 - Retrieving Node KG Schema for agent 'model_oas_generator'")
    # --- Step 2: Invoke schema_processor agent -----------------------------
    agent_name = "sync_oas_generator"
    logger.info(f"Step 2 - invoking '{agent_name}' agent with KB_PATH={KB_PATH}")

    if session_id is None:
        session_id = str(uuid.uuid4())
    set_conversation_id(session_id)

    logger.info(f"🔑 Generated session_id: {session_id}")

    # Prepare trace metadata
    trace_metadata = TraceMetadata(
        session_id=session_id,
        app_name=APP_NAME,
        user_id=agent_name,
        tags=[APP_NAME, agent_name, "sync"],
    )

    logger.info(f"Invoking SYNC agent '{agent_name}' for {APP_NAME}")
    records = _fetch_models_list(filename)
    result = batch_invoker(
        agent_name,
        records,
        trace_metadata=trace_metadata,
    )

    logger.info(f"Prompt generated successfully for {APP_NAME}")
    return result


if __name__ == "__main__":
    logger.info("Running node-kb-builder")
    build_result = build_sync_oas(filename="MER-12345---Party-Feature")
    # models_list = _fetch_models_list("MER-12345---Party-Feature")
    # logger.info(f"Models list: {models_list}")
