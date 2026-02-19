#!/usr/bin/env bash
# ABOUTME: Run Orch Flow Studio Chainlit UI in development mode

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Set default config directory if not already set
export DYNAGENT_CONFIG_ROOT_DIR="${DYNAGENT_CONFIG_ROOT_DIR:-agent_configs/orch_flow_studio}"

# Default port
PORT="${PORT:-2337}"

echo "Starting Orch Flow Studio on http://localhost:$PORT"
echo "Config directory: $DYNAGENT_CONFIG_ROOT_DIR"

# Run Chainlit
chainlit run src/autobots_orch_flow_studio/domains/orch_flow_studio/server.py --port "$PORT" --host 127.0.0.1
