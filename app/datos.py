"""Capa de datos del tablero: lee la base SQLite (bi/estudio_longevidad.sqlite) y calcula todo con pandas.
Sin interfaz: se puede probar con `python3 tests/test_datos.py`."""
import pathlib, sqlite3
import pandas as pd

DB = pathlib.Path(__file__).resolve().parent.parent / 'bi' / 'estudio_longevidad.sqlite'
CON_PACIENTE = ['fact_visita', 'fact_resultado_paciente', 'dim_genetica_pro', 'fact_evento_previo', 'fact_informe_integracion']


def cargar(db=DB):
    con = sqlite3.connect(db)
    try:
        nombres = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {n: pd.read_sql(f'SELECT * FROM {n}', con) for n in nombres}
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
    for t in ('fact_biomarcador', 'fact_condicion'):
        out[t] = d[t][d[t].visit_id.isin(vis)]
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
    c = d['fact_condicion'].merge(d['fact_visita'][['visit_id', 'visit_n']], on='visit_id')
    c = c[c.visit_n.isin([0, 2])]
    t = c.groupby(['condicion', 'visit_n']).presente.mean().mul(100).round(1).unstack().rename(columns={0: 'pct_inicio', 2: 'pct_12m'})
    return t.reset_index().sort_values('pct_inicio', ascending=False)


def biomarcador(d, nombre):
    b = d['fact_biomarcador']
    b = b[b.biomarcador == nombre].merge(d['fact_visita'][['visit_id', 'meses_desde_baseline']], on='visit_id')
    b = b.merge(d['dim_paciente'][['patient_id', 'protocolo']], on='patient_id')
    return b.groupby(['protocolo', 'meses_desde_baseline']).valor.mean().round(2).reset_index()


def paciente(d, patient_id):
    v = d['fact_visita'][d['fact_visita'].patient_id == patient_id].sort_values('visit_n')
    return dict(perfil=d['dim_paciente'][d['dim_paciente'].patient_id == patient_id].iloc[0], visitas=v,
                informe=d['fact_informe_integracion'][d['fact_informe_integracion'].patient_id == patient_id],
                genetica=d['dim_genetica_pro'][d['dim_genetica_pro'].patient_id == patient_id],
                eventos=d['fact_evento_previo'][d['fact_evento_previo'].patient_id == patient_id])
