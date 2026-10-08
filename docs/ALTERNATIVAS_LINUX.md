# Tableros sobre Linux: alternativas para el mismo modelo de datos

Todas leen lo mismo: `bi/estudio_longevidad.sqlite` o los CSV de `bi/`. La limpieza y los modelos se hacen una sola vez en Python (`ejecutar_todo.sh`).

| Herramienta | Cómo se arma | Corre en Debian | Cuenta | Cuándo conviene |
|---|---|---|---|---|
| **Apache Superset** (principal, en `superset/`) | Código y API: `cargar_tablero.sh` | Sí, venv o Docker | No (código abierto) | BI completo con SQL Lab y tableros, reproducible por terminal |
| **Streamlit + Plotly** (incluido en `app/`) | Código Python versionado | Sí, nativo (`pip install -r requirements.txt`) | No | Portfolio de datos: todo es código y se reproduce con un comando |
| **HTML autocontenido** (`dashboard_estudio_datos_longevidad.html`) | Generado por `05_armar_dashboard.py` | Sí, cualquier navegador | No | Compartir un link o publicar en GitHub Pages |
| **Metabase** | Interfaz web; consultas SQL guardadas | Sí, con Docker o con el .jar (Java) | No (versión de código abierto) | Que usuarios no técnicos exploren con preguntas guardadas |
| **Apache Superset** | Interfaz web + SQL Lab | Sí, con Docker | No | Más control y gráficos, a cambio de una instalación más pesada |
| **Grafana** | Paneles sobre una base de datos | Sí, nativo | No | Series de tiempo y monitoreo; menos natural para análisis clínico |
| **Looker Studio** | Interfaz web, armado manual | Sí, desde el navegador | Cuenta de Google | Cuando el equipo ya usa Google |
| **Power BI** | Escritorio (Windows) o servicio web | Desktop no; el servicio web exige cuenta de trabajo o estudio | Sí | Cuando la clínica ya usa Microsoft |

## Comandos de referencia
Superset: `superset/README_SUPERSET.md`. Streamlit: `streamlit run app/app_streamlit.py`. Metabase no se probó; seguí su documentación oficial.

    # Streamlit
    pip install -r requirements.txt
    ./ejecutar_todo.sh
    streamlit run app/app_streamlit.py

    # Metabase (Docker): imagen oficial metabase/metabase, puerto 3000
    # Superset (Docker): ver la guía oficial "Installing Superset from scratch / Docker Compose"

## Qué mostrar en un portfolio
Que el mismo modelo de datos alimenta varias herramientas: el valor está en la limpieza, el modelo estrella y las medidas, no en arrastrar gráficos con el mouse. Las consultas de `sql/consultas_kpi.sql` y las pruebas de `tests/` sirven como evidencia de que los números coinciden entre herramientas.
