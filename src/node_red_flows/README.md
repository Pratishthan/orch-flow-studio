# Node-RED flow for Chainlit `/chat` endpoint

This folder contains a minimal Node-RED flow that implements the `/chat` endpoint expected by Chainlit.

## Start Node-RED with this flow

From the `orch-flow-studio` project root:

```bash
make node-red
```

This starts Node-RED with `flows_chat.json` pre-loaded (port 1880). Open the editor at http://localhost:1880.

## Manual import (alternative)

1. Start Node-RED and open the editor (http://localhost:1880).
2. Open the **menu** (three lines, top right) → **Import**.
3. Click **select a file to import** and choose `flows_chat.json`, or paste the contents of `flows_chat.json` into the clipboard and use **Import** → **Clipboard**.
4. Click **Import**, then **Deploy**.

The flow will:

- Listen for **POST** requests at **/chat**.
- Read the JSON body (e.g. `{ "message": "user text" }`).
- Respond with JSON `{ "reply": "You said: ..." }`.

You can edit the **Build reply** function node to change the behavior (e.g. call external APIs or add logic).

## Contract

- **Request:** POST, body `{ "message": "<user message>", "session_id": "<optional>" }`.
- **Response:** JSON `{ "reply": "<text>" }` or `{ "error": "<text>" }`.
