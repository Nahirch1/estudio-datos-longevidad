#!/usr/bin/env bash
# Instala Superset en un entorno virtual dentro de esta carpeta (Debian/Ubuntu). Ejecutar una sola vez.
set -euo pipefail
cd "$(dirname "$0")"
python3 --version
echo "Superset exige una versión de Python soportada (revisá la documentación oficial; si tu Debian trae una más nueva, usá docker-compose.yml)."
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev python3-venv libsasl2-dev libldap2-dev pkg-config
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install apache-superset rich cachetools "flask-caching<2.4"
[ -f .env ] || { echo "export SUPERSET_SECRET_KEY=$(openssl rand -base64 42)" > .env; echo 'export SUPERSET_ADMIN_PASSWORD=cambiame-esta-clave' >> .env; }
. ./.env
export FLASK_APP=superset SUPERSET_CONFIG_PATH="$PWD/superset_config.py"
superset db upgrade
superset fab create-admin --username admin --firstname Admin --lastname Local --email admin@local.test --password "$SUPERSET_ADMIN_PASSWORD"
superset init
echo "Listo. Editá superset/.env para cambiar la clave de admin si querés. Siguiente: ./iniciar.sh"
