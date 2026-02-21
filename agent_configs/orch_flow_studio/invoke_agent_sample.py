def _trigger_behaviour_list_generator(
    initial_input: str,
    state: MerState,
):
    """Extract behaviour list and write to {workspace_base_path}/{AGENTIC_GENERATOR_META}/{FBP_BEHAVIOUR_META}/{jira_number}/{BEHAVIOUR_LIST_JSON}."""

    user_id: str = state.get("user_name", "")
    repo_name: str = state.get("repo_name", "")
    jira_number: str = state.get("jira_number", "")
    thread_id = str(uuid.uuid4())
    set_conversation_id(thread_id)
    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "agent_name": BEHAVIOUR_LIST_EXTRACTOR,
            "app_name": APP_NAME,
        },
    }

    user_content = _build_user_message(initial_input, user_id, repo_name, jira_number)

    input_state: dict = {
        "messages": [{"role": "user", "content": user_content}],
        "agent_name": BEHAVIOUR_LIST_EXTRACTOR,
        "session_id": thread_id,
        "user_name": user_id,
        "jira_number": jira_number,
        "repo_name": repo_name,
    }

    # Prepare trace metadata
    trace_metadata = TraceMetadata(
        session_id=thread_id,
        app_name=APP_NAME,
        user_id=user_id,
        tags=[BEHAVIOUR_LIST_EXTRACTOR],
    )

    # Invoke agent (agent will be created internally)
    logger.info(f"Invoking agent '{BEHAVIOUR_LIST_EXTRACTOR}'")
    result = invoke_agent(
        agent_name=BEHAVIOUR_LIST_EXTRACTOR,
        input_state=input_state,
        config=config,
        trace_metadata=trace_metadata,
    )
    messages = result.get("messages") or []
    logger.debug(f"Messages: {messages}")

    converted = output_format_converter(BEHAVIOUR_LIST_EXTRACTOR, messages)
    if converted.startswith("Error:"):
        raise ValueError(f"behaviour_list: {converted}")
    logger.info(f"Converted: {converted}")
    data = json.loads(converted)
    behaviour_list_struct = data.get("behaviours")
    if not isinstance(behaviour_list_struct, list):
        raise TypeError(
            f"behaviour_list: output_format_converter did not return {{behaviours: [...]}}; got {type(behaviour_list_struct).__name__}"
        )

    logger.info(f"Extracted behaviour list (structured): {behaviour_list_struct}")

    write_meta_json_file(
        state=input_state,
        meta_subdir=FBP_BEHAVIOUR_META,
        file_name=BEHAVIOUR_LIST_JSON,
        content=behaviour_list_struct,
        error_label="behaviour_list",
    )
