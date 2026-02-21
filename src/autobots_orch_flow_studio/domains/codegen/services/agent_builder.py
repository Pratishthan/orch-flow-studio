# ABOUTME: Agent builder services for creating new agent configurations.
# ABOUTME: Provides functions for validating, generating, and writing agent configuration files.

import json
import os
import re
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from autobots_devtools_shared_lib.common.observability import get_logger

logger = get_logger(__name__)

# Name validation regex: lowercase letters, numbers, hyphens, underscores
# Must start with a letter
_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

# Base path for new-repo (relative to workspace root)
# Resolve to absolute path to handle relative paths correctly
def _get_new_repo_base() -> Path:
    """Get the absolute path to new-repo directory.
    
    Looks for new-repo in the workspace root (parent of autobots-agents-jarvis).
    Path structure: agent_on_agent/autobots-agents-jarvis/src/.../agent_builder.py
    """
    # Get the current file's directory
    current_file = Path(__file__).resolve()
    # Go up 6 levels to workspace root: concierge -> domains -> autobots_agents_jarvis -> src -> autobots-agents-jarvis -> agent_on_agent
    workspace_root = current_file.parent.parent.parent.parent.parent.parent
    new_repo_path = workspace_root / "new-repo"
    return new_repo_path

NEW_REPO_BASE = _get_new_repo_base()
AGENT_CONFIGS_BASE = NEW_REPO_BASE / "agent_configs"
AGENTS_YAML_FILENAME = "agents.yaml"


def validate_agent_name(name: str) -> tuple[bool, str]:
    """Validate agent name format.

    Args:
        name: Agent name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Agent name cannot be empty"
    if not _NAME_RE.match(name):
        return (
            False,
            f"Agent name '{name}' must be lowercase, start with a letter, and contain only letters, numbers, hyphens, and underscores",
        )
    return True, ""


def validate_domain_name(domain: str) -> tuple[bool, str]:
    """Validate domain name format.

    Args:
        domain: Domain name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain:
        return False, "Domain name cannot be empty"
    if not _NAME_RE.match(domain):
        return (
            False,
            f"Domain name '{domain}' must be lowercase, start with a letter, and contain only letters, numbers, hyphens, and underscores",
        )
    return True, ""


def get_domain_path(domain: str) -> Path:
    """Get the full path to a domain directory in new-repo.

    Args:
        domain: Domain name

    Returns:
        Path to domain directory
    """
    return AGENT_CONFIGS_BASE / domain


def get_prompt_number(domain: str) -> int:
    """Get the next prompt number for a domain.

    Args:
        domain: Domain name

    Returns:
        Next available prompt number (e.g., 03, 04)
    """
    domain_path = get_domain_path(domain)
    prompts_dir = domain_path / "prompts"

    if not prompts_dir.exists():
        return 0

    existing_numbers = []
    for file in prompts_dir.glob("*.md"):
        # Extract number from filename like "00-welcome.md"
        match = re.match(r"^(\d+)-", file.name)
        if match:
            existing_numbers.append(int(match.group(1)))

    return max(existing_numbers, default=-1) + 1


def validate_agent_config(
    domain: str,
    agent_name: str,
    prompt_content: str,
    tools: list[str],
) -> tuple[bool, str]:
    """Validate agent configuration before creation.

    Args:
        domain: Domain name
        agent_name: Agent name
        prompt_content: Prompt content
        tools: List of tool names

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate domain name
    is_valid, error = validate_domain_name(domain)
    if not is_valid:
        return False, error

    # Validate agent name
    is_valid, error = validate_agent_name(agent_name)
    if not is_valid:
        return False, error

    # Check if agent already exists
    domain_path = get_domain_path(domain)
    agents_yaml = domain_path / AGENTS_YAML_FILENAME
    if agents_yaml.exists():
        content = agents_yaml.read_text()
        if f"{agent_name}:" in content or f'"{agent_name}"' in content:
            return False, f"Agent '{agent_name}' already exists in domain '{domain}'"

    # Validate prompt content
    if not prompt_content or not prompt_content.strip():
        return False, "Prompt content cannot be empty"

    # Validate tools
    if not tools:
        return False, "Agent must have at least one tool"

    # Check for required tools (handoff and get_agent_list are recommended)
    if "handoff" not in tools:
        logger.warning(f"Agent '{agent_name}' does not have 'handoff' tool - recommended for multi-agent systems")

    # Auto-generate missing tools
    created_tools, _ = ensure_tools_exist(tools)
    if created_tools:
        logger.info(f"Auto-generated {len(created_tools)} missing tools: {', '.join(created_tools)}")

    return True, ""


def _get_llm_client() -> ChatGoogleGenerativeAI | None:
    """Get LLM client configured from environment variables.
    
    Returns:
        ChatGoogleGenerativeAI instance if GOOGLE_API_KEY is set, None otherwise
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return None
    
    model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    
    try:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.7,  # Balanced creativity for prompt generation
        )
    except Exception as e:
        logger.warning(f"Failed to create LLM client: {e}")
        return None


def create_agent_prompt_content(
    agent_name: str,
    purpose: str,
    instructions: str | None = None,
) -> str:
    """Generate agent prompt content from user requirements using LLM.

    Args:
        agent_name: Agent name (e.g., "joke_agent")
        purpose: Agent's main purpose/role
        instructions: Optional additional instructions

    Returns:
        Formatted prompt content (LLM-generated if available, otherwise template-based)
    """
    # Convert agent_name to display name (e.g., "joke_agent" -> "Joke Agent")
    display_name = " ".join(word.capitalize() for word in agent_name.replace("_", "-").split("-"))

    # Try to use LLM for enhanced prompt generation
    llm_client = _get_llm_client()
    
    if llm_client:
        try:
            # Create LLM prompt for generating the agent prompt
            llm_prompt = f"""You are an expert at writing AI agent prompts. Generate a comprehensive, professional prompt for an AI agent with the following details:

Agent Name: {display_name}
Purpose: {purpose}
Custom Instructions: {instructions if instructions else "None provided"}

The prompt should be in markdown format and include:
1. A title (# {display_name})
2. A role description (You are **{display_name}**, {purpose})
3. Instructions section (if custom instructions provided)
4. Guidelines section with professional best practices for AI agents
5. Tool Instructions section explaining how to use tools, including the requirement to call `get_agent_list` MANDATORILY before calling `handoff`

Make it clear, actionable, and professional. The guidelines should emphasize being helpful, using tools effectively, and proper agent handoff procedures. Return only the markdown content, no additional explanation."""

            # Call LLM
            messages = [HumanMessage(content=llm_prompt)]
            response = llm_client.invoke(messages)
            
            # Extract content from response
            # LangChain AIMessage.content can be a string or list of content blocks
            if hasattr(response, 'content') and response.content:
                # Handle both string and list content types
                if isinstance(response.content, str):
                    generated_prompt = response.content.strip()
                elif isinstance(response.content, list):
                    # Join list of content blocks (usually strings or dicts)
                    content_parts = []
                    for part in response.content:
                        if isinstance(part, str):
                            content_parts.append(part)
                        elif isinstance(part, dict) and 'text' in part:
                            content_parts.append(part['text'])
                        else:
                            content_parts.append(str(part))
                    generated_prompt = '\n'.join(content_parts).strip()
                else:
                    generated_prompt = str(response.content).strip()
                
                # Ensure we have valid content
                if isinstance(generated_prompt, str) and len(generated_prompt) > 0:
                    logger.info(f"Successfully generated prompt for '{agent_name}' using LLM")
                    return generated_prompt
                else:
                    logger.warning(f"LLM returned empty or invalid response for '{agent_name}', falling back to template")
            else:
                logger.warning(f"LLM response missing content for '{agent_name}', falling back to template")
                
        except Exception as e:
            logger.warning(f"Failed to generate prompt using LLM for '{agent_name}': {e}. Falling back to template.")
    
    # Fallback to template-based generation
    prompt = f"# {display_name}\n\n"
    prompt += f"You are **{display_name}**, {purpose}.\n\n"

    if instructions:
        prompt += "## Instructions\n\n"
        prompt += f"{instructions}\n\n"

    prompt += "## Guidelines\n\n"
    prompt += "- Be helpful and professional\n"
    prompt += "- Use the available tools to accomplish your tasks\n"
    prompt += "- You can use handoff tool to route users to other agents if needed\n\n"

    prompt += "## Tool Instructions\n"
    prompt += "- Call `get_agent_list` to get list of agents MANDATORILY before calling `handoff`\n"

    return prompt


def create_agent_yaml_entry(
    agent_name: str,
    prompt_number: int,
    tools: list[str],
    batch_enabled: bool = False,
    is_default: bool = False,
    output_schema: str | None = None,
) -> str:
    """Create YAML entry for an agent.

    Args:
        agent_name: Agent name
        prompt_number: Prompt file number (e.g., 3 for "03-agent-name")
        tools: List of tool names
        batch_enabled: Whether batch processing is enabled
        is_default: Whether this is the default agent
        output_schema: Optional output schema filename

    Returns:
        YAML string for the agent entry
    """
    # Format prompt number as zero-padded string
    prompt_str = f"{prompt_number:02d}-{agent_name.replace('_', '-')}"

    yaml = f"  {agent_name}:\n"
    yaml += f"    prompt: \"{prompt_str}\"\n"

    if batch_enabled:
        yaml += "    batch_enabled: true\n"
    else:
        yaml += "    batch_enabled: false\n"

    if is_default:
        yaml += "    is_default: true\n"

    if output_schema:
        yaml += f"    output_schema: \"{output_schema}\"\n"

    yaml += "    tools:\n"
    for tool in tools:
        yaml += f"      - \"{tool}\"\n"

    return yaml


def create_output_schema(agent_name: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a JSON schema for agent output.

    Args:
        agent_name: Agent name
        fields: Optional dictionary of field definitions. Can be in two formats:
            - Simple: {"field_name": "string"} - will be converted to {"field_name": {"type": "string"}}
            - Full: {"field_name": {"type": "string", "required": True}} - used as-is

    Returns:
        JSON schema dictionary
    """
    schema_name = f"{agent_name.replace('_', '-')}-output.json"

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"jarvis/{schema_name}",
        "title": f"{agent_name.replace('_', ' ').title()} Output",
        "type": "object",
        "required": [],
        "properties": {},
    }

    if fields:
        # Normalize fields: convert simple format {"field": "string"} to full format
        normalized_fields = {}
        for field_name, field_def in fields.items():
            if isinstance(field_def, str):
                # Simple format: {"field": "string"} -> {"field": {"type": "string"}}
                normalized_fields[field_name] = {"type": field_def}
            elif isinstance(field_def, dict):
                # Full format: already a dict, use as-is
                normalized_fields[field_name] = field_def.copy()
            else:
                # Fallback: treat as string type
                normalized_fields[field_name] = {"type": "string"}
        
        # Extract required fields
        schema["required"] = [
            k for k, v in normalized_fields.items() 
            if isinstance(v, dict) and v.get("required", False)
        ]
        schema["properties"] = normalized_fields

    return schema


def ensure_domain_structure(domain: str) -> tuple[bool, str]:
    """Ensure domain directory structure exists in new-repo.

    Args:
        domain: Domain name

    Returns:
        Tuple of (success, error_message)
    """
    domain_path = get_domain_path(domain)

    try:
        # Create domain directory
        domain_path.mkdir(parents=True, exist_ok=True)

        # Create prompts directory
        (domain_path / "prompts").mkdir(exist_ok=True)

        # Create schemas directory
        (domain_path / "schemas").mkdir(exist_ok=True)

        # Create agents.yaml if it doesn't exist
        agents_yaml = domain_path / AGENTS_YAML_FILENAME
        if not agents_yaml.exists():
            agents_yaml.write_text(
                f"# ABOUTME: {domain.title()} agent configuration\n"
                f"# ABOUTME: Defines agents for the {domain} domain\n\n"
                "agents:\n"
            )

        return True, ""
    except Exception as e:
        return False, f"Failed to create domain structure: {str(e)}"


def add_agent_to_yaml(domain: str, yaml_entry: str) -> tuple[bool, str]:
    """Add agent entry to agents.yaml file.

    Args:
        domain: Domain name
        yaml_entry: YAML entry string for the agent

    Returns:
        Tuple of (success, error_message)
    """
    domain_path = get_domain_path(domain)
    agents_yaml = domain_path / AGENTS_YAML_FILENAME

    if not agents_yaml.exists():
        return False, f"{AGENTS_YAML_FILENAME} does not exist for domain '{domain}'"

    try:
        content = agents_yaml.read_text()
        # Check if agents: section exists
        if "agents:" not in content:
            content = f"# ABOUTME: Agent configuration\n\nagents:\n{content}"

        # Append the new agent entry
        content = content.rstrip() + "\n" + yaml_entry + "\n"
        agents_yaml.write_text(content)
        return True, ""
    except Exception as e:
        return False, f"Failed to add agent to {AGENTS_YAML_FILENAME}: {str(e)}"


def write_prompt_file(domain: str, prompt_number: int, agent_name: str, content: str) -> tuple[bool, str]:
    """Write prompt file to domain prompts directory.

    Args:
        domain: Domain name
        prompt_number: Prompt number
        agent_name: Agent name
        content: Prompt content

    Returns:
        Tuple of (success, error_message)
    """
    domain_path = get_domain_path(domain)
    prompts_dir = domain_path / "prompts"

    prompt_filename = f"{prompt_number:02d}-{agent_name.replace('_', '-')}.md"
    prompt_path = prompts_dir / prompt_filename

    try:
        prompts_dir.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(content, encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, f"Failed to write prompt file: {str(e)}"


def write_schema_file(domain: str, agent_name: str, schema: dict[str, Any]) -> tuple[bool, str]:
    """Write output schema file to domain schemas directory.

    Args:
        domain: Domain name
        agent_name: Agent name
        schema: JSON schema dictionary

    Returns:
        Tuple of (success, error_message)
    """
    domain_path = get_domain_path(domain)
    schemas_dir = domain_path / "schemas"

    schema_filename = f"{agent_name.replace('_', '-')}-output.json"
    schema_path = schemas_dir / schema_filename

    try:
        schemas_dir.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, f"Failed to write schema file: {str(e)}"


# ==================== SERVICES FILE GENERATION ====================

def create_services_file_content(
    domain: str,
    agent_name: str,
    batch_enabled: bool = False,
) -> str:
    """Generate services file content for an agent.

    Args:
        domain: Domain name
        agent_name: Agent name
        batch_enabled: Whether the agent is batch-enabled

    Returns:
        Generated services file content as a string
    """
    if batch_enabled:
        return _create_batch_services_file_content(domain, agent_name)
    else:
        return _create_standard_services_file_content(domain, agent_name)


def _create_batch_services_file_content(domain: str, agent_name: str) -> str:
    """Generate services file content for a batch-enabled agent.

    Args:
        domain: Domain name
        agent_name: Agent name

    Returns:
        Generated services file content
    """
    # Convert agent_name to function name (snake_case)
    func_name = agent_name
    
    content = f'''# ABOUTME: Service file for {agent_name} - batch-enabled agent
import uuid
from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    get_logger,
    init_tracing,
    set_session_id,
)
from autobots_devtools_shared_lib.dynagent import batch_invoker, BatchResult
from dotenv import load_dotenv

# Import domain tools registration (adjust based on domain)
# from autobots_agents_jarvis.domains.{domain}.tools import register_{domain}_tools

logger = get_logger(__name__)
load_dotenv()
init_tracing()

APP_NAME = "{domain}-{agent_name}-batch"

def {func_name}_batch(
    records: list[str],
    user_id: str = "default",
    session_id: str | None = None,
) -> BatchResult:
    """Run {agent_name} agent in batch mode.
    
    Args:
        records: List of input strings to process
        user_id: User ID for tracing
        session_id: Optional session ID (auto-generated if None)
    
    Returns:
        BatchResult with successes and failures
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    set_session_id(session_id)
    
    # Register domain tools if needed
    # register_{domain}_tools()
    
    trace_metadata = TraceMetadata.create(
        session_id=session_id,
        app_name=APP_NAME,
        user_id=user_id,
        tags=[APP_NAME, "{agent_name}", "batch"],
    )
    
    logger.info(f"Invoking batch agent '{agent_name}' with {{len(records)}} records")
    result = batch_invoker(
        "{agent_name}",
        records,
        trace_metadata=trace_metadata,
    )
    
    logger.info(
        f"Batch complete: successes={{len(result.successes)}} failures={{len(result.failures)}}"
    )
    return result
'''
    return content


def _create_standard_services_file_content(domain: str, agent_name: str) -> str:
    """Generate services file content for a standard (non-batch) agent.

    Args:
        domain: Domain name
        agent_name: Agent name

    Returns:
        Generated services file content
    """
    # Convert agent_name to function name (snake_case)
    func_name = agent_name
    
    content = f'''# ABOUTME: Service file for {agent_name} - standard agent invocation
import uuid
from typing import TYPE_CHECKING
from autobots_devtools_shared_lib.common.observability import (
    TraceMetadata,
    get_logger,
    init_tracing,
    set_session_id,
)
from autobots_devtools_shared_lib.dynagent import invoke_agent, ainvoke_agent
from dotenv import load_dotenv

# Import domain tools registration (adjust based on domain)
# from autobots_agents_jarvis.domains.{domain}.tools import register_{domain}_tools

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig

logger = get_logger(__name__)
load_dotenv()
init_tracing()

APP_NAME = "{domain}-{agent_name}"

def call_{func_name}_sync(
    user_message: str,
    session_id: str | None = None,
    enable_tracing: bool = True,
) -> dict:
    """Synchronously invoke {agent_name} agent.
    
    Args:
        user_message: Message to send to the agent
        session_id: Optional session ID (auto-generated if None)
        enable_tracing: Whether to enable tracing
    
    Returns:
        dict: Complete final state from agent execution
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    set_session_id(session_id)
    
    # Register domain tools if needed
    # register_{domain}_tools()
    
    config: RunnableConfig = {{
        "configurable": {{
            "thread_id": session_id,
            "agent_name": "{agent_name}",
            "app_name": APP_NAME,
        }},
    }}
    
    input_state: dict = {{
        "messages": [{{"role": "user", "content": user_message}}],
        "agent_name": "{agent_name}",
        "session_id": session_id,
    }}
    
    trace_metadata = TraceMetadata(
        session_id=session_id,
        app_name=APP_NAME,
        user_id=APP_NAME,
        tags=[APP_NAME, "{agent_name}", "sync"],
    )
    
    logger.info(f"Invoking agent '{agent_name}'")
    result = invoke_agent(
        agent_name="{agent_name}",
        input_state=input_state,
        config=config,
        trace_metadata=trace_metadata,
        enable_tracing=enable_tracing,
    )
    
    return result

async def call_{func_name}_async(
    user_message: str,
    session_id: str | None = None,
    enable_tracing: bool = True,
) -> dict:
    """Asynchronously invoke {agent_name} agent.
    
    Args:
        user_message: Message to send to the agent
        session_id: Optional session ID (auto-generated if None)
        enable_tracing: Whether to enable tracing
    
    Returns:
        dict: Complete final state from agent execution
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    set_session_id(session_id)
    
    # Register domain tools if needed
    # register_{domain}_tools()
    
    config: RunnableConfig = {{
        "configurable": {{
            "thread_id": session_id,
            "agent_name": "{agent_name}",
            "app_name": APP_NAME,
        }},
    }}
    
    input_state: dict = {{
        "messages": [{{"role": "user", "content": user_message}}],
        "agent_name": "{agent_name}",
        "session_id": session_id,
    }}
    
    trace_metadata = TraceMetadata(
        session_id=session_id,
        app_name=APP_NAME,
        user_id=APP_NAME,
        tags=[APP_NAME, "{agent_name}", "async"],
    )
    
    logger.info(f"Invoking agent '{agent_name}' (async)")
    result = await ainvoke_agent(
        agent_name="{agent_name}",
        input_state=input_state,
        config=config,
        trace_metadata=trace_metadata,
        enable_tracing=enable_tracing,
    )
    
    return result
'''
    return content


def write_services_file(
    domain: str,
    agent_name: str,
    batch_enabled: bool = False,
) -> tuple[bool, str]:
    """Write services file for an agent.

    Args:
        domain: Domain name
        agent_name: Agent name
        batch_enabled: Whether the agent is batch-enabled

    Returns:
        Tuple of (success, error_message)
    """
    domain_path = get_domain_path(domain)
    services_file = domain_path / f"{agent_name}.py"

    try:
        # Generate services file content
        content = create_services_file_content(domain, agent_name, batch_enabled)
        
        # Write the file
        services_file.write_text(content, encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, f"Failed to write services file: {str(e)}"


# ==================== TOOL AUTO-GENERATION ====================

def check_tool_exists(tool_name: str) -> bool:
    """Check if a tool function exists in tools.py.

    Args:
        tool_name: Name of the tool to check (e.g., "my_tool")

    Returns:
        True if tool exists, False otherwise
    """
    tools_file = Path(__file__).parent / "tools.py"
    if not tools_file.exists():
        return False
    
    content = tools_file.read_text(encoding="utf-8")
    # Check for function definition: @tool followed by def tool_name
    pattern = rf"@tool\s+def\s+{tool_name}\s*\("
    return bool(re.search(pattern, content))


def get_tools_file_path() -> Path:
    """Get the path to tools.py file.

    Returns:
        Path to tools.py
    """
    return Path(__file__).parent / "tools.py"


def generate_tool_code(tool_name: str) -> str:
    """Generate skeleton code for a new tool.

    Args:
        tool_name: Name of the tool (e.g., "my_tool")

    Returns:
        Generated tool code as a string
    """
    # Convert tool_name to function name (handle snake_case)
    func_name = tool_name
    
    # Generate a simple tool skeleton
    # Note: The imports (ToolRuntime, Dynagent, tool, set_session_id, logger) 
    # are already in tools.py, so we don't need to add them
    tool_code = f'''# --- Auto-generated tool: {tool_name} ---

@tool
def {func_name}(runtime: ToolRuntime[None, Dynagent]) -> str:
    """{tool_name.replace('_', ' ').title()} tool.

    TODO: Implement the functionality for this tool.
    This tool was auto-generated when creating an agent that requires it.

    Returns:
        Result of the tool execution
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Executing {func_name} for session {{session_id}}")

    # TODO: Implement tool logic here
    return f"Tool '{func_name}' executed successfully. Implementation needed."


'''
    return tool_code


def add_tool_to_file(tool_name: str, tool_code: str) -> tuple[bool, str]:
    """Add a new tool to tools.py file.

    Args:
        tool_name: Name of the tool
        tool_code: Generated tool code

    Returns:
        Tuple of (success, error_message)
    """
    tools_file = get_tools_file_path()
    
    if not tools_file.exists():
        return False, "tools.py file not found"
    
    try:
        content = tools_file.read_text(encoding="utf-8")
        
        # Find the registration function
        registration_pattern = r"def register_concierge_tools\(\) -> None:"
        match = re.search(registration_pattern, content)
        
        if not match:
            return False, "Could not find register_concierge_tools function"
        
        # Find where to insert the tool (before the registration function)
        insert_pos = match.start()
        
        # Insert the tool code before the registration section
        # Look for the last @tool before registration
        before_registration = content[:insert_pos]
        
        # Find the last @tool or last function before registration
        last_tool_match = list(re.finditer(r"@tool\s+def\s+\w+", before_registration))
        
        if last_tool_match:
            # Insert after the last tool
            last_tool_end = last_tool_match[-1].end()
            # Find the end of that function (next blank line or end of function)
            remaining = before_registration[last_tool_end:]
            # Find the next double newline (end of function)
            next_double_newline = remaining.find("\n\n")
            if next_double_newline != -1:
                insert_pos = last_tool_end + next_double_newline + 2
            else:
                insert_pos = last_tool_end
        else:
            # Insert before registration function
            insert_pos = match.start()
        
        # Insert the tool code
        new_content = content[:insert_pos] + tool_code + content[insert_pos:]
        
        # Now update the registration function to include the new tool
        # Find the register_usecase_tools call
        reg_pattern = r"register_usecase_tools\(\s*\["
        reg_match = re.search(reg_pattern, new_content)
        
        if reg_match:
            # Find the closing bracket of the list
            bracket_pos = reg_match.end()
            # Find the last item in the list before the closing bracket
            # Look for the last line with a tool name before the closing bracket
            list_start = bracket_pos
            list_end = new_content.find("]", bracket_pos)
            if list_end == -1:
                return False, "Could not find end of register_usecase_tools list"
            
            list_content = new_content[list_start:list_end]
            # Find the last tool in the list (last non-comment, non-empty line)
            lines = list_content.split("\n")
            last_tool_line_idx = None
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line and not line.startswith("#") and not line.startswith("]"):
                    # Extract tool name (remove trailing comma)
                    tool_match = re.search(r"(\w+),?\s*$", line)
                    if tool_match:
                        last_tool_line_idx = i
                        break
            
            if last_tool_line_idx is not None:
                # Insert after the last tool line
                line_start = new_content.rfind(lines[last_tool_line_idx], list_start, list_end)
                if line_start != -1:
                    line_end = line_start + len(lines[last_tool_line_idx])
                    # Add the new tool to the list
                    new_content = (
                        new_content[:line_end] +
                        f",\n            {tool_name},  # Auto-generated tool" +
                        new_content[line_end:]
                    )
                else:
                    # Fallback: add before closing bracket
                    new_content = (
                        new_content[:list_end] +
                        f",\n            {tool_name},  # Auto-generated tool" +
                        new_content[list_end:]
                    )
            else:
                # Empty list or no tools found, add as first item
                new_content = (
                    new_content[:bracket_pos] +
                    f"\n            {tool_name},  # Auto-generated tool" +
                    new_content[bracket_pos:]
                )
        else:
            return False, "Could not find register_usecase_tools call"
        
        tools_file.write_text(new_content, encoding="utf-8")
        return True, f"Tool '{tool_name}' added to tools.py"
        
    except Exception as e:
        logger.exception(f"Error adding tool {tool_name} to tools.py")
        return False, f"Failed to add tool to tools.py: {str(e)}"


def ensure_tools_exist(tools: list[str]) -> tuple[list[str], list[str]]:
    """Ensure all required tools exist, creating missing ones.

    Args:
        tools: List of tool names required

    Returns:
        Tuple of (created_tools, existing_tools)
    """
    created_tools = []
    existing_tools = []
    
    # Standard tools that are always available (from shared lib or common)
    standard_tools = {
        "handoff", "get_agent_list", "get_context_tool", "set_context_tool",
        "update_context_tool", "clear_context_tool", "read_file_tool",
        "write_file_tool", "list_files_tool", "output_format_converter_tool",
        "validate_email"
    }
    
    for tool_name in tools:
        # Skip standard tools
        if tool_name in standard_tools:
            existing_tools.append(tool_name)
            continue
        
        # Check if tool exists
        if check_tool_exists(tool_name):
            existing_tools.append(tool_name)
        else:
            # Generate and add the tool
            tool_code = generate_tool_code(tool_name)
            success, error_msg = add_tool_to_file(tool_name, tool_code)
            if success:
                created_tools.append(tool_name)
                logger.info(f"Auto-generated tool: {tool_name}")
            else:
                logger.warning(f"Failed to auto-generate tool '{tool_name}': {error_msg}")
                # Still add to existing to avoid blocking agent creation
                existing_tools.append(tool_name)
    
    return created_tools, existing_tools
