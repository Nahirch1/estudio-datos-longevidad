"""Capa de datos del tablero: lee la base SQLite (bi/estudio_longevidad.sqlite) y calcula todo con pandas.
Sin interfaz: se puede probar con `python3 tests/test_datos.py`."""
import pathlib, sqlite3
import pandas as pd

DB = pathlib.Path(__file__).resolve().parent.parent / 'bi' / 'estudio_longevidad.sqlite'
CON_PACIENTE = ['fact_visita', 'fact_resultado_paciente', 'dim_genetica_pro', 'fact_evento_previo', 'fact_informe_integracion']


PESADAS = ('fact_laboratorio', 'fact_biomarcador_muestra')   # ~100 mil filas por 85 columnas: se consultan por columna, no se cargan enteras


def cargar(db=DB):
    con = sqlite3.connect(db)
    try:
        nombres = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0] not in PESADAS]
        d = {n: pd.read_sql(f'SELECT * FROM {n}', con) for n in nombres}
        d['_db'] = str(db)
        return d
    finally:
        con.close()


def filtrar(d, programa=None, sexo=None, grupo_etario=None):
    """Devuelve una copia de las tablas con solo los pacientes que cumplen los filtros (listas vacías = todos)."""
    p = d['dim_paciente']
    for col, val in (('programa', programa), ('sexo', sexo), ('grupo_etario', grupo_etario)):
        if val:
            p = p[p[col].isin(val)]
    ids = set(p.patient_id)
    out = dict(d)
    out['dim_paciente'] = p
    for t in CON_PACIENTE:
        out[t] = d[t][d[t].patient_id.isin(ids)]
    vis = set(out['fact_visita'].visit_id)
    out['fact_condicion'] = d['fact_condicion'][d['fact_condicion'].visit_id.isin(vis)]
    return out


def _resultados(d):
    return d['fact_resultado_paciente'].merge(d['dim_paciente'][['patient_id', 'tiene_plan', 'protocolo', 'adherencia']], on='patient_id')


def kpis(d):
    v0 = d['fact_visita'][d['fact_visita'].visit_n == 0]
    r = _resultados(d)
    g = lambda col, plan: r[r.tiene_plan == plan][col].dropna()
    return dict(
        pacientes=int(d['dim_paciente'].patient_id.nunique()), visitas=int(len(d['fact_visita'])),
        brecha_inicial=float(v0.brecha_modificable.mean()), pct_acelerados=float((v0.brecha_modificable >= 2).mean() * 100),
        d12_plan=float(g('d_brecha_modificable_12m', 1).mean()), n12_plan=int(len(g('d_brecha_modificable_12m', 1))),
        d12_control=float(g('d_brecha_modificable_12m', 0).mean()), n12_control=int(len(g('d_brecha_modificable_12m', 0))),
        long12_plan=float(g('d_score_longevidad_12m', 1).mean()), long12_control=float(g('d_score_longevidad_12m', 0).mean()),
        resp6_plan=float(g('resp_6m', 1).mean() * 100), resp6_control=float(g('resp_6m', 0).mean() * 100))


def tendencia_brecha(d):
    v = d['fact_visita'].merge(d['dim_paciente'][['patient_id', 'protocolo']], on='patient_id')
    return v.groupby(['protocolo', 'hito']).brecha_modificable.mean().round(2).reset_index()


def tabla_protocolos(d):
    r = _resultados(d)
    t = r.groupby('protocolo').agg(pacientes=('patient_id', 'count'), delta_brecha_12m=('d_brecha_modificable_12m', 'mean'),
                                   delta_longevidad_12m=('d_score_longevidad_12m', 'mean'), pct_respondedores_6m=('resp_6m', 'mean'),
                                   ritmo=('ritmo_envejecimiento', 'mean')).round(2)
    t['pct_respondedores_6m'] = (t.pct_respondedores_6m * 100).round(1)
    return t.reset_index().sort_values('delta_brecha_12m')


def ritmo_por_adherencia(d):
    return _resultados(d).groupby('adherencia').ritmo_envejecimiento.mean().round(2).reindex(['Alta', 'Media', 'Baja']).reset_index()


def embudo(d):
    return d['fact_embudo'].sort_values('orden')


def condiciones(d):
    """% de visitas con la condición al inicio y a los 12 meses. fact_condicion guarda solo las presentes: el denominador sale de fact_visita."""
    vis = d['fact_visita'][d['fact_visita'].visit_n.isin([0, 2])]; den = vis.groupby('visit_n').size()
    c = d['fact_condicion'].merge(vis[['visit_id', 'visit_n']], on='visit_id')
    t = c.groupby(['condicion', 'visit_n']).size().unstack(fill_value=0)
    t = (t.div(den, axis=1) * 100).round(1).rename(columns={0: 'pct_inicio', 2: 'pct_12m'})
    return t.reset_index().sort_values('pct_inicio', ascending=False)


def _laboratorio(d, columna):
    """Una columna de fact_laboratorio para los pacientes del filtro actual (consulta directa a SQLite)."""
    validas = set(d['dim_biomarcador'].columna)
    if columna not in validas:
        raise ValueError(f'biomarcador desconocido: {columna}')
    con = sqlite3.connect(d['_db'])
    try:
        x = pd.read_sql(f'SELECT visit_id, patient_id, "{columna}" AS valor FROM fact_laboratorio WHERE "{columna}" IS NOT NULL', con)
    finally:
        con.close()
    return x[x.patient_id.isin(set(d['dim_paciente'].patient_id))]


def biomarcador(d, columna):
    b = _laboratorio(d, columna).merge(d['fact_visita'][['visit_id', 'hito']], on='visit_id')
    b = b.merge(d['dim_paciente'][['patient_id', 'protocolo']], on='patient_id')
    b['meses_desde_baseline'] = b.hito.map({'0m': 0, '6m': 6, '12m': 12})
    return b.groupby(['protocolo', 'meses_desde_baseline']).valor.mean().round(2).reset_index()


def lista_biomarcadores(d):
    """(columna, nombre, categoría, unidad) de todo lo que hay en laboratorio, ordenado por categoría."""
    b = d['dim_biomarcador']
    return b.sort_values(['categoria', 'biomarcador'])[['columna', 'biomarcador', 'categoria', 'unidad']]


def insulina(d):
    """Insulina en ayunas vs post-carga. La post-carga se midió en ~59% de las visitas y NO al azar: se pidió más cuando el HOMA-IR era alto."""
    ay, po = _laboratorio(d, 'insulina_ayunas'), _laboratorio(d, 'insulina_post_carga')
    vis = d['fact_visita'][['visit_id', 'hito', 'homa_ir'] if 'homa_ir' in d['fact_visita'] else ['visit_id', 'hito']]
    m = ay.merge(po[['visit_id', 'valor']], on='visit_id', how='left', suffixes=('_ayunas', '_post')).merge(vis, on='visit_id')
    t = m.groupby('hito').agg(visitas=('visit_id', 'count'), con_post_carga=('valor_post', 'count'), ayunas_mediana=('valor_ayunas', 'median'), post_mediana=('valor_post', 'median')).round(1)
    t['pct_con_post_carga'] = (100 * t.con_post_carga / t.visitas).round(1)
    return t.reset_index()


def genotipo_vs_biomarcador(d, marcador, columna):
    """Media de un biomarcador por genotipo de un marcador del panel (solo programa PRO, visita inicial)."""
    g = d['dim_genetica_pro'][['patient_id', marcador]]
    if marcador not in d['dim_genetica_pro'].columns:
        raise ValueError(marcador)
    b = _laboratorio(d, columna).merge(d['fact_visita'][d['fact_visita'].visit_n == 0][['visit_id']], on='visit_id').merge(g, on='patient_id')
    return b.groupby(marcador).valor.agg(pacientes='count', media='mean').round(2).reset_index()


def relojes(d):
    """Brecha media por hito: reloj de biomarcadores y hábitos (A/B) y PhenoAge (C)."""
    v = d['fact_visita']
    return v.groupby('hito')[['brecha_modificable', 'brecha_phenoage']].mean().round(2).reset_index()


def paciente(d, patient_id):
    v = d['fact_visita'][d['fact_visita'].patient_id == patient_id].sort_values('visit_n')
    return dict(perfil=d['dim_paciente'][d['dim_paciente'].patient_id == patient_id].iloc[0], visitas=v,
                informe=d['fact_informe_integracion'][d['fact_informe_integracion'].patient_id == patient_id],
                genetica=d['dim_genetica_pro'][d['dim_genetica_pro'].patient_id == patient_id],
                eventos=d['fact_evento_previo'][d['fact_evento_previo'].patient_id == patient_id])
