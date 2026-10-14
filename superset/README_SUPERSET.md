# Tablero en Apache Superset, todo por terminal

Superset lee la base `bi/estudio_longevidad.sqlite` que genera `06_exportar_bi.py`. La configuración del tablero está en código (`configurar_dashboard.py`), así que se reproduce con comandos, sin armar nada con el mouse.

## Pasos (Debian)
```
./ejecutar_todo.sh                 # genera datos, limpieza, modelos y la base SQLite
cd superset
./instalar.sh                      # una sola vez: entorno virtual, Superset, usuario admin
./iniciar.sh                       # deja Superset en http://localhost:8088 (terminal 1)
./cargar_tablero.sh                # en otra terminal: crea conexión, datasets, gráficos y tablero
```
Después entrá a http://localhost:8088 con el usuario `admin` y la clave de `superset/.env`, y abrí el tablero "Estudio de Datos de Longevidad".

## Qué crea el script
- 1 conexión a la base SQLite.
- 18 conjuntos de datos, cada uno una consulta SQL (las mismas de `sql/consultas_kpi.sql`, más las nuevas de laboratorio y genética).
- 18 gráficos: 6 tarjetas de número (pacientes, brecha inicial, % acelerados, analitos, marcadores genéticos, hiperinsulinemia post-carga con ayunas normal), embudo, histograma de la brecha, plan vs. estándar, brecha por protocolo, respondedores a 6 meses, ritmo por adherencia, insulina en ayunas vs. post-carga, dos relojes de edad biológica, Lp(a) por genotipo, ferritina por variante HFE, padecimientos y validación de la limpieza.
- 1 tablero con todos los gráficos.

Se puede volver a correr: actualiza lo existente en lugar de duplicarlo.

## Qué está probado y qué no
- **Probado:** las 18 consultas SQL de los conjuntos de datos sobre la base real, con los números esperados (42.000 pacientes, 0,70, 27,4%, −0,33 y +0,17 a 12 meses). También la secuencia de llamadas del script, contra un servidor simulado (crea 38 elementos —conexión, 18 conjuntos de datos, 18 gráficos y el tablero— y los actualiza al repetir, sin duplicar).
- **No probado:** la instalación de Superset y las llamadas contra un Superset real, porque este entorno no puede instalar paquetes. Los tipos de gráfico y sus parámetros pueden variar entre versiones de Superset. Si alguno falla, el script se detiene y muestra el mensaje de error de la API con el nombre del gráfico; con ese mensaje se ajusta un solo parámetro.
- El diseño del tablero (orden y tamaño de los gráficos) lo arma Superset de forma automática la primera vez. Si querés acomodarlo, se hace desde la interfaz o se ajusta en el código.

## Problemas frecuentes
- **`TypeError: SupersetMetastoreCache.__init__() got an unexpected keyword argument 'ignore_delete_many_errors'`**: `flask-caching` demasiado nuevo para esa versión de Superset. Dentro del entorno: `pip install "flask-caching<2.4"` y repetí el comando que falló. Ya está en `instalar.sh`.
- **`ModuleNotFoundError: No module named 'rich'`** al correr `superset`: ejecutá `pip install rich` dentro del entorno (`. .venv/bin/activate`) y repetí el comando que falló. Ya está incluido en `instalar.sh`.
- **Python no soportado:** Superset exige ciertas versiones de Python. Revisá `python3 --version` contra la documentación oficial; si tu Debian trae una más nueva, usá `docker-compose.yml` (no probado) y corré el script con `DB_PATH=/data/estudio_longevidad.sqlite`.
- **Error de conexión con SQLite:** `superset_config.py` ya desactiva el bloqueo por defecto de SQLite. Verificá que `SUPERSET_CONFIG_PATH` apunte a ese archivo (lo hacen los scripts).
- **Falta de paquetes al instalar:** corré `instalar.sh` con permisos de `sudo` para las librerías del sistema.

### La API devuelve 422 «La conexión ha fallado» al crear la base
Registrá la base por CLI (no hace prueba de conexión) y volvé a correr `./cargar_tablero.sh`, que reutiliza la conexión existente:
```
. .venv/bin/activate; . ./.env
export FLASK_APP=superset SUPERSET_CONFIG_PATH="$PWD/superset_config.py"
superset set-database-uri -d "Estudio de Datos de Longevidad" -u "sqlite:///$(realpath ../bi/estudio_longevidad.sqlite)"
```

### `ModuleNotFoundError: No module named 'cachetools'` (API 500 / «La conexión ha fallado»)
Falta una dependencia que el paquete no declara. Con el venv activo: `pip install cachetools`, reiniciar `./iniciar.sh` y volver a correr `./cargar_tablero.sh`. Si aparece otro módulo faltante, se instala igual (`pip install <módulo>`).
