# ABOUTME: Orch Flow Studio-specific Chainlit entry point for the orch_flow_studio_chat use case.
# ABOUTME: Wires tracing, OAuth, and the shared streaming helper.

import json
import os
from typing import TYPE_CHECKING, Any

import chainlit as cl
import httpx
from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    flush_tracing,
    get_logger,
    init_tracing,
    set_conversation_id,
)
from autobots_devtools_shared_lib.dynagent import create_base_agent
from autobots_devtools_shared_lib.dynagent.ui import stream_agent_events
from dotenv import load_dotenv

from autobots_orch_flow_studio.common.utils.formatting import format_structured_output
from autobots_orch_flow_studio.domains.orch_flow_studio.settings import (
    init_orch_flow_studio_settings,
)
from autobots_orch_flow_studio.domains.orch_flow_studio.tools import register_orch_flow_studio_tools

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__file__)

# Application name for tracing and identification
APP_NAME = "orch_flow_studio_chat"

# Register Orch Flow Studio settings so shared-lib (dynagent) uses the same instance.
init_orch_flow_studio_settings()

# Registration must precede AgentMeta.instance() (called inside create_base_agent).
register_orch_flow_studio_tools()

NODE_RED_URL = os.environ.get("NODE_RED_URL", "http://localhost:1880").rstrip("/")
FLOWS_API_URL = f"{NODE_RED_URL}/flows"
FLOW_EXT = ".json"
# Path where flow JSON is saved/loaded (set NODE_RED_FLOW_PATH in env)
NODE_RED_FLOW_PATH = os.environ.get(
    "NODE_RED_FLOW_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "node_red_flows", "saved_flows.json"),
)


def _flows_headers():
    return {"Node-RED-API-Version": "v1", "Content-Type": "application/json"}


async def _get_flows(client: httpx.AsyncClient):
    """GET current flows from Node-RED (v1 = array of nodes)."""
    r = await client.get(FLOWS_API_URL, headers=_flows_headers())
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else data.get("flows", data)


async def _post_flows(client: httpx.AsyncClient, flows):
    """POST flows to Node-RED (v1 array)."""
    r = await client.post(FLOWS_API_URL, json=flows, headers=_flows_headers())
    r.raise_for_status()


def _flow_file_exists():
    return os.path.isfile(NODE_RED_FLOW_PATH)


def _read_flow_file():
    with open(NODE_RED_FLOW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_flows_from_path(path: str):
    """Read flow JSON from a path; return list of flow nodes (handles array or {flows: []})."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "flows" in data:
        return data["flows"]
    return data if isinstance(data, list) else []


def _write_flow_file(flows, path: str):
    """Write flows JSON to the given absolute path."""
    path = os.path.abspath(path.strip())
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(flows, f, indent=2)


def _open_nodered_message():
    return (
        f"**Open in new tab:** [Open Node-RED Playground]({NODE_RED_URL}) — "
        "right-click → Open link in new tab, or Ctrl/Cmd+Click."
    )


async def _load_flows_into_nodered_then_send(flows, source_label: str):
    """POST flows to Node-RED and send success message with open link."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        await _post_flows(client, flows)
    await cl.Message(
        content=f"Flow loaded from {source_label} into Node-RED. You can work on it and update it.\n\n{_open_nodered_message()}"
    ).send()


def _nodered_tool_actions():
    """Return the list of Node-RED sub-tool actions (for Tools section)."""
    flow_exists = _flow_file_exists()
    return [
        cl.Action(
            name="open_nodered",
            label="Open Node-RED",
            payload={"action": "open"},
            tooltip="Open Node-RED in a new tab",
        ),
        cl.Action(
            name="save_flow",
            label="Save flow to file",
            payload={"action": "save"},
            tooltip="Save current Node-RED flows to an absolute path (you will be asked for the path)",
        ),
        cl.Action(
            name="load_flow_open",
            label="Load flow and open Node-RED"
            if flow_exists
            else "Load flow and open Node-RED (no saved file yet)",
            payload={"action": "load_open"},
            tooltip="Load default saved flow into Node-RED, then open editor",
        ),
        cl.Action(
            name="browse_saved_flows",
            label="Browse saved flows",
            payload={"action": "browse"},
            tooltip="Enter a directory path to list flow JSON files; click one to load and open",
        ),
        cl.Action(
            name="load_flow_upload",
            label="Load from uploaded file",
            payload={"action": "upload"},
            tooltip="Upload a flow JSON file from your computer, then load into Node-RED and open",
        ),
    ]


NODERED_COMMAND_ID = "nodered_tools"


def _nodered_tools_message_content():
    """Content for the Node-RED tools panel: choose action + default load path."""
    content = "**Node-RED tools** — choose an action:"
    if NODE_RED_FLOW_PATH:
        content += f"\n\nDefault load path: `{NODE_RED_FLOW_PATH}`"
    return content


# Check if OAuth is configured
OAUTH_ENABLED = bool(
    os.getenv("OAUTH_GITHUB_CLIENT_ID")
    and os.getenv("OAUTH_GITHUB_CLIENT_SECRET")
    and os.getenv("CHAINLIT_AUTH_SECRET")
)

# Only register OAuth callback if OAuth is enabled
if OAUTH_ENABLED:

    @cl.oauth_callback  # type: ignore[arg-type]
    def oauth_callback(
        provider_id: str,
        token: str,  # noqa: ARG001
        raw_user_data: dict,
        default_user: cl.User,
    ) -> cl.User | None:
        """Handle OAuth callback from GitHub.

        Args:
            provider_id: The OAuth provider ID (e.g., "github").
            token: The OAuth access token.
            raw_user_data: Raw user data from the provider.
            default_user: Default user object created by Chainlit.

        Returns:
            The authenticated user or None if authentication fails.
        """
        if provider_id != "github":
            logger.warning(f"Unsupported OAuth provider: {provider_id}")
            return None

        username = raw_user_data.get("login", "unknown")
        logger.info(f"User authenticated via GitHub: {username}")
        return default_user
else:
    # No OAuth - anonymous access
    logger.info("OAuth is not configured - anonymous access")
    pass


def _get_user_identifier() -> str:
    """User ID for tracing and state; defaults to anonymous when OAuth is off."""
    user = cl.user_session.get("user")
    if user:
        return user.identifier[:200]
    return f"anonymous-{cl.context.session.thread_id}"[:200]


@cl.on_chat_start
async def start():
    """Initialize the chat session with the welcome agent."""
    # Create agent instance once and store it in session
    init_tracing()
    base_agent = create_base_agent()
    cl.user_session.set("base_agent", base_agent)

    # Prepare trace metadata for Langfuse observability (session-level)
    user_id = _get_user_identifier()
    cl.user_session.set("user_id", user_id)

    trace_metadata = TraceMetadata.create(
        session_id=cl.context.session.thread_id,
        app_name=APP_NAME,
        user_id=user_id,
        tags=[APP_NAME],
    )
    set_conversation_id(cl.context.session.thread_id)
    cl.user_session.set("trace_metadata", trace_metadata)

    await cl.Message(content="Hello! I'm Orch Flow Studio. How can I help you today?").send()
    await cl.context.emitter.set_commands(
        [
            {
                "id": NODERED_COMMAND_ID,
                "description": "Node-RED Tools",
                "icon": "workflow",
                "button": False,
            },
        ]
    )


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages from the user."""
    set_conversation_id(cl.context.session.thread_id)
    if getattr(message, "command", None) == NODERED_COMMAND_ID:
        await cl.Message(
            content=_nodered_tools_message_content(),
            actions=_nodered_tool_actions(),
        ).send()
        return
    config: RunnableConfig = {
        "configurable": {
            "thread_id": cl.context.session.thread_id,
        },
        "recursion_limit": 50,
        "run_name": APP_NAME,  # Set trace name for Langfuse
    }

    # Reuse the same agent instance from session
    base_agent = cl.user_session.get("base_agent")
    if not base_agent:
        await cl.Message(content="Error: Session initialization failed. Please refresh.").send()
        return

    user_id = cl.user_session.get("user_id")

    input_state: dict[str, Any] = {
        "messages": [{"role": "user", "content": message.content}],
        "user_id": user_id,
        "app_name": APP_NAME,
        "session_id": cl.context.session.thread_id,
    }

    # Retrieve trace metadata from session
    trace_metadata = cl.user_session.get("trace_metadata")

    result = await stream_agent_events(
        agent=base_agent,
        input_state=input_state,
        config=config,
        on_structured_output=format_structured_output,
        enable_tracing=True,
        trace_metadata=trace_metadata,
    )
    logger.debug(f"Agent execution completed with result: {result}")


@cl.action_callback("open_nodered")
async def on_open_nodered(action: cl.Action):
    """Open Node-RED in a new tab (send link to user)."""
    await cl.Message(content=_open_nodered_message()).send()


@cl.action_callback("save_flow")
async def on_save_flow(action: cl.Action):
    """Ask for absolute path, then fetch flows from Node-RED and save to that path."""
    res = await cl.AskUserMessage(
        content="Enter the **absolute path** where the flow JSON should be saved (e.g. `/home/user/flows.json` or `C:\\flows.json`):",
        timeout=120,
        raise_on_timeout=False,
    ).send()
    if not res or not res.get("output"):
        await cl.Message(content="Save cancelled or no path provided.").send()
        return
    path = (res["output"] or "").strip()
    if not path:
        await cl.Message(content="Save cancelled: path was empty.").send()
        return
    path = os.path.abspath(path)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            flows = await _get_flows(client)
        _write_flow_file(flows, path)
        await cl.Message(content=f"Flow saved to `{path}`.").send()
    except httpx.ConnectError:
        await cl.Message(
            content=f"Cannot reach Node-RED at `{NODE_RED_URL}`. Is it running?"
        ).send()
    except httpx.HTTPStatusError as e:
        await cl.Message(
            content=f"Node-RED API error: {e.response.status_code}. Enable Admin API or check auth."
        ).send()
    except Exception as e:
        await cl.Message(content=f"Save failed: {e!s}").send()


@cl.action_callback("load_flow_open")
async def on_load_flow_open(action: cl.Action):
    """Load default saved flow from NODE_RED_FLOW_PATH into Node-RED, then send link."""
    if not _flow_file_exists():
        await cl.Message(
            content=f"No saved flow at `{NODE_RED_FLOW_PATH}`. Save a flow from Node-RED first, or set `NODE_RED_FLOW_PATH`."
        ).send()
        return
    try:
        flows = _read_flows_from_path(NODE_RED_FLOW_PATH)
        await _load_flows_into_nodered_then_send(flows, f"`{NODE_RED_FLOW_PATH}`")
    except httpx.ConnectError:
        await cl.Message(
            content=f"Cannot reach Node-RED at `{NODE_RED_URL}`. Is it running?"
        ).send()
    except httpx.HTTPStatusError as e:
        await cl.Message(
            content=f"Node-RED API error: {e.response.status_code}. Enable Admin API or check auth."
        ).send()
    except Exception as e:
        await cl.Message(content=f"Load failed: {e!s}").send()


@cl.action_callback("browse_saved_flows")
async def on_browse_saved_flows(action: cl.Action):
    """Ask for directory path, list flow JSON files, show clickable list to load and open."""
    res = await cl.AskUserMessage(
        content="Enter the **absolute path** of the directory where your flow JSON files are saved:",
        timeout=120,
        raise_on_timeout=False,
    ).send()
    if not res or not res.get("output"):
        await cl.Message(content="Cancelled or no path provided.").send()
        return
    dir_path = os.path.abspath((res["output"] or "").strip())
    if not os.path.isdir(dir_path):
        await cl.Message(content=f"Not a directory or not found: `{dir_path}`").send()
        return
    try:
        all_files = os.listdir(dir_path)
        json_files = sorted([f for f in all_files if f.lower().endswith(FLOW_EXT)])
    except OSError as e:
        await cl.Message(content=f"Cannot list directory: {e!s}").send()
        return
    if not json_files:
        await cl.Message(content=f"No `.json` files found in `{dir_path}`").send()
        return
    # One action per file: click to load that file into Node-RED and open editor
    file_actions = [
        cl.Action(
            name="load_flow_from_path",
            label=f"Load: {f}",
            payload={"path": os.path.join(dir_path, f)},
            tooltip=f"Load {f} into Node-RED and open editor",
        )
        for f in json_files
    ]
    await cl.Message(
        content=f"**Flows in `{dir_path}`** — click a flow to load it into Node-RED and open the editor (then you can work on it and update it):",
        actions=file_actions,
    ).send()


@cl.action_callback("load_flow_from_path")
async def on_load_flow_from_path(action: cl.Action):
    """Load flow from path (payload) into Node-RED and send open link."""
    path = (action.payload or {}).get("path") if isinstance(action.payload, dict) else None
    if not path or not os.path.isfile(path):
        await cl.Message(content="Invalid or missing file path.").send()
        return
    try:
        flows = _read_flows_from_path(path)
        if not flows:
            await cl.Message(content=f"File is empty or not a valid flow JSON: `{path}`").send()
            return
        await _load_flows_into_nodered_then_send(flows, f"`{path}`")
    except httpx.ConnectError:
        await cl.Message(
            content=f"Cannot reach Node-RED at `{NODE_RED_URL}`. Is it running?"
        ).send()
    except httpx.HTTPStatusError as e:
        await cl.Message(
            content=f"Node-RED API error: {e.response.status_code}. Enable Admin API or check auth."
        ).send()
    except Exception as e:
        await cl.Message(content=f"Load failed: {e!s}").send()


@cl.action_callback("load_flow_upload")
async def on_load_flow_upload(action: cl.Action):
    """Ask user to upload a flow JSON file, then load into Node-RED and send open link."""
    files = await cl.AskFileMessage(
        content="Upload a **flow JSON file** to load into Node-RED (then you can open the editor and work on it):",
        accept={"application/json": [FLOW_EXT], "text/plain": [FLOW_EXT]},
        max_files=1,
        timeout=120,
        raise_on_timeout=False,
    ).send()
    if not files:
        await cl.Message(content="Upload cancelled or no file received.").send()
        return
    f = files[0]
    path = getattr(f, "path", None)
    if not path or not os.path.isfile(path):
        await cl.Message(content="Could not read uploaded file.").send()
        return
    try:
        flows = _read_flows_from_path(path)
        if not flows:
            await cl.Message(content="File is empty or not a valid flow JSON.").send()
            return
        await _load_flows_into_nodered_then_send(
            flows, f"uploaded file `{getattr(f, 'name', 'file')}`"
        )
    except httpx.ConnectError:
        await cl.Message(
            content=f"Cannot reach Node-RED at `{NODE_RED_URL}`. Is it running?"
        ).send()
    except httpx.HTTPStatusError as e:
        await cl.Message(
            content=f"Node-RED API error: {e.response.status_code}. Enable Admin API or check auth."
        ).send()
    except Exception as e:
        await cl.Message(content=f"Load failed: {e!s}").send()


@cl.on_stop
def on_stop() -> None:
    """Handle chat stop."""
    flush_tracing()
    logger.info("Chat session stopped")


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
