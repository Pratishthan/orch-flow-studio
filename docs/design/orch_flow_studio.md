# Plan: Rename "jarvis" domain to "orch_flow_studio"

## Context

The `autobots-orch-flow-studio` repo serves as a **template** for new multi-domain projects. Both the source root package (`autobots_orch_flow_studio`) and the primary demo domain (`domains/jarvis/`) use the word "jarvis", making scaffolding ambiguous — a single find-and-replace can't distinguish the two levels.

**Solution**: Rename the demo domain from "jarvis" to "orch_flow_studio". The source root stays `autobots_orch_flow_studio`. This gives the template two clearly distinct names, enabling clean two-pass scaffolding.

## Changes

### 1. Rename directories

| From | To |
|------|-----|
| `src/autobots_orch_flow_studio/domains/jarvis/` | `domains/orch_flow_studio/` |
| `agent_configs/jarvis/` | `agent_configs/orch_flow_studio/` |
| `tests/unit/domains/jarvis/` | `tests/unit/domains/orch_flow_studio/` |
| `tests/integration/domains/jarvis/` | `tests/integration/domains/orch_flow_studio/` |
| `tests/sanity/domains/jarvis/` | `tests/sanity/domains/orch_flow_studio/` |

### 2. Rename files

| From | To |
|------|-----|
| `sbin/run_jarvis.sh` | `sbin/run_orch_flow_studio.sh` |
| `domains/jarvis/jarvis_batch.py` | `domains/orch_flow_studio/orch_flow_studio_batch.py` |

### 3. Settings refactoring (two-level pattern)

**`configs/settings.py`** — rename to shared `AppSettings`:
- `JarvisSettings` → `AppSettings`
- `get_jarvis_settings()` → `get_app_settings()`
- `init_jarvis_settings(settings)` → `init_app_settings(settings: AppSettings | None = None)` — accepts optional subclass instance
- `app_name` default stays generic (scaffold will override)
- Docstring: `"""Pydantic settings for application configuration.\nExtends DynagentSettings with app-level settings."""`

**`domains/orch_flow_studio/settings.py`** — NEW file, domain-specific:
```python
class OrchFlowStudioSettings(AppSettings):
    default_city: str = Field(default="London", description="Default city for weather lookups")
    default_joke_category: str = Field(default="general", description="Default joke category")

def get_orch_flow_studio_settings() -> OrchFlowStudioSettings: ...
def init_orch_flow_studio_settings() -> OrchFlowStudioSettings:
    s = OrchFlowStudioSettings()
    init_app_settings(s)  # chains: orch_flow_studio → app → dynagent
    return s
```

**Other domains** (`customer_support/server.py`, `sales/server.py`):
- Change `init_jarvis_settings()` → `init_app_settings()` (direct call, no domain subclass)

### 4. Content replacements (domain-level only)

Applied in order (most-specific first). **`autobots_orch_flow_studio` / `autobots-orch-flow-studio` are NOT touched.**

| Old | New |
|-----|-----|
| `register_jarvis_tools` | `register_orch_flow_studio_tools` |
| `_get_jarvis_batch_agents` | `_get_orch_flow_studio_batch_agents` |
| `jarvis_registered` | `orch_flow_studio_registered` |
| `jarvis_tools_registered` | `orch_flow_studio_tools_registered` |
| `jarvis_batch` | `orch_flow_studio_batch` |
| `jarvis_chat` | `orch_flow_studio_chat` |
| `jarvis-chat` | `orch_flow_studio-chat` |
| `jarvis_tools` | `orch_flow_studio_tools` |
| `jarvis-invoke-demo` | `orch_flow_studio-invoke-demo` |
| `run_jarvis` | `run_orch_flow_studio` |
| `setup_jarvis` | `setup_orch_flow_studio` |
| `jarvis_dir` | `orch_flow_studio_dir` |
| `jarvis_agents` | `orch_flow_studio_agents` |
| `JARVIS_DIR` / `JARVIS` (shell vars) | `ORCH_FLOW_STUDIO_DIR` / `ORCH_FLOW_STUDIO` |
| `_JARVIS_CONFIG` | `_ORCH_FLOW_STUDIO_CONFIG` |
| `Jarvis` (display name in docs/comments/UI) | `Orch Flow Studio` |
| `jarvis` (catch-all: config paths, env vars) | `orch_flow_studio` |

### 5. Add `validate_email` to `register_orch_flow_studio_tools`

In `domains/orch_flow_studio/tools.py`, import `validate_email` from `common.tools.validation_tools` and include it in `register_orch_flow_studio_tools()` to demonstrate the shared-tool-in-domain pattern.

### 6. Files affected

**Source code:**
- `src/autobots_orch_flow_studio/configs/settings.py` — refactor to `AppSettings`
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/settings.py` — NEW: `OrchFlowStudioSettings`
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/server.py` — use `init_orch_flow_studio_settings()`
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/tools.py` — rename + add `validate_email`
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/services.py` — docstring update
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/orch_flow_studio_batch.py` — rename + content
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/call_invoke_agent.py` — content updates
- `src/autobots_orch_flow_studio/domains/orch_flow_studio/get_schema_for_agent.py` — content updates
- `src/autobots_orch_flow_studio/domains/customer_support/server.py` — `init_app_settings()`
- `src/autobots_orch_flow_studio/domains/sales/server.py` — `init_app_settings()`

**Tests:**
- `tests/conftest.py` — `AppSettings`, `_ORCH_FLOW_STUDIO_CONFIG_*`, docstring
- `tests/helpers.py` — `orch_flow_studio_tools_registered()`
- `tests/unit/domains/orch_flow_studio/conftest.py`
- `tests/unit/domains/orch_flow_studio/test_tools.py`
- `tests/integration/domains/orch_flow_studio/conftest.py`
- `tests/integration/domains/orch_flow_studio/test_batch.py`
- `tests/sanity/domains/orch_flow_studio/conftest.py`
- `tests/sanity/domains/orch_flow_studio/test_dynagent_canary.py`

**Config/infra:**
- `Makefile`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `sbin/run_orch_flow_studio.sh` (renamed from `run_jarvis.sh`)
- `sbin/run_all_domains.sh`
- `sbin/sanity_test.sh`
- `agent_configs/orch_flow_studio/agents.yaml`

**Docs:**
- `README.md` — all domain-level "Jarvis" → "Orch Flow Studio", keep repo name untouched

### 7. Docker: parameterize for per-domain images

**Dockerfile** — add `DOMAIN` build arg:
```dockerfile
ARG DOMAIN=orch_flow_studio
ENV APP_DOMAIN=${DOMAIN}
# ... rest of build unchanged ...
CMD ["sh", "-c", "bash sbin/run_${APP_DOMAIN}.sh"]
```

**docker-compose.yml** — three services with shared env via YAML anchors:
```yaml
x-common-env: &common-env
  GOOGLE_API_KEY: ${GOOGLE_API_KEY}
  LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-}
  # ... etc ...

services:
  orch_flow_studio-chat:
    build: { context: ., args: { DOMAIN: orch_flow_studio } }
    ports: ["1337:1337"]
    environment:
      <<: *common-env
      DYNAGENT_CONFIG_ROOT_DIR: /app/agent_configs/orch_flow_studio

  customer-support-chat:
    build: { context: ., args: { DOMAIN: customer_support } }
    ports: ["1338:1338"]
    environment:
      <<: *common-env
      DYNAGENT_CONFIG_ROOT_DIR: /app/agent_configs/customer-support

  sales-chat:
    build: { context: ., args: { DOMAIN: sales } }
    ports: ["1339:1339"]
    environment:
      <<: *common-env
      DYNAGENT_CONFIG_ROOT_DIR: /app/agent_configs/sales
```

**Makefile** — parameterize docker targets:
```makefile
DOMAIN ?= orch_flow_studio
docker-build:
    docker build --build-arg DOMAIN=$(DOMAIN) -t $(DOCKER_IMAGE_NAME)-$(DOMAIN) .
```

### 8. Update scaffold.py for two-level scaffolding

After rename, scaffold.py handles TWO independent name spaces:

1. **Source root**: `autobots_orch_flow_studio` → `autobots_<name>`
2. **Domain**: `orch_flow_studio` → `<primary_domain>`

Add `--primary-domain` flag (defaults to `<name>` for backward compat):
```
python3 sbin/scaffold.py kbe-pay                           # both levels = kbe_pay
python3 sbin/scaffold.py kbe-pay --primary-domain nurture   # src_root=kbe_pay, domain=nurture
```

Changes to scaffold.py:
- Add `--primary-domain` CLI arg
- Add `derive_domain_names()` for domain-level name variants (orch_flow_studio → new domain)
- Split `build_replacements()` into source-root replacements + domain replacements
- Update `rename_paths()` to handle `orch_flow_studio` → `<domain>` directory renames
- Update `PATHS_TO_REMOVE` to reference `orch_flow_studio` instead of `jarvis`
- Update domain settings: rename `OrchFlowStudioSettings` → `<Domain>Settings`, `orch_flow_studio_settings.py` → `<domain>_settings.py`

### 9. Update CLAUDE.md

Update workspace-level `CLAUDE.md` to reflect:
- Domain rename (jarvis → orch_flow_studio in domain references)
- New `AppSettings` / `OrchFlowStudioSettings` pattern
- Updated Docker multi-domain support
- Keep `autobots_orch_flow_studio` as source root unchanged

### 10. Phase 2 note (future)

Move hardcoded `APP_NAME` values to `app_constants.py` (shared) and `orch_flow_studio_constants.py` (domain). Not in scope for this change.

## Execution order

1. Rename directories (bottom-up to avoid breaking paths)
2. Rename files (`run_jarvis.sh`, `jarvis_batch.py`)
3. Refactor `configs/settings.py` → `AppSettings`
4. Create `domains/orch_flow_studio/settings.py` with `OrchFlowStudioSettings`
5. Apply content replacements across all text files
6. Update `customer_support/server.py` and `sales/server.py` → `init_app_settings()`
7. Add `validate_email` to `register_orch_flow_studio_tools()`
8. Update Dockerfile and docker-compose.yml for per-domain builds
9. Update scaffold.py for two-level support
10. Update README.md and CLAUDE.md
11. Run verification

## Verification

```bash
cd autobots-orch-flow-studio
make all-checks    # format, lint, type-check, test
```

Confirm no remaining domain-level "jarvis" references (excluding repo/package name):
```bash
grep -rn "jarvis" --include="*.py" --include="*.yaml" --include="*.sh" --include="*.toml" \
  src/ tests/ sbin/ agent_configs/ \
  | grep -v "autobots_orch_flow_studio" \
  | grep -v "autobots-orch-flow-studio"
```

Docker build test:
```bash
make docker-build DOMAIN=orch_flow_studio
make docker-build DOMAIN=customer_support
make docker-build DOMAIN=sales
```
