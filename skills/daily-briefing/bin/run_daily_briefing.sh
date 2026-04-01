#!/bin/bash
# run_daily_briefing.sh - Runs the daily briefing data gatherer
# TCC permissions are granted to Terminal.app (or the calling process)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR="${SCRIPT_DIR}/../scripts/daily_briefing_orchestrator.sh"

if [[ ! -f "$ORCHESTRATOR" ]]; then
  echo "Error: Orchestrator not found at $ORCHESTRATOR" >&2
  exit 1
fi

# Pass any arguments (e.g., --cleanup)
bash -l "$ORCHESTRATOR" "$@"
