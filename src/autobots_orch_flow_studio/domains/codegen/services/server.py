# ABOUTME: Concierge-specific Chainlit entry point for the concierge_chat use case.
# ABOUTME: Wires tracing, OAuth, and the shared streaming helper.

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chainlit as cl
from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    flush_tracing,
    get_logger,
    init_tracing,
    set_session_id,
)
from autobots_devtools_shared_lib.dynagent import create_base_agent
from autobots_devtools_shared_lib.dynagent.ui import stream_agent_events
from dotenv import load_dotenv

from autobots_agents_jarvis.common.utils.formatting import format_structured_output
from autobots_agents_jarvis.domains.concierge.settings import init_concierge_settings
from autobots_agents_jarvis.domains.concierge.tools import register_concierge_tools
# Removed direct imports from agent_builder - agent_builder agent handles everything via its tools

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__file__)

# Application name for tracing and identification
APP_NAME = "concierge_chat"

# Removed unused constants - agent_builder handles everything deterministically

# Register Concierge settings so shared-lib (dynagent) uses the same instance.
init_concierge_settings()

# Initialise write-through context store (Postgres + Redis).

# Registration must precede AgentMeta.instance() (called inside create_base_agent).
register_concierge_tools()


# Register action callback for creating agents (must be at module level)
@cl.action_callback("create_agent")
async def on_create_agent_action(action: cl.Action):
    """Handle the create agent action button click."""
    await collect_agent_info_step_by_step()


# Removed action callbacks for tool selection - agent_builder handles everything deterministically via conversation


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
    set_session_id(cl.context.session.thread_id)
    cl.user_session.set("trace_metadata", trace_metadata)

    # Create action button for agent builder
    # Note: Action callback must be defined before the action is used
    create_agent_action = cl.Action(
        name="create_agent",
        payload={"action": "create_agent"},
        label="🚀 Create New Agent",
        tooltip="Click to start creating a new agent configuration",
    )
    
    # Send welcome message with action button
    # Note: If the button doesn't appear, users can type "create agent" instead
    welcome_msg = cl.Message(
        content="""Hello! I'm Concierge. How can I help you today?

**🚀 Create a New Agent:**
You can create a new agent by:
- **Clicking the "🚀 Create New Agent" button below** (if visible)
- **Typing:** `create agent`, `new agent`, `build agent`, or `agent builder`

I'll guide you through a simple step-by-step process to create your agent configuration.""",
    )
    welcome_msg.actions = [create_agent_action]
    await welcome_msg.send()


def get_available_tools() -> list[str]:
    """Get list of available tools by parsing tools.py file.
    
    Returns:
        List of tool names found in tools.py
    """
    tools_file = Path(__file__).parent / "tools.py"
    
    if not tools_file.exists():
        logger.warning("tools.py not found, returning default tools")
        return ["handoff", "get_agent_list"]
    
    try:
        content = tools_file.read_text(encoding="utf-8")
        # Find all @tool decorated functions
        pattern = r"@tool\s+def\s+(\w+)\s*\("
        matches = re.findall(pattern, content)
        
        # Filter out agent-builder specific tools (they're not for agents to use)
        agent_builder_tools = {
            "validate_agent_name_tool",
            "validate_domain_name_tool",
            "validate_agent_config_tool",
            "get_prompt_number_tool",
            "create_agent_prompt_content_tool",
            "create_agent_yaml_entry_tool",
            "ensure_domain_structure_tool",
            "create_agent_config_tool",
            "create_agent",
        }
        
        # Filter out agent builder tools
        available_tools = [tool for tool in matches if tool not in agent_builder_tools]
        
        # Add standard tools that might not be in tools.py but are always available
        standard_tools = ["handoff", "get_agent_list", "get_context_tool", "set_context_tool",
                          "update_context_tool", "clear_context_tool", "read_file_tool",
                          "write_file_tool", "list_files_tool", "output_format_converter_tool"]
        
        # Combine and deduplicate, then sort
        all_tools = set(available_tools) | set(standard_tools)
        return sorted(all_tools)
        
    except Exception as e:
        logger.exception(f"Error reading tools.py: {e}")
        # Return default tools on error
        return ["handoff", "get_agent_list"]


# Removed show_tool_selection_ui - agent_builder handles tool selection deterministically via conversation


async def collect_agent_info_step_by_step():
    """Start agent creation flow using the agent_builder agent."""
    # Mark that we're in agent creation mode
    cl.user_session.set("agent_creation_mode", True)
    
    # Invoke the agent_builder agent to start the conversation
    config: RunnableConfig = {
        "configurable": {
            "thread_id": cl.context.session.thread_id,
            "agent_name": "agent_builder",  # Use agent_builder agent
        },
        "recursion_limit": 50,
        "run_name": "agent_builder_chat",
    }
    
    base_agent = cl.user_session.get("base_agent")
    if not base_agent:
        await cl.Message(content="Error: Session initialization failed. Please refresh.").send()
        return
    
    user_id = cl.user_session.get("user_id")
    trace_metadata = cl.user_session.get("trace_metadata")
    
    # Initial message to start agent creation
    input_state: dict[str, Any] = {
        "messages": [{"role": "user", "content": "I want to create a new agent. Please help me through the process."}],
        "user_id": user_id,
        "app_name": "agent_builder_chat",
        "session_id": cl.context.session.thread_id,
        "agent_name": "agent_builder",
    }
    
    await stream_agent_events(
        agent=base_agent,
        input_state=input_state,
        config=config,
        on_structured_output=format_structured_output,
        enable_tracing=True,
        trace_metadata=trace_metadata,
    )


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages from the user."""
    set_session_id(cl.context.session.thread_id)
    
    # Check if user wants to create an agent
    if message.content.lower().strip() in ["create agent", "new agent", "build agent", "agent builder"]:
        await collect_agent_info_step_by_step()
        return
    
    # Check if user is in agent creation flow
    agent_creation_mode = cl.user_session.get("agent_creation_mode", False)
    
    # Determine which agent to use
    if agent_creation_mode:
        agent_name = "agent_builder"
        run_name = "agent_builder_chat"
    else:
        agent_name = None  # Use default agent
        run_name = APP_NAME

    config: RunnableConfig = {
        "configurable": {
            "thread_id": cl.context.session.thread_id,
        },
        "recursion_limit": 50,
        "run_name": run_name,
    }
    
    # Set agent_name in config if we're using agent_builder
    if agent_name:
        config["configurable"]["agent_name"] = agent_name

    # Reuse the same agent instance from session
    base_agent = cl.user_session.get("base_agent")
    if not base_agent:
        await cl.Message(content="Error: Session initialization failed. Please refresh.").send()
        return

    user_id = cl.user_session.get("user_id")

    input_state: dict[str, Any] = {
        "messages": [{"role": "user", "content": message.content}],
        "user_id": user_id,
        "app_name": run_name,
        "session_id": cl.context.session.thread_id,
    }
    
    # Set agent_name in input_state if using agent_builder
    if agent_name:
        input_state["agent_name"] = agent_name

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
    
    # Check if agent_builder has completed agent creation (by checking if it called create_agent_config_tool)
    # This is a simple heuristic - in practice, the agent_builder should signal completion
    # For now, we'll let the agent manage its own state via context tools


# Removed handle_agent_form_step - now handled by agent_builder agent deterministically


# Removed create_agent_from_form - agent creation is now handled deterministically by agent_builder agent
# The agent_builder uses create_agent_config_tool to create agents


@cl.on_stop
def on_stop() -> None:
    """Handle chat stop."""
    flush_tracing()
    logger.info("Chat session stopped")


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
