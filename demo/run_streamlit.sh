#!/usr/bin/env bash
# Launch the Agent Colosseum Streamlit dashboard
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$DIR")"
cd "$PROJECT"
exec .venv/bin/streamlit run demo/app.py --server.headless true "$@"
