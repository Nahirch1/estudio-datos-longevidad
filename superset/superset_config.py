"""Configuración local de Superset para el proyecto (uso en la propia máquina, sin exponer a internet)."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
# Superset bloquea SQLite por defecto; es seguro aquí porque la base es de solo lectura y local.
PREVENT_UNSAFE_DB_CONNECTIONS = False
TALISMAN_ENABLED = False          # servir por http en localhost
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {"es": {"flag": "es", "name": "Español"}, "en": {"flag": "us", "name": "English"}}
ROW_LIMIT = 50000

# Números en formato argentino: 1.500 y 0,33
D3_FORMAT = {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]}
