#!/usr/bin/env bash
# Crea (o actualiza) conexión, datasets, gráficos y tablero en el Superset que esté corriendo en localhost:8088.
set -euo pipefail
cd "$(dirname "$0")"
. .venv/bin/activate
. ./.env
python3 configurar_dashboard.py
