# ABOUTME: Concierge domain services — mock implementations for jokes and weather.
# ABOUTME: Combines joke_service and weather_service for the Concierge domain.

import random
from typing import Any

# ==================== JOKE SERVICE ====================

# Mock joke database
JOKES: dict[str, list[dict[str, Any]]] = {
    "programming": [
        {
            "joke_text": "Why do programmers prefer dark mode? Because light attracts bugs!",
            "category": "programming",
            "rating": 4,
        },
        {
            "joke_text": "How many programmers does it take to change a light bulb? None, it's a hardware problem!",
            "category": "programming",
            "rating": 3,
        },
        {
            "joke_text": "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
            "category": "programming",
            "rating": 5,
        },
        {
            "joke_text": "There are 10 types of people in the world: those who understand binary and those who don't.",
            "category": "programming",
            "rating": 4,
        },
        {
            "joke_text": "Why do Python programmers wear glasses? Because they can't C!",
            "category": "programming",
            "rating": 3,
        },
    ],
    "general": [
        {
            "joke_text": "Why don't scientists trust atoms? Because they make up everything!",
            "category": "general",
            "rating": 4,
        },
        {
            "joke_text": "What do you call a fake noodle? An impasta!",
            "category": "general",
            "rating": 3,
        },
        {
            "joke_text": "Why did the scarecrow win an award? He was outstanding in his field!",
            "category": "general",
            "rating": 3,
        },
    ],
    "knock-knock": [
        {
            "joke_text": "Knock knock. Who's there? Interrupting cow. Interrupting cow w— MOOOOO!",
            "category": "knock-knock",
            "rating": 2,
        },
        {
            "joke_text": "Knock knock. Who's there? Tank. Tank who? You're welcome!",
            "category": "knock-knock",
            "rating": 3,
        },
    ],
    "dad-joke": [
        {
            "joke_text": "I'm afraid for the calendar. Its days are numbered.",
            "category": "dad-joke",
            "rating": 4,
        },
        {
            "joke_text": "What do you call a bear with no teeth? A gummy bear!",
            "category": "dad-joke",
            "rating": 3,
        },
        {
            "joke_text": "Why don't eggs tell jokes? They'd crack each other up!",
            "category": "dad-joke",
            "rating": 3,
        },
        {
            "joke_text": "I used to hate facial hair, but then it grew on me.",
            "category": "dad-joke",
            "rating": 4,
        },
    ],
}


def get_joke(category: str) -> dict[str, Any]:
    """Get a random joke from the specified category.

    Args:
        category: The joke category (programming, general, knock-knock, dad-joke)

    Returns:
        A dictionary containing joke_text, category, and rating
    """
    if category not in JOKES:
        return {
            "error": f"Invalid category '{category}'. Use get_joke_categories to see available categories."
        }

    return random.choice(JOKES[category])  # noqa: S311 - random is fine for joke selection


def list_categories() -> list[str]:
    """Get the list of available joke categories.

    Returns:
        List of available category names
    """
    return list(JOKES.keys())


# ==================== WEATHER SERVICE ====================

# Mock weather database with synthetic data
WEATHER_DATA: dict[str, dict[str, Any]] = {
    "san francisco": {
        "location": "San Francisco",
        "temperature": {"value": 62, "unit": "fahrenheit"},
        "conditions": "Foggy",
    },
    "new york": {
        "location": "New York",
        "temperature": {"value": 55, "unit": "fahrenheit"},
        "conditions": "Partly Cloudy",
    },
    "london": {
        "location": "London",
        "temperature": {"value": 12, "unit": "celsius"},
        "conditions": "Rainy",
    },
    "tokyo": {
        "location": "Tokyo",
        "temperature": {"value": 18, "unit": "celsius"},
        "conditions": "Clear",
    },
    "seattle": {
        "location": "Seattle",
        "temperature": {"value": 50, "unit": "fahrenheit"},
        "conditions": "Rainy",
    },
    "miami": {
        "location": "Miami",
        "temperature": {"value": 82, "unit": "fahrenheit"},
        "conditions": "Sunny",
    },
}

# Forecast templates for different conditions
FORECAST_TEMPLATES: dict[str, list[str]] = {
    "Foggy": [
        "Foggy morning clearing to partly cloudy",
        "Continued fog with light winds",
        "Fog dissipating by midday",
    ],
    "Partly Cloudy": [
        "Mostly sunny",
        "Increasing clouds",
        "Cloudy with chance of rain",
    ],
    "Rainy": [
        "Light rain continuing",
        "Heavy rain expected",
        "Rain tapering off",
        "Scattered showers",
    ],
    "Clear": [
        "Clear skies continuing",
        "Partly cloudy",
        "Mostly sunny",
        "Clear and pleasant",
    ],
    "Sunny": ["Sunny and warm", "Hot and sunny", "Clear skies", "Bright sunshine"],
}


def get_weather(location: str) -> dict[str, Any]:
    """Get current weather information for a location.

    Args:
        location: The location to get weather for (e.g., "San Francisco", "New York")

    Returns:
        A dictionary containing location, temperature, and conditions
    """
    location_key = location.lower()

    if location_key not in WEATHER_DATA:
        return {
            "error": f"Weather data not available for '{location}'. Try: San Francisco, New York, London, Tokyo, Seattle, or Miami."
        }

    return WEATHER_DATA[location_key].copy()


def get_forecast(location: str, days: int = 3) -> dict[str, Any]:
    """Get weather forecast for a location.

    Args:
        location: The location to get forecast for
        days: Number of days to forecast (default: 3, max: 7)

    Returns:
        A dictionary containing location and forecast array
    """
    location_key = location.lower()

    if location_key not in WEATHER_DATA:
        return {
            "error": f"Weather data not available for '{location}'. Try: San Francisco, New York, London, Tokyo, Seattle, or Miami."
        }

    # Limit days to reasonable range
    days = min(max(days, 1), 7)

    # Get current conditions and generate forecast based on it
    current = WEATHER_DATA[location_key]
    conditions = current["conditions"]
    forecast_options = FORECAST_TEMPLATES.get(conditions, ["Conditions vary"])

    # Generate forecast days - using list comprehension for performance
    forecast_list = [
        random.choice(forecast_options)  # noqa: S311
        for _ in range(days)
    ]

    return {
        "location": current["location"],
        "forecast": forecast_list,
    }


# ==================== TEST MAIN ====================

if __name__ == "__main__":
    """Test the agent builder functionality.

    Run this script to test agent creation:
        python -m autobots_agents_jarvis.domains.concierge.services

    Or from the project root:
        python src/autobots_agents_jarvis/domains/concierge/services.py
    """
    import sys
    import os
    from pathlib import Path

    # Add the src directory to Python path if running directly
    current_file = Path(__file__).resolve()
    # Go up 4 levels: concierge -> domains -> autobots_agents_jarvis -> src
    src_dir = current_file.parent.parent.parent.parent
    
    # Verify the path exists and contains the package
    if not src_dir.exists():
        print(f"ERROR: src directory not found at {src_dir}")
        sys.exit(1)
    
    # Check if autobots_agents_jarvis package exists
    package_dir = src_dir / "autobots_agents_jarvis"
    if not package_dir.exists():
        print(f"ERROR: Package directory not found at {package_dir}")
        sys.exit(1)
    
    # Add to path if not already there
    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)

    print("=" * 80)
    print("Testing Agent Builder Services")
    print("=" * 80)
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    print(f"Looking for package in: {package_dir}")
    print()

    # Import agent builder functions for testing
    try:
        from autobots_agents_jarvis.domains.concierge.agent_builder import (
            add_agent_to_yaml,
            create_agent_prompt_content,
            create_agent_yaml_entry,
            create_output_schema,
            ensure_domain_structure,
            get_domain_path,
            get_prompt_number,
            validate_agent_config,
            validate_agent_name,
            validate_domain_name,
            write_prompt_file,
        )
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Check if it's a pydantic/Python 3.14 compatibility issue
        if "pydantic" in error_msg.lower() or "ConfigError" in error_type:
            print("=" * 80)
            print("ERROR: Python 3.14 Compatibility Issue")
            print("=" * 80)
            print()
            print("The langfuse library (used for tracing) has compatibility issues")
            print("with Python 3.14 due to pydantic v1 dependencies.")
            print()
            print("Solutions:")
            print("1. Use Python 3.11 or 3.12 instead:")
            print("   python3.11 src/autobots_agents_jarvis/domains/concierge/services.py")
            print("   python3.12 src/autobots_agents_jarvis/domains/concierge/services.py")
            print()
            print("2. Or run as a module (which may handle dependencies better):")
            print("   python3 -m autobots_agents_jarvis.domains.concierge.services")
            print()
            print(f"Error details: {error_type}: {error_msg}")
            print()
            sys.exit(1)
        else:
            print(f"ERROR: Failed to import agent_builder: {error_type}: {error_msg}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Python path entries: {sys.path[:5]}...")  # Show first 5 entries
            sys.exit(1)

    # Test 1: Validate names
    print("1. Testing Name Validation")
    print("-" * 80)
    test_cases = [
        ("test_agent", True),
        ("test-agent", True),
        ("test123", True),
        ("TestAgent", False),  # uppercase
        ("123agent", False),  # starts with number
        ("test agent", False),  # space
        ("", False),  # empty
    ]

    for name, should_pass in test_cases:
        is_valid, error = validate_agent_name(name)
        status = "PASS" if (is_valid == should_pass) else "FAIL"
        print(f"{status} '{name}': valid={is_valid}, expected={should_pass}")
        if not is_valid and should_pass:
            print(f"   Error: {error}")

    print()

    # Test 2: Validate domain names
    print("2. Testing Domain Name Validation")
    print("-" * 80)
    domain_cases = [
        ("test-domain", True),
        ("test_domain", True),
        ("TestDomain", False),
        ("", False),
    ]

    for domain, should_pass in domain_cases:
        is_valid, error = validate_domain_name(domain)
        status = "PASS" if (is_valid == should_pass) else "FAIL"
        print(f"{status} '{domain}': valid={is_valid}, expected={should_pass}")

    print()

    # Test 3: Get prompt number
    print("3. Testing Prompt Number Generation")
    print("-" * 80)
    test_domain = "test-domain"
    prompt_num = get_prompt_number(test_domain)
    print(f"Next prompt number for '{test_domain}': {prompt_num:02d}")
    print()

    # Test 4: Create prompt content
    print("4. Testing Prompt Content Generation")
    print("-" * 80)
    prompt_content = create_agent_prompt_content(
        agent_name="test_agent",
        purpose="a helpful test agent that demonstrates functionality",
        instructions="Always be friendly and provide clear responses.",
    )
    print("Generated prompt content:")
    print("-" * 40)
    print(prompt_content)
    print("-" * 40)
    print()

    # Test 5: Create YAML entry
    print("5. Testing YAML Entry Generation")
    print("-" * 80)
    yaml_entry = create_agent_yaml_entry(
        agent_name="test_agent",
        prompt_number=0,
        tools=["test_tool", "handoff", "get_agent_list"],
        batch_enabled=False,
        is_default=False,
        output_schema="test-agent-output.json",
    )
    print("Generated YAML entry:")
    print("-" * 40)
    print(yaml_entry)
    print("-" * 40)
    print()

    # Test 6: Create output schema
    print("6. Testing Output Schema Generation")
    print("-" * 80)
    schema_fields = {
        "result": {
            "type": "string",
            "description": "The test result",
            "required": True,
        },
        "status": {
            "type": "string",
            "enum": ["success", "failure"],
            "description": "Status of the operation",
            "required": True,
        },
    }
    schema = create_output_schema("test_agent", schema_fields)
    print("Generated schema:")
    print("-" * 40)
    import json

    print(json.dumps(schema, indent=2))
    print("-" * 40)
    print()

    # Test 7: Ensure domain structure
    print("7. Testing Domain Structure Creation")
    print("-" * 80)
    test_domain = "test-domain"
    success, error = ensure_domain_structure(test_domain)
    if success:
        print(f"PASS: Domain structure created for '{test_domain}'")
        domain_path = get_domain_path(test_domain)
        print(f"   Path: {domain_path}")
        print(f"   Exists: {domain_path.exists()}")
        print(f"   Prompts dir exists: {(domain_path / 'prompts').exists()}")
        print(f"   Schemas dir exists: {(domain_path / 'schemas').exists()}")
        print(f"   agents.yaml exists: {(domain_path / 'agents.yaml').exists()}")
    else:
        print(f"FAIL: Failed to create domain structure: {error}")
    print()

    # Test 8: Full agent creation workflow
    print("8. Testing Complete Agent Creation Workflow")
    print("-" * 80)
    test_domain = "test-domain"
    # Use a unique agent name with timestamp to avoid conflicts
    import time
    test_agent_name = f"sample_agent_{int(time.time())}"

    # Generate prompt content for this specific agent
    test_prompt_content = create_agent_prompt_content(
        agent_name=test_agent_name,
        purpose="a sample agent created for testing purposes",
        instructions="This is a test agent. Always respond with test data.",
    )

    # Validate configuration first
    is_valid, error = validate_agent_config(
        domain=test_domain,
        agent_name=test_agent_name,
        prompt_content=test_prompt_content,
        tools=["sample_tool", "handoff", "get_agent_list"],
    )

    if not is_valid:
        print(f"FAIL: Validation failed: {error}")
        sys.exit(1)

    print(f"PASS: Configuration validated for '{test_agent_name}' in domain '{test_domain}'")

    # Get prompt number
    prompt_num = get_prompt_number(test_domain)
    print(f"PASS: Next prompt number: {prompt_num:02d}")

    # Create YAML entry
    yaml_entry = create_agent_yaml_entry(
        agent_name=test_agent_name,
        prompt_number=prompt_num,
        tools=["sample_tool", "handoff", "get_agent_list"],
        batch_enabled=False,
        is_default=False,
    )

    # Add to agents.yaml
    success, error = add_agent_to_yaml(test_domain, yaml_entry)
    if success:
        print("PASS: Added agent to agents.yaml")
    else:
        print(f"FAIL: Failed to add agent: {error}")
        sys.exit(1)

    # Write prompt file
    success, error = write_prompt_file(test_domain, prompt_num, test_agent_name, test_prompt_content)
    if success:
        prompt_filename = f"{prompt_num:02d}-{test_agent_name.replace('_', '-')}.md"
        print(f"PASS: Created prompt file: {prompt_filename}")
    else:
        print(f"FAIL: Failed to create prompt file: {error}")
        sys.exit(1)

    # Verify files were created
    domain_path = get_domain_path(test_domain)
    prompt_file = domain_path / "prompts" / f"{prompt_num:02d}-{test_agent_name.replace('_', '-')}.md"
    agents_yaml = domain_path / "agents.yaml"

    print()
    print("Created Files:")
    print(f"   - {agents_yaml}")
    print(f"   - {prompt_file}")
    print()

    # Test 9: Verify file contents
    print("9. Verifying Created Files")
    print("-" * 80)
    if agents_yaml.exists():
        content = agents_yaml.read_text()
        if test_agent_name in content:
            print(f"PASS: agents.yaml contains '{test_agent_name}'")
        else:
            print(f"FAIL: agents.yaml does not contain '{test_agent_name}'")
    else:
        print("FAIL: agents.yaml does not exist")

    if prompt_file.exists():
        content = prompt_file.read_text()
        # Check for "Sample Agent" (the display name) or "sample" in the content
        if "Sample Agent" in content or "sample" in content.lower():
            print("PASS: Prompt file contains agent name")
        else:
            print("FAIL: Prompt file does not contain agent name")
            print(f"   Content preview: {content[:100]}...")
    else:
        print("FAIL: Prompt file does not exist")

    print()
    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
    print()
    print(f"Test files created in: {domain_path}")
    print("   You can inspect the created files to verify the output.")
    print()
    print("To clean up test files, delete the test-domain directory:")
    print(f"   rm -rf {domain_path}")
    print()
