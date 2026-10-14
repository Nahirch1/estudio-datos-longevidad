#!/usr/bin/env bash
# Corre el proyecto completo de punta a punta: datos -> limpieza -> modelos -> exportes -> pruebas (unos 10 minutos para 42.000 pacientes).
set -euo pipefail
cd "$(dirname "$0")"
python3 -I 01_generar_cohorte.py
python3 -I 02_generar_fuentes_crudas.py
python3 -I 03_pipeline_limpieza.py
python3 -I 04_modelos.py
python3 -I 05_armar_dashboard.py     # vista previa HTML
python3 -I 06_exportar_bi.py         # CSV, Excel (muestra) y base SQLite
python3 -I 07_generar_diccionario.py # docs/DICCIONARIO_DATOS.md
python3 -I tests/test_datos.py       # comprueba que los números coinciden
echo "Listo. Tablero principal: cd superset && ./instalar.sh && ./iniciar.sh && ./cargar_tablero.sh (ver superset/README_SUPERSET.md)"
