#!/bin/sh
set -eu
# Do not enable shell tracing: credentials are inherited only via environment.
export PATH="/opt/agent-tools/bin:$PATH"
test -n "${GH_TOKEN:-}"
test -n "${SYMPHONY_QUEUE_TOKEN:-}"
command -v gh >/dev/null
command -v python3 >/dev/null
command -v graphify >/dev/null
test -r /opt/skills/superpowers/using-superpowers/SKILL.md
test -r /opt/skills/graphify/SKILL.md
timeout 30 codex app-server --strict-config --print-startup-config
# Render from the same read-only registration used by the gate. Preserve all
# workspaces/pending state. The generated workflow is runtime configuration only.
test -n "${SYMPHONY_PROJECT:-}"
test -n "${SYMPHONY_REGISTRY:-}"
mkdir -p /work/runtime
python3 /runtime/machine.py --registry "$SYMPHONY_REGISTRY" \
  --project "$SYMPHONY_PROJECT" --output /work/runtime/WORKFLOW.md
exec /opt/symphony/bin/symphony /work/runtime/WORKFLOW.md \
  --logs-root /work/logs \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
