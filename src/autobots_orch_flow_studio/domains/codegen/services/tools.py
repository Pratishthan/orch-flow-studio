# ABOUTME: Concierge use-case tools — the tools that Concierge registers.
# ABOUTME: Provides joke and weather functionality for demonstration purposes.

from autobots_devtools_shared_lib.common.observability import get_logger, set_session_id
from autobots_devtools_shared_lib.dynagent import Dynagent
from langchain.tools import ToolRuntime, tool

from autobots_agents_jarvis.common.tools.validation_tools import validate_email
from autobots_agents_jarvis.domains.concierge.agent_builder import (
    add_agent_to_yaml,
    create_agent_prompt_content,
    create_agent_yaml_entry,
    create_output_schema,
    ensure_domain_structure,
    ensure_tools_exist,
    get_prompt_number,
    validate_agent_config,
    validate_agent_name,
    validate_domain_name,
    write_prompt_file,
    write_schema_file,
    write_services_file,
)
from autobots_agents_jarvis.domains.concierge.services import (
    get_forecast as weather_get_forecast,
    get_joke,
    list_categories,
)
from autobots_agents_jarvis.domains.concierge.services import get_weather as weather_get_weather

logger = get_logger(__name__)


# --- @tool wrappers ---


@tool
def tell_joke(runtime: ToolRuntime[None, Dynagent], category: str) -> str:
    """Tell a joke from the specified category.

    Args:
        category: The joke category (programming, general, knock-knock, dad-joke)

    Returns:
        A formatted joke string
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Telling joke for session {session_id}, category: {category}")

    joke_data = get_joke(category)
    if "error" in joke_data:
        return joke_data["error"]

    return f"{joke_data['joke_text']} (Category: {joke_data['category']}, Rating: {joke_data['rating']}/5)"


@tool
def get_joke_categories() -> str:
    """Get the list of available joke categories.

    Returns:
        A comma-separated list of available joke categories
    """
    categories = list_categories()
    return f"Available joke categories: {', '.join(categories)}"


@tool
def get_weather(runtime: ToolRuntime[None, Dynagent], location: str) -> str:
    """Get current weather information for a location.

    Args:
        location: The location to get weather for (e.g., "San Francisco", "New York")

    Returns:
        Formatted weather information
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Getting weather for session {session_id}, location: {location}")

    weather_data = weather_get_weather(location)
    if "error" in weather_data:
        return weather_data["error"]

    temp = weather_data["temperature"]
    return (
        f"Weather in {weather_data['location']}: "
        f"{weather_data['conditions']}, "
        f"{temp['value']}°{temp['unit'][0].upper()}"
    )


@tool
def get_forecast(runtime: ToolRuntime[None, Dynagent], location: str, days: int = 3) -> str:
    """Get weather forecast for a location.

    Args:
        location: The location to get forecast for (e.g., "San Francisco", "New York")
        days: Number of days to forecast (default: 3, max: 7)

    Returns:
        Formatted weather forecast
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Getting forecast for session {session_id}, location: {location}, days: {days}")

    forecast_data = weather_get_forecast(location, days)
    if "error" in forecast_data:
        return forecast_data["error"]

    forecast_items = "\n  ".join(
        f"Day {i + 1}: {item}" for i, item in enumerate(forecast_data["forecast"])
    )
    return f"Weather forecast for {forecast_data['location']}:\n  {forecast_items}"


# --- Agent Builder Tools ---


@tool
def validate_agent_name_tool(runtime: ToolRuntime[None, Dynagent], agent_name: str) -> str:
    """Validate an agent name format.

    Args:
        agent_name: The agent name to validate (e.g., "joke_agent", "weather_agent")

    Returns:
        Validation result message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Validating agent name for session {session_id}, name: {agent_name}")

    is_valid, error = validate_agent_name(agent_name)
    if is_valid:
        return f"Agent name '{agent_name}' is valid"
    return f"Validation failed: {error}"


@tool
def validate_domain_name_tool(runtime: ToolRuntime[None, Dynagent], domain_name: str) -> str:
    """Validate a domain name format.

    Args:
        domain_name: The domain name to validate (e.g., "concierge", "sales", "customer-support")

    Returns:
        Validation result message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Validating domain name for session {session_id}, domain: {domain_name}")

    is_valid, error = validate_domain_name(domain_name)
    if is_valid:
        return f"Domain name '{domain_name}' is valid"
    return f"Validation failed: {error}"


@tool
def validate_agent_config_tool(
    runtime: ToolRuntime[None, Dynagent],
    domain: str,
    agent_name: str,
    prompt_content: str,
    tools: list[str],
) -> str:
    """Validate a complete agent configuration before creation.

    Args:
        domain: The domain name (e.g., "concierge")
        agent_name: The agent name (e.g., "joke_agent")
        prompt_content: The prompt content for the agent
        tools: List of tool names the agent should have

    Returns:
        Validation result message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(
        f"Validating agent config for session {session_id}, domain: {domain}, agent: {agent_name}"
    )

    is_valid, error = validate_agent_config(domain, agent_name, prompt_content, tools)
    if is_valid:
        return f"Agent configuration for '{agent_name}' in domain '{domain}' is valid"
    return f"Validation failed: {error}"


@tool
def get_prompt_number_tool(runtime: ToolRuntime[None, Dynagent], domain: str) -> str:
    """Get the next available prompt number for a domain.

    Args:
        domain: The domain name (e.g., "concierge")

    Returns:
        The next prompt number as a string
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Getting prompt number for session {session_id}, domain: {domain}")

    prompt_num = get_prompt_number(domain)
    return f"Next prompt number for domain '{domain}': {prompt_num:02d}"


@tool
def create_agent_prompt_content_tool(
    runtime: ToolRuntime[None, Dynagent],
    agent_name: str,
    purpose: str,
    instructions: str | None = None,
) -> str:
    """Generate agent prompt content from requirements.

    Args:
        agent_name: Agent name (e.g., "joke_agent")
        purpose: Agent's main purpose/role description
        instructions: Optional additional instructions

    Returns:
        Generated prompt content
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Creating prompt content for session {session_id}, agent: {agent_name}")

    prompt_content = create_agent_prompt_content(agent_name, purpose, instructions)
    return prompt_content


@tool
def create_agent_yaml_entry_tool(
    runtime: ToolRuntime[None, Dynagent],
    agent_name: str,
    prompt_number: int,
    tools: list[str],
    batch_enabled: bool = False,
    is_default: bool = False,
    output_schema: str | None = None,
) -> str:
    """Create YAML entry for an agent configuration.

    Args:
        agent_name: Agent name (e.g., "joke_agent")
        prompt_number: Prompt file number (e.g., 3 for "03-agent-name")
        tools: List of tool names
        batch_enabled: Whether batch processing is enabled (default: False)
        is_default: Whether this is the default agent (default: False)
        output_schema: Optional output schema filename (default: None)

    Returns:
        YAML string for the agent entry
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Creating YAML entry for session {session_id}, agent: {agent_name}")

    yaml_entry = create_agent_yaml_entry(
        agent_name, prompt_number, tools, batch_enabled, is_default, output_schema
    )
    return yaml_entry


@tool
def ensure_domain_structure_tool(runtime: ToolRuntime[None, Dynagent], domain: str) -> str:
    """Ensure domain directory structure exists in new-repo.

    Args:
        domain: Domain name (e.g., "concierge")

    Returns:
        Success or error message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Ensuring domain structure for session {session_id}, domain: {domain}")

    success, error = ensure_domain_structure(domain)
    if success:
        return f"Domain structure for '{domain}' is ready in new-repo"
    return f"Failed to create domain structure: {error}"


@tool
def create_agent(
    runtime: ToolRuntime[None, Dynagent],
    domain: str,
    agent_name: str,
    purpose: str,
    tools: str,
    instructions: str | None = None,
    batch_enabled: bool = False,
    is_default: bool = False,
) -> str:
    """Create a new agent configuration in the new-repo directory.

    This tool allows you to create a complete agent configuration by providing:
    - Domain name (e.g., "concierge", "sales")
    - Agent name (e.g., "my_agent")
    - Purpose/description of what the agent does
    - Tools (comma-separated list, e.g., "tool1, tool2, handoff, get_agent_list")
    - Optional: Additional instructions for the agent
    - Optional: Batch enabled flag (default: False)
    - Optional: Is default agent flag (default: False)

    Args:
        domain: The domain name this agent belongs to (lowercase, letters, numbers, hyphens, underscores)
        agent_name: The name for the agent (lowercase, letters, numbers, hyphens, underscores)
        purpose: A clear description of the agent's main purpose and role
        tools: Comma-separated list of tool names the agent should have access to
        instructions: Optional additional instructions for the agent's behavior
        batch_enabled: Whether batch processing is enabled (default: False)
        is_default: Whether this is the default agent for the domain (default: False)

    Returns:
        Success message with details of created files, or error message if creation fails
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(
        f"Creating agent for session {session_id}, domain: {domain}, agent: {agent_name}"
    )

    try:
        # Parse tools from comma-separated string
        tools_list = [tool.strip() for tool in tools.split(",") if tool.strip()]

        # Validate domain name
        is_valid, error = validate_domain_name(domain)
        if not is_valid:
            return f"Validation failed: {error}"

        # Validate agent name
        is_valid, error = validate_agent_name(agent_name)
        if not is_valid:
            return f"Validation failed: {error}"

        # Generate prompt content
        prompt_content = create_agent_prompt_content(
            agent_name=agent_name,
            purpose=purpose,
            instructions=instructions,
        )

        # Validate complete configuration
        is_valid, error = validate_agent_config(domain, agent_name, prompt_content, tools_list)
        if not is_valid:
            return f"Validation failed: {error}"

        # Ensure domain structure exists
        success, error_msg = ensure_domain_structure(domain)
        if not success:
            return f"Failed to create domain structure: {error_msg}"

        # Get prompt number
        prompt_num = get_prompt_number(domain)

        # Create YAML entry
        yaml_entry = create_agent_yaml_entry(
            agent_name=agent_name,
            prompt_number=prompt_num,
            tools=tools_list,
            batch_enabled=batch_enabled,
            is_default=is_default,
            output_schema=None,  # Can be added later if needed
        )

        # Add to agents.yaml
        success, error_msg = add_agent_to_yaml(domain, yaml_entry)
        if not success:
            return f"Failed to add agent to agents.yaml: {error_msg}"

        # Write prompt file
        success, error_msg = write_prompt_file(domain, prompt_num, agent_name, prompt_content)
        if not success:
            return f"Failed to write prompt file: {error_msg}"

        # Write services file
        success, error_msg = write_services_file(domain, agent_name, batch_enabled)
        if not success:
            return f"Failed to write services file: {error_msg}"

        # Success!
        files_created = [
            f"new-repo/agent_configs/{domain}/agents.yaml (updated)",
            f"new-repo/agent_configs/{domain}/prompts/{prompt_num:02d}-{agent_name.replace('_', '-')}.md",
            f"new-repo/agent_configs/{domain}/{agent_name}.py",
        ]

        return (
            f"✅ Agent '{agent_name}' created successfully in domain '{domain}'!\n\n"
            f"**Details:**\n"
            f"- Prompt Number: {prompt_num:02d}\n"
            f"- Batch Enabled: {'Yes' if batch_enabled else 'No'}\n"
            f"- Is Default: {'Yes' if is_default else 'No'}\n"
            f"- Tools: {', '.join(tools_list)}\n\n"
            f"**Files Created:**\n" + "\n".join(f"- {f}" for f in files_created)
        )

    except Exception as e:
        logger.exception("Error creating agent")
        return f"❌ An error occurred while creating the agent: {str(e)}"


@tool
def create_agent_config_tool(
    runtime: ToolRuntime[None, Dynagent],
    domain: str,
    agent_name: str,
    prompt_content: str,
    tools: list[str],
    batch_enabled: bool = False,
    is_default: bool = False,
    output_schema_fields: dict | None = None,
) -> str:
    """Create a complete agent configuration in new-repo with all necessary files.

    This tool performs all steps: validation, domain structure setup, file creation.

    Args:
        domain: Domain name (e.g., "concierge")
        agent_name: Agent name (e.g., "joke_agent")
        prompt_content: Prompt content for the agent
        tools: List of tool names
        batch_enabled: Whether batch processing is enabled (default: False)
        is_default: Whether this is the default agent (default: False)
        output_schema_fields: Optional dictionary of schema field definitions (default: None)

    Returns:
        Success message with details of created files, or error message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(
        f"Creating agent config for session {session_id}, domain: {domain}, agent: {agent_name}"
    )

    # Step 1: Validate configuration
    is_valid, error = validate_agent_config(domain, agent_name, prompt_content, tools)
    if not is_valid:
        return f"Validation failed: {error}"

    # Step 2: Ensure domain structure
    success, error = ensure_domain_structure(domain)
    if not success:
        return f"Failed to create domain structure: {error}"

    # Step 3: Get prompt number
    prompt_number = get_prompt_number(domain)

    # Step 4: Create YAML entry
    output_schema_filename = None
    if output_schema_fields:
        schema = create_output_schema(agent_name, output_schema_fields)
        output_schema_filename = f"{agent_name.replace('_', '-')}-output.json"
        # Write schema file
        success, error = write_schema_file(domain, agent_name, schema)
        if not success:
            return f"Failed to write schema file: {error}"

    yaml_entry = create_agent_yaml_entry(
        agent_name, prompt_number, tools, batch_enabled, is_default, output_schema_filename
    )

    # Step 5: Add to agents.yaml
    success, error = add_agent_to_yaml(domain, yaml_entry)
    if not success:
        return f"Failed to add agent to agents.yaml: {error}"

    # Step 6: Write prompt file
    success, error = write_prompt_file(domain, prompt_number, agent_name, prompt_content)
    if not success:
        return f"Failed to write prompt file: {error}"

    # Step 7: Write services file
    success, error = write_services_file(domain, agent_name, batch_enabled)
    if not success:
        return f"Failed to write services file: {error}"

    files_created = [
        f"new-repo/agent_configs/{domain}/agents.yaml (updated)",
        f"new-repo/agent_configs/{domain}/prompts/{prompt_number:02d}-{agent_name.replace('_', '-')}.md",
        f"new-repo/agent_configs/{domain}/{agent_name}.py",
    ]
    if output_schema_filename:
        files_created.append(
            f"new-repo/agent_configs/{domain}/schemas/{output_schema_filename}"
        )

    return (
        f"Successfully created agent '{agent_name}' in domain '{domain}'.\n"
        f"Files created:\n" + "\n".join(f"  - {f}" for f in files_created)
    )


@tool
def write_services_file_tool(
    runtime: ToolRuntime[None, Dynagent],
    domain: str,
    agent_name: str,
    batch_enabled: bool = False,
) -> str:
    """Create a services file for an agent.

    This tool creates a Python services file that allows programmatic invocation
    of the agent. The file will be placed at:
    new-repo/src/autobots_agents_jarvis/domains/{domain}/{agent_name}.py

    Args:
        domain: Domain name (e.g., "concierge")
        agent_name: Agent name (e.g., "joke_agent")
        batch_enabled: Whether the agent is batch-enabled (default: False)

    Returns:
        Success or error message
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(
        f"Creating services file for session {session_id}, domain: {domain}, agent: {agent_name}"
    )

    success, error = write_services_file(domain, agent_name, batch_enabled)
    if success:
        return f"Successfully created services file: new-repo/src/autobots_agents_jarvis/domains/{domain}/{agent_name}.py"
    return f"Failed to create services file: {error}"


# --- Auto-generated tool: get_time ---

@tool
def get_time(runtime: ToolRuntime[None, Dynagent]) -> str:
    """Get Time tool.

    TODO: Implement the functionality for this tool.
    This tool was auto-generated when creating an agent that requires it.

    Returns:
        Result of the tool execution
    """
    session_id = runtime.state.get("session_id", "default")
    set_session_id(session_id)
    logger.info(f"Executing get_time for session {session_id}")

    # TODO: Implement tool logic here
    return "Tool 'get_time' executed successfully. Implementation needed."


# --- Registration entry-point (called once at app startup) ---


def register_concierge_tools() -> None:
    """Register all Concierge tools into the dynagent usecase pool.

    Includes joke and weather tools, shared validation tools (validate_email),
    and agent builder tools for creating new agent configurations.
    """
    from autobots_devtools_shared_lib.dynagent import register_usecase_tools

    register_usecase_tools(
        [
            tell_joke,
            get_joke_categories,
            get_weather,
            get_forecast,
            validate_email,
            # Agent builder tools
            validate_agent_name_tool,
            validate_domain_name_tool,
            validate_agent_config_tool,
            get_prompt_number_tool,
            create_agent_prompt_content_tool,
            create_agent_yaml_entry_tool,
            ensure_domain_structure_tool,
            create_agent_config_tool,
            create_agent,  # Simple runtime tool for creating agents
            write_services_file_tool,  # Tool for creating services files,
            get_time,  # Auto-generated tool
        ]
    )
