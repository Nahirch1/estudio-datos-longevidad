#!/usr/bin/env bash
# Arranca Superset en http://localhost:8088 (usuario admin).
set -euo pipefail
cd "$(dirname "$0")"
. .venv/bin/activate
. ./.env
export FLASK_APP=superset SUPERSET_CONFIG_PATH="$PWD/superset_config.py"
superset run -p 8088 --with-threads
