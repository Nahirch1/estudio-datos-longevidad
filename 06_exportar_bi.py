"""Exporta el modelo en estrella para Power BI / Looker Studio / BigQuery (carpeta bi/).
Sin datos personales (DNI, nombre, apellido): el BI trabaja solo con patient_id."""
import json, pathlib
import pandas as pd
b = pathlib.Path(__file__).parent; out = b/'bi'; out.mkdir(exist_ok=True)
v = pd.read_csv(b/'resultados/visitas_con_modelos.csv', parse_dates=['fecha_visita'])
r = pd.read_csv(b/'resultados/pacientes_resumen_longitudinal.csv')
pa = pd.read_csv(b/'datos/cohorte/pacientes.csv', parse_dates=['fecha_consulta', 'fecha_estudios', 'fecha_integracion'])
inf = pd.read_csv(b/'resultados/informe_integracion_borrador.csv')
ev = pd.read_csv(b/'datos/cohorte/eventos_clinicos.csv')
emb = json.loads((b/'datos/cohorte/embudo.json').read_text())
cal = json.loads((b/'datos/pipeline_salida/calidad_datos.json').read_text(encoding='utf-8'))
w = lambda df, n: df.to_csv(out/f'{n}.csv', index=False, encoding='utf-8')

# ---- dimensiones
b0 = v[v.visit_n == 0].set_index('patient_id')
dp = pa[['patient_id', 'sexo', 'localidad', 'programa', 'protocolo', 'adherencia', 'cobertura_anamnesis_pct', 'n_eventos_previos', 'fam_cardiovascular', 'fam_diabetes', 'fam_cancer', 'fam_neurodegenerativa', 'intol_lactosa_detectada', 'intol_gluten_detectada']].copy()
dp['edad_inicial'] = dp.patient_id.map(b0.edad_cronologica).round(1)
dp['grupo_etario'] = pd.cut(dp.edad_inicial, [0, 39, 49, 59, 69, 120], labels=['<40', '40-49', '50-59', '60-69', '70+']).astype(str)
dp['segmento'] = dp.patient_id.map(r.set_index('patient_id').segmento)
dp['tiene_plan'] = (dp.protocolo != 'Seguimiento estándar').astype(int)
dp['intol_gluten_real'] = dp.patient_id.map(r.set_index('patient_id').intol_gluten_real)
dp['intol_lactosa_real'] = dp.patient_id.map(r.set_index('patient_id').intol_lactosa_real)
w(dp, 'dim_paciente')
gen = v[(v.visit_n == 0) & (v.programa == 'PRO')][['patient_id', 'apoe', 'apoe_e4_carrier', 'mthfr_c677t', 'fto_alelos_riesgo', 'ace_id', 'lct_13910', 'hla_dq2_dq8', 'vdr_foki', 'cyp1a2_cafeina', 'gstt1', 'prs_metabolico', 'brecha_genetica_fija']]
w(gen, 'dim_genetica_pro')
prot = pd.DataFrame({'protocolo': ['Seguimiento estándar', 'Nutrición metabólica', 'Suplementación antioxidante', 'Entrenamiento VO2máx + sueño', 'Suplementación y minerales', 'Combinado integral']})
prot['orden'] = range(1, 7); prot['tiene_plan'] = (prot.protocolo != 'Seguimiento estándar').astype(int)
w(prot, 'dim_protocolo')
f = pd.date_range(v.fecha_visita.min().normalize(), v.fecha_visita.max().normalize(), freq='D')
w(pd.DataFrame({'fecha': f, 'anio': f.year, 'mes': f.month, 'anio_mes': f.strftime('%Y-%m')}), 'dim_fecha')
dom = pd.DataFrame({'dominio': ['Metabolismo', 'Inflamación', 'Cardiovascular', 'Detoxificación', 'Rendimiento físico y cognitivo'], 'columna_score': ['score_metabolismo', 'score_inflamacion', 'score_cardiovascular', 'score_detoxificacion', 'score_rendimiento']}); dom['orden'] = range(1, 6)
w(dom, 'dim_dominio')

# ---- hechos
VIS = ['visit_id', 'patient_id', 'visit_n', 'hito', 'meses_desde_baseline', 'fecha_visita', 'edad_cronologica', 'edad_biologica_modificable', 'brecha_modificable', 'brecha_genetica_fija', 'brecha_total_pro', 'score_longevidad',
       'score_metabolismo', 'score_inflamacion', 'score_cardiovascular', 'score_detoxificacion', 'score_rendimiento', 'n_condiciones', 'alerta_metabolica_temprana',
       'celular_en_cama', 'sesiones_fuerza_sem', 'min_cardio_sem', 'sedentarismo_h_dia', 'ultraprocesados_sem', 'alcohol_sem', 'dieta_mediterranea_score', 'tabaquismo', 'estres_percibido', 'ansiedad_score', 'calidad_sueno', 'sueno_horas', 'hora_acostarse',
       'energia', 'claridad_mental', 'dolor', 'molestias_digestivas', 'hallazgo_principal']
w(v[VIS], 'fact_visita')
UN = {'glucosa': ('Metabólico', 'mg/dL'), 'hba1c': ('Metabólico', '%'), 'insulina': ('Metabólico', 'µU/mL'), 'homa_ir': ('Metabólico', 'índice'), 'trigliceridos': ('Cardiovascular', 'mg/dL'), 'ldl': ('Cardiovascular', 'mg/dL'), 'hdl': ('Cardiovascular', 'mg/dL'),
      'colesterol_total': ('Cardiovascular', 'mg/dL'), 'pa_sistolica': ('Cardiovascular', 'mmHg'), 'homocisteina': ('Cardiovascular', 'µmol/L'), 'pcr_us': ('Inflamación', 'mg/L'), 'drom_ucarr': ('Estrés oxidativo', 'U.CARR'), 'pic_indice': ('Estrés oxidativo', 'índice (placeholder)'),
      'ferritina': ('Nutrientes', 'ng/mL'), 'vitamina_d': ('Nutrientes', 'ng/mL'), 'b12': ('Nutrientes', 'pg/mL'), 'tsh': ('Hormonal', 'µUI/mL'), 'carga_metales_idx': ('Minerales y metales', 'índice'), 'vo2max_ml_kg_min': ('Rendimiento', 'ml/kg/min'),
      'fuerza_agarre_kg': ('Rendimiento', 'kg'), 'masa_magra_kg': ('Composición', 'kg'), 'grasa_corporal_pct': ('Composición', '%'), 'hrv_rmssd_ms': ('Rendimiento', 'ms'), 'pasos_dia': ('Actividad', 'pasos')}
UN.update({c: ('Minerales y metales', 'valor Oligoscan (ficticio)') for c in v.columns if c.startswith('oligo_')})
bm = v.melt(id_vars=['visit_id', 'patient_id'], value_vars=list(UN), var_name='biomarcador', value_name='valor').dropna(subset=['valor'])
bm['categoria'] = bm.biomarcador.map(lambda x: UN[x][0]); bm['unidad'] = bm.biomarcador.map(lambda x: UN[x][1])
w(bm, 'fact_biomarcador')
cc = [c for c in v.columns if c.startswith('cond_')]
cd = v.melt(id_vars=['visit_id', 'patient_id'], value_vars=cc, var_name='condicion', value_name='presente'); cd['condicion'] = cd.condicion.str.replace('cond_', '')
w(cd, 'fact_condicion')
rs = r[['patient_id', 'brecha_0', 'longevidad_0', 'd_brecha_modificable_6m', 'd_brecha_modificable_12m', 'd_score_longevidad_6m', 'd_score_longevidad_12m', 'd_n_condiciones_12m', 'd_energia_12m', 'd_dolor_12m', 'd_claridad_mental_12m', 'd_molestias_digestivas_12m',
        'd_ultraprocesados_sem_12m', 'd_sesiones_fuerza_sem_12m', 'd_estres_percibido_12m', 'd_calidad_sueno_12m', 'ritmo_envejecimiento', 'resp_6m', 'resp_12m', 'grp_gluten', 'grp_lactosa']]
w(rs, 'fact_resultado_paciente')
w(ev, 'fact_evento_previo')
w(inf, 'fact_informe_integracion')
orden = ['consultas', 'estudios', 'integracion', 'control_6m', 'control_12m']
w(pd.DataFrame({'etapa': orden, 'orden': range(1, 6), 'pacientes': [emb[k] for k in orden]}), 'fact_embudo')
w(pd.DataFrame([{'problema': k, 'cantidad': n} for k, n in cal['problemas_resueltos'].items()]), 'fact_calidad_problemas')
w(pd.DataFrame(cal['validacion']), 'fact_calidad_validacion')
print({p.stem: len(pd.read_csv(p)) for p in sorted(out.glob('*.csv'))})

# ---- Libro único para Power BI web (cada hoja es una tabla de Excel con nombre = nombre de la tabla)
try:
    import xlsxwriter
    xp = out/'estudio_longevidad_modelo.xlsx'
    wb = xlsxwriter.Workbook(str(xp), {'constant_memory': False, 'strings_to_numbers': False})
    for p in sorted(out.glob('*.csv')):
        d = pd.read_csv(p); ws = wb.add_worksheet(p.stem[:31])
        for c in d.columns:
            if d[c].dtype == object: d[c] = d[c].fillna('')
        d = d.astype(object).where(d.notna(), None)
        cols = list(d.columns)
        for c in cols:
            if c.startswith('fecha'): d[c] = pd.to_datetime(d[c]).dt.to_pydatetime()
        fd = wb.add_format({'num_format': 'yyyy-mm-dd'})
        ws.add_table(0, 0, len(d), len(cols) - 1, {'name': p.stem, 'columns': [dict(header=c, format=fd) if c.startswith('fecha') else dict(header=c) for c in cols], 'data': d.values.tolist(), 'style': 'Table Style Light 1'})
    wb.close(); print('xlsx ok', round(xp.stat().st_size / 1e6, 1), 'MB')
except ImportError:
    print('xlsxwriter no instalado: pip install xlsxwriter')

# ---- Tablas planas para Looker Studio (sin necesidad de combinar fuentes)
lk = out/'looker'; lk.mkdir(exist_ok=True)
at = dp[['patient_id', 'sexo', 'grupo_etario', 'programa', 'protocolo', 'tiene_plan', 'adherencia', 'segmento']]
vis = v[VIS].drop(columns=['hallazgo_principal']).merge(at.drop(columns=['sexo']).rename(columns={}), on='patient_id', how='left').merge(dp[['patient_id', 'sexo']], on='patient_id')
vis['fecha_visita'] = vis.fecha_visita.dt.strftime('%Y-%m-%d')
vis.to_csv(lk/'lk_visitas.csv', index=False)
vis_key = vis[['visit_id', 'visit_n', 'hito', 'meses_desde_baseline', 'fecha_visita']]
bmx = bm.merge(vis_key, on='visit_id').merge(at, on='patient_id'); bmx.to_csv(lk/'lk_biomarcadores.csv', index=False)
cdx = cd.merge(vis_key, on='visit_id').merge(at, on='patient_id'); cdx.to_csv(lk/'lk_condiciones.csv', index=False)
rsx = rs.merge(at, on='patient_id'); rsx.to_csv(lk/'lk_resultados.csv', index=False)
inf.merge(at[['patient_id', 'programa', 'protocolo']], on='patient_id').to_csv(lk/'lk_informes.csv', index=False)
for n in ['fact_embudo', 'fact_calidad_problemas', 'fact_calidad_validacion', 'dim_genetica_pro', 'fact_evento_previo']:
    pd.read_csv(out/f'{n}.csv').to_csv(lk/f'lk_{n.split("_", 1)[1]}.csv', index=False)
print('looker', {p.name: round(p.stat().st_size / 1e6, 1) for p in sorted(lk.glob('*.csv'))})

# ---- Base SQLite (para DBeaver, Superset, Metabase u otra herramienta que no requiera cuenta)
import sqlite3
dbp = out/'estudio_longevidad.sqlite'
if dbp.exists(): dbp.unlink()
con = sqlite3.connect(dbp)
for p in sorted(out.glob('*.csv')): pd.read_csv(p).to_sql(p.stem, con, index=False)
con.execute('CREATE INDEX ix_visita_pac ON fact_visita(patient_id)'); con.execute('CREATE INDEX ix_bio_visita ON fact_biomarcador(visit_id)'); con.commit(); con.close()
print('sqlite ok', round(dbp.stat().st_size / 1e6, 1), 'MB')

# ---- Data Studio (carga de CSV) lee la coma como separador de miles: dejar PUNTO decimal y redondear
for p in sorted(lk.glob('*.csv')):
    pd.read_csv(p).round(4).to_csv(p, index=False, encoding='utf-8')
print('looker csv con punto decimal')
