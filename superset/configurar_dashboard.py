"""Crea en Superset, por API y sin tocar la interfaz: la conexión a la base, los conjuntos de datos (consultas SQL),
los gráficos y el tablero "Estudio de Datos de Longevidad". Se puede correr varias veces (actualiza lo existente).

Uso:  . .venv/bin/activate && . ./.env && python3 configurar_dashboard.py
Variables: SUPERSET_URL (http://localhost:8088), SUPERSET_USER (admin), SUPERSET_ADMIN_PASSWORD, DB_PATH (ruta a la base SQLite)."""
import json, os, pathlib, sys
import requests

URL = os.environ.get('SUPERSET_URL', 'http://localhost:8088').rstrip('/')
USER = os.environ.get('SUPERSET_USER', 'admin')
PASS = os.environ.get('SUPERSET_ADMIN_PASSWORD', 'admin')
DB_PATH = os.environ.get('DB_PATH', str(pathlib.Path(__file__).resolve().parent.parent / 'bi' / 'estudio_longevidad.sqlite'))
DB_NAME, DASH_TITLE, DASH_SLUG = 'Estudio de Datos de Longevidad', 'Estudio de Datos de Longevidad', 'estudio-datos-longevidad'

s = requests.Session()


def login():
    r = s.post(f'{URL}/api/v1/security/login', json={'username': USER, 'password': PASS, 'provider': 'db', 'refresh': True})
    r.raise_for_status()
    s.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
    c = s.get(f'{URL}/api/v1/security/csrf_token/')
    c.raise_for_status()
    s.headers.update({'X-CSRFToken': c.json()['result'], 'Referer': URL, 'Content-Type': 'application/json'})


def listar(recurso, campo):
    r = s.get(f'{URL}/api/v1/{recurso}/', params={'q': '(page_size:1000)'})
    r.raise_for_status()
    return {x[campo]: x['id'] for x in r.json()['result']}


def guardar(recurso, campo, nombre, cuerpo, existentes):
    if nombre in existentes:
        if recurso == 'dataset':  # la API de edición no acepta 'database' ni 'table_name'
            cuerpo = {'sql': cuerpo['sql']}
        r = s.put(f'{URL}/api/v1/{recurso}/{existentes[nombre]}', json=cuerpo)
        accion, i = 'actualizado', existentes[nombre]
    else:
        r = s.post(f'{URL}/api/v1/{recurso}/', json=cuerpo)
        accion, i = 'creado', None
    if not r.ok:
        sys.exit(f'ERROR en {recurso} "{nombre}": {r.status_code} {r.text[:600]}')
    i = i or r.json().get('id')
    print(f'  {accion}: {recurso} {nombre} (id {i})')
    return i


# ---- consultas (conjuntos de datos virtuales); misma lógica que sql/consultas_kpi.sql
V0 = "FROM fact_visita WHERE visit_n = 0"
DATASETS = {
    'kpi_pacientes': "SELECT COUNT(DISTINCT patient_id) AS pacientes FROM fact_visita",
    'kpi_brecha_inicial': f"SELECT ROUND(AVG(brecha_modificable), 2) AS brecha_inicial {V0}",
    'kpi_pct_acelerados': f"SELECT ROUND(100.0 * AVG(brecha_modificable >= 2), 1) AS pct_acelerados {V0}",
    'embudo': "SELECT orden || ' · ' || etapa AS etapa, pacientes FROM fact_embudo",
    'histograma_brecha': f"SELECT brecha_modificable {V0}",
    'plan_vs_estandar_12m': """SELECT CASE WHEN p.tiene_plan = 1 THEN 'Con plan' ELSE 'Seguimiento estándar' END AS grupo, COUNT(r.d_brecha_modificable_12m) AS pacientes,
        ROUND(AVG(r.d_brecha_modificable_12m), 2) AS delta_brecha_12m, ROUND(AVG(r.d_score_longevidad_12m), 2) AS delta_longevidad_12m, ROUND(AVG(r.d_n_condiciones_12m), 2) AS delta_condiciones_12m
        FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) WHERE r.d_brecha_modificable_12m IS NOT NULL GROUP BY 1""",
    'tendencia_brecha': """SELECT p.protocolo AS protocolo, CASE v.visit_n WHEN 0 THEN 0 WHEN 1 THEN 6 ELSE 12 END AS mes, ROUND(AVG(v.brecha_modificable), 2) AS brecha_media
        FROM fact_visita v JOIN dim_paciente p USING (patient_id) GROUP BY 1, 2""",
    'respondedores_6m': """SELECT p.protocolo AS protocolo, ROUND(100.0 * AVG(r.resp_6m), 1) AS pct_respondedores, COUNT(r.resp_6m) AS pacientes
        FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) WHERE r.resp_6m IS NOT NULL GROUP BY 1""",
    'ritmo_por_adherencia': """SELECT p.adherencia AS adherencia, ROUND(AVG(r.ritmo_envejecimiento), 2) AS ritmo_envejecimiento
        FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) GROUP BY 1""",
    # fact_condicion guarda solo las condiciones presentes: el denominador es el total de visitas de cada hito
    'padecimientos': """SELECT c.condicion AS condicion,
        ROUND(100.0 * SUM(CASE WHEN v.visit_n = 0 THEN 1 ELSE 0 END) / (SELECT COUNT(*) FROM fact_visita WHERE visit_n = 0), 1) AS pct_inicio,
        ROUND(100.0 * SUM(CASE WHEN v.visit_n = 2 THEN 1 ELSE 0 END) / (SELECT COUNT(*) FROM fact_visita WHERE visit_n = 2), 1) AS pct_12m
        FROM fact_condicion c JOIN fact_visita v USING (visit_id) GROUP BY 1 ORDER BY 2 DESC""",
    'kpi_analitos': "SELECT COUNT(*) AS analitos FROM dim_biomarcador",
    'kpi_marcadores_geneticos': "SELECT COUNT(*) AS marcadores FROM dim_marcador_genetico",
    'insulina_ayunas_vs_post': """SELECT CASE v.visit_n WHEN 0 THEN 0 WHEN 1 THEN 6 ELSE 12 END AS mes, 'En ayunas' AS medicion, ROUND(AVG(l.insulina_ayunas), 1) AS insulina
        FROM fact_laboratorio l JOIN fact_visita v USING (visit_id) GROUP BY 1
        UNION ALL
        SELECT CASE v.visit_n WHEN 0 THEN 0 WHEN 1 THEN 6 ELSE 12 END, 'Post-carga (2 h)', ROUND(AVG(l.insulina_post_carga), 1)
        FROM fact_laboratorio l JOIN fact_visita v USING (visit_id) WHERE l.insulina_post_carga IS NOT NULL GROUP BY 1""",
    'kpi_hiperinsulinemia_oculta': """SELECT ROUND(100.0 * SUM(CASE WHEN l.insulina_ayunas < 12 AND c.visit_id IS NOT NULL THEN 1 ELSE 0 END) / SUM(CASE WHEN l.insulina_ayunas < 12 THEN 1 ELSE 0 END), 1) AS pct_oculta
        FROM fact_laboratorio l JOIN fact_visita v USING (visit_id)
        LEFT JOIN fact_condicion c ON c.visit_id = l.visit_id AND c.condicion = 'hiperinsulinemia_postcarga'
        WHERE v.visit_n = 0 AND l.insulina_post_carga IS NOT NULL""",
    'relojes_por_hito': """SELECT CASE visit_n WHEN 0 THEN 0 WHEN 1 THEN 6 ELSE 12 END AS mes, 'Biomarcadores + hábitos' AS reloj, ROUND(AVG(brecha_modificable), 2) AS brecha FROM fact_visita GROUP BY 1
        UNION ALL
        SELECT CASE visit_n WHEN 0 THEN 0 WHEN 1 THEN 6 ELSE 12 END, 'PhenoAge (Levine 2018)', ROUND(AVG(brecha_phenoage), 2) FROM fact_visita GROUP BY 1""",
    'lpa_por_genotipo': """SELECT g.lpa_rs10455872 AS genotipo, ROUND(AVG(l.lipoproteina_a), 1) AS lipoproteina_a_media
        FROM dim_genetica_pro g JOIN fact_visita v ON v.patient_id = g.patient_id AND v.visit_n = 0 JOIN fact_laboratorio l ON l.visit_id = v.visit_id GROUP BY 1""",
    'ferritina_por_hfe': """SELECT CASE g.hfe WHEN 'sin variantes' THEN '1 · ninguna' WHEN 'H63D portador' THEN '2 · H63D' WHEN 'C282Y portador' THEN '3 · C282Y' ELSE '4 · compuesto' END AS variante_hfe, ROUND(AVG(l.ferritina), 0) AS ferritina_media
        FROM dim_genetica_pro g JOIN fact_visita v ON v.patient_id = g.patient_id AND v.visit_n = 0 JOIN fact_laboratorio l ON l.visit_id = v.visit_id GROUP BY 1""",
    'calidad_validacion': "SELECT grupo, comparados, correctos, exactitud FROM fact_calidad_validacion",
}


def metrica(sql, etiqueta):
    return {'expressionType': 'SQL', 'sqlExpression': sql, 'label': etiqueta}


def numero(ds, col, titulo, fmt=',.0f', sub=''):
    return dict(nombre=titulo, ds=ds, viz='big_number_total', p={'metric': metrica(f'MAX({col})', col), 'subheader': sub, 'y_axis_format': fmt, 'header_font_size': 0.4, 'subheader_font_size': 0.15})


def tabla(ds, cols, titulo, fmt=None):
    p = {'query_mode': 'raw', 'all_columns': cols, 'row_limit': 1000, 'order_desc': False}
    if fmt:  # formato numérico por columna (usa el separador argentino de superset_config.py)
        p['column_config'] = {c: {'d3NumberFormat': f} for c, f in fmt.items()}
    return dict(nombre=titulo, ds=ds, viz='table', p=p)


def barras(ds, x, y, titulo, serie=None, horizontal=False):
    p = {'x_axis': x, 'metrics': [metrica(f'MAX({y})', y)], 'groupby': [serie] if serie else [], 'row_limit': 1000, 'orientation': 'horizontal' if horizontal else 'vertical', 'show_legend': bool(serie)}
    return dict(nombre=titulo, ds=ds, viz='echarts_timeseries_bar', p=p)


def lineas(ds, x, y, serie, titulo):
    p = {'x_axis': x, 'metrics': [metrica(f'MAX({y})', y)], 'groupby': [serie], 'row_limit': 1000, 'show_legend': True, 'markerEnabled': True}
    return dict(nombre=titulo, ds=ds, viz='echarts_timeseries_line', p=p)


CHARTS = [
    numero('kpi_pacientes', 'pacientes', 'Pacientes', ',.0f', 'pacientes sintéticos'),
    numero('kpi_brecha_inicial', 'brecha_inicial', 'Brecha inicial (años)', ',.2f', 'años de edad biológica sobre la cronológica'),
    numero('kpi_pct_acelerados', 'pct_acelerados', '% con 2 o más años de aceleración', ',.1f', '% de los pacientes'),
    barras('embudo', 'etapa', 'pacientes', 'Embudo (simulado)', horizontal=True),
    dict(nombre='Brecha modificable (años)', ds='histograma_brecha', viz='histogram_v2', p={'column': 'brecha_modificable', 'bins': 30, 'row_limit': 10000}),
    tabla('plan_vs_estandar_12m', ['grupo', 'pacientes', 'delta_brecha_12m', 'delta_longevidad_12m', 'delta_condiciones_12m'], 'Plan vs. seguimiento estándar a 12 meses', {'pacientes': ',d', 'delta_brecha_12m': ',.2f', 'delta_longevidad_12m': ',.2f', 'delta_condiciones_12m': ',.2f'}),
    lineas('tendencia_brecha', 'mes', 'brecha_media', 'protocolo', 'Brecha media por protocolo'),
    barras('respondedores_6m', 'protocolo', 'pct_respondedores', '% de respondedores a 6 meses', horizontal=True),
    barras('ritmo_por_adherencia', 'adherencia', 'ritmo_envejecimiento', 'Ritmo de envejecimiento por adherencia'),
    tabla('padecimientos', ['condicion', 'pct_inicio', 'pct_12m'], 'Padecimientos: inicio vs. 12 meses (%)', {'pct_inicio': ',.1f', 'pct_12m': ',.1f'}),
    numero('kpi_analitos', 'analitos', 'Analitos y mediciones por visita', ',.0f', 'analitos de laboratorio y otros estudios en el catálogo'),
    numero('kpi_marcadores_geneticos', 'marcadores', 'Marcadores genéticos (PRO)', ',.0f', 'panel ficticio de variantes'),
    numero('kpi_hiperinsulinemia_oculta', 'pct_oculta', 'Hiperinsulinemia post-carga con insulina en ayunas normal (%)', ',.1f', 'de quienes tienen las dos mediciones'),
    barras('insulina_ayunas_vs_post', 'mes', 'insulina', 'Insulina media: ayunas vs. post-carga (µU/mL)', serie='medicion'),
    lineas('relojes_por_hito', 'mes', 'brecha', 'reloj', 'Brecha de edad biológica: dos relojes'),
    barras('lpa_por_genotipo', 'genotipo', 'lipoproteina_a_media', 'Lipoproteína (a) por genotipo LPA'),
    barras('ferritina_por_hfe', 'variante_hfe', 'ferritina_media', 'Ferritina por variante HFE'),
    tabla('calidad_validacion', ['grupo', 'comparados', 'correctos', 'exactitud'], 'Validación de la limpieza de datos', {'comparados': ',d', 'correctos': ',d', 'exactitud': ',.1f'}),
]


# filas del tablero: (altura en unidades de 8 px, [(nombre del gráfico, ancho de 1 a 12), ...])
FILAS = [
    (22, [('Pacientes', 4), ('Brecha inicial (años)', 4), ('% con 2 o más años de aceleración', 4)]),
    (42, [('Embudo (simulado)', 4), ('Brecha modificable (años)', 4), ('% de respondedores a 6 meses', 4)]),
    (26, [('Plan vs. seguimiento estándar a 12 meses', 12)]),
    (42, [('Brecha media por protocolo', 6), ('Ritmo de envejecimiento por adherencia', 6)]),
    (22, [('Analitos y mediciones por visita', 4), ('Marcadores genéticos (PRO)', 4), ('Hiperinsulinemia post-carga con insulina en ayunas normal (%)', 4)]),
    (42, [('Insulina media: ayunas vs. post-carga (µU/mL)', 6), ('Brecha de edad biológica: dos relojes', 6)]),
    (42, [('Lipoproteína (a) por genotipo LPA', 6), ('Ferritina por variante HFE', 6)]),
    (50, [('Padecimientos: inicio vs. 12 meses (%)', 6), ('Validación de la limpieza de datos', 6)]),
]


def disposicion_tablero(dash_id, ch_id):
    pos = {'DASHBOARD_VERSION_KEY': 'v2',
           'ROOT_ID': {'type': 'ROOT', 'id': 'ROOT_ID', 'children': ['GRID_ID']},
           'GRID_ID': {'type': 'GRID', 'id': 'GRID_ID', 'children': [], 'parents': ['ROOT_ID']}}
    for n, (alto, items) in enumerate(FILAS, 1):
        fila = f'ROW-{n}'
        pos['GRID_ID']['children'].append(fila)
        pos[fila] = {'type': 'ROW', 'id': fila, 'children': [], 'parents': ['ROOT_ID', 'GRID_ID'], 'meta': {'background': 'BACKGROUND_TRANSPARENT'}}
        for nombre, ancho in items:
            cid = f'CHART-{ch_id[nombre]}'
            pos[fila]['children'].append(cid)
            pos[cid] = {'type': 'CHART', 'id': cid, 'children': [], 'parents': ['ROOT_ID', 'GRID_ID', fila],
                        'meta': {'chartId': ch_id[nombre], 'width': ancho, 'height': alto, 'sliceName': nombre}}
    r = s.put(f'{URL}/api/v1/dashboard/{dash_id}', json={'position_json': json.dumps(pos)})
    if not r.ok:
        sys.exit(f'ERROR al ordenar el tablero: {r.status_code} {r.text[:600]}')
    print(f'  tablero ordenado en {len(FILAS)} filas')


def main():
    if not pathlib.Path(DB_PATH).exists() and not DB_PATH.startswith('/data/'):
        sys.exit(f'No existe la base {DB_PATH}. Corré antes ../ejecutar_todo.sh')
    login()
    print('Conexión a la base')
    dbs = listar('database', 'database_name')
    db_id = dbs.get(DB_NAME) or guardar('database', 'database_name', DB_NAME, {'database_name': DB_NAME, 'sqlalchemy_uri': f'sqlite:///{DB_PATH}', 'expose_in_sqllab': True}, dbs)
    print('Conjuntos de datos')
    dss = listar('dataset', 'table_name')
    ds_id = {n: guardar('dataset', 'table_name', n, {'database': db_id, 'schema': 'main', 'table_name': n, 'sql': q}, dss) for n, q in DATASETS.items()}
    print('Tablero')
    dashes = listar('dashboard', 'dashboard_title')
    dash_id = guardar('dashboard', 'dashboard_title', DASH_TITLE, {'dashboard_title': DASH_TITLE, 'slug': DASH_SLUG, 'published': True}, dashes)
    print('Gráficos')
    charts = listar('chart', 'slice_name')
    ch_id = {}
    for c in CHARTS:
        params = dict(c['p'], viz_type=c['viz'], datasource=f"{ds_id[c['ds']]}__table", adhoc_filters=[])
        cuerpo = {'slice_name': c['nombre'], 'viz_type': c['viz'], 'datasource_id': ds_id[c['ds']], 'datasource_type': 'table', 'params': json.dumps(params), 'dashboards': [dash_id]}
        ch_id[c['nombre']] = guardar('chart', 'slice_name', c['nombre'], cuerpo, charts)
    print('Diseño del tablero')
    disposicion_tablero(dash_id, ch_id)
    print(f'\nListo: {URL}/superset/dashboard/{DASH_SLUG}/')


if __name__ == '__main__':
    main()
