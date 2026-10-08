"""
04 · MODELOS Y ANÁLISIS SOBRE LA COHORTE LIMPIA (8.000 pacientes, 0/6/12 meses) — datos 100% sintéticos
  1) Edad biológica por biomarcadores + hábitos (no es un reloj epigenético: no hay metilación)
       Reloj A: predice la edad cronológica (sin referencia)  ·  Reloj B: calibrado con una referencia simulada en el 25% de los pacientes
  2) Genética FIJA (solo programa PRO) vs componente MODIFIABLE de la brecha
  3) 5 scores por dominio + Score de Longevidad (pesos editables) + segmentos + borrador de informe de integración
  4) Longitudinal: ritmo de envejecimiento, respondedores, hábitos y síntomas, señales tempranas, padecimientos
  5) Operación: embudo, tiempos, cobertura de anamnesis
En este entorno se usó scikit-learn; en el tuyo podés cambiar el boosting por XGBoost, sumar SHAP y usar statsmodels MixedLM.
"""
import numpy as np, pandas as pd, json, os, warnings
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV, LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, mean_absolute_error, roc_auc_score
from sklearn.inspection import permutation_importance
warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__)); COH = f'{HERE}/datos/cohorte'; RES = f'{HERE}/resultados'
os.makedirs(RES, exist_ok=True); rng = np.random.default_rng(11)
df = pd.read_csv(f'{COH}/visitas_longitudinal.csv', parse_dates=['fecha_visita'])
pac = pd.read_csv(f'{COH}/pacientes.csv', parse_dates=['fecha_consulta', 'fecha_estudios', 'fecha_integracion'])
evt = pd.read_csv(f'{COH}/eventos_clinicos.csv'); truth = pd.read_csv(f'{COH}/solucion_latentes.csv')
embudo = json.load(open(f'{COH}/embudo.json')); calidad = json.load(open(f'{HERE}/datos/pipeline_salida/calidad_datos.json'))
f1 = lambda x, d=1: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)
df['sexo_m'] = (df.sexo == 'M').astype(int)
df['hito'] = np.where(df.meses_desde_baseline < 1, '0m', np.where(df.meses_desde_baseline < 9, '6m', '12m'))
T = truth.set_index('visit_id'); tr_mod = df.visit_id.map(T.brecha_modificable_real)

# ------------------------------------------------------------------ 1) EDAD BIOLÓGICA
HAB = ['hora_acostarse', 'celular_en_cama', 'sesiones_fuerza_sem', 'min_cardio_sem', 'sedentarismo_h_dia', 'ultraprocesados_sem', 'alcohol_sem', 'dieta_mediterranea_score', 'estres_percibido', 'ansiedad_score', 'calidad_sueno']
CLOCK = ['glucosa', 'hba1c', 'insulina', 'homa_ir', 'trigliceridos', 'grasa_corporal_pct', 'imc', 'alt', 'ast', 'ldl', 'hdl', 'colesterol_total', 'pa_sistolica', 'homocisteina', 'pcr_us', 'drom_ucarr',
         'pic_indice', 'ferritina', 'vitamina_d', 'b12', 'tsh', 'creatinina', 'carga_metales_idx', 'ratio_zn_cu', 'ratio_ca_mg', 'vo2max_ml_kg_min', 'fuerza_agarre_kg', 'masa_magra_kg', 'hrv_rmssd_ms',
         'sueno_horas', 'pasos_dia', 'sexo_m'] + HAB + [c for c in df.columns if c.startswith('oligo_')]
mk_en = lambda: make_pipeline(StandardScaler(), ElasticNetCV(l1_ratio=[.2, .5, .9], cv=3, max_iter=8000))
mk_gb = lambda: HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_depth=3, l2_regularization=1.0, random_state=0)
# Reloj A
X, y, g = df[CLOCK], df.edad_cronologica, df.patient_id
oofA = np.zeros(len(df))
for tr, te in GroupKFold(5).split(X, y, g):
    a = mk_en().fit(X.iloc[tr], y.iloc[tr]); b = mk_gb().fit(X.iloc[tr], y.iloc[tr]); oofA[te] = 0.5 * a.predict(X.iloc[te]) + 0.5 * b.predict(X.iloc[te])
brA = oofA - LinearRegression().fit(y.values.reshape(-1, 1), oofA).predict(y.values.reshape(-1, 1))
corr_A = float(np.corrcoef(brA, tr_mod)[0, 1]); mae_A = float(mean_absolute_error(y, oofA))
# Reloj B: referencia simulada en el 25% de los pacientes
lab_ids = set(np.random.default_rng(5).choice(df.patient_id.unique(), int(0.25 * df.patient_id.nunique()), replace=False))
df['tiene_ref'] = df.patient_id.isin(lab_ids); df['gap_ref'] = np.where(df.tiene_ref, tr_mod + rng.normal(0, 1.2, len(df)), np.nan)
FB = CLOCK + ['edad_cronologica']; lab_df = df[df.tiene_ref]; unl = ~df.tiene_ref.values
oofB = pd.Series(np.nan, index=df.index); app = np.zeros(len(df))
for tr, te in GroupKFold(5).split(lab_df, groups=lab_df.patient_id):
    tri, tei = lab_df.index[tr], lab_df.index[te]
    m1, m2 = mk_en().fit(df.loc[tri, FB], df.loc[tri, 'gap_ref']), mk_gb().fit(df.loc[tri, FB], df.loc[tri, 'gap_ref'])
    fn = lambda idx: 0.5 * m1.predict(df.loc[idx, FB]) + 0.5 * m2.predict(df.loc[idx, FB])
    oofB.loc[tei] = fn(tei); app[unl] += fn(df.index[unl]) / 5
df['brecha_modificable'] = np.where(df.tiene_ref, oofB, app); df['edad_biologica_modificable'] = df.edad_cronologica + df.brecha_modificable
corr_B = float(np.corrcoef(df.brecha_modificable[unl], tr_mod[unl])[0, 1]); mae_B = float(mean_absolute_error(tr_mod[unl], df.brecha_modificable[unl]))
en_f = mk_en().fit(lab_df[FB], lab_df.gap_ref); sc, coef = en_f[0], en_f[1].coef_
gb_f = mk_gb().fit(lab_df[FB], lab_df.gap_ref); ix = rng.choice(len(lab_df), min(800, len(lab_df)), replace=False)
pi = permutation_importance(gb_f, lab_df[FB].iloc[ix], lab_df.gap_ref.iloc[ix], n_repeats=3, random_state=0, scoring='neg_mean_absolute_error')
LBL = {'vo2max_ml_kg_min': 'VO2 máx', 'drom_ucarr': 'D-ROMs', 'pic_indice': 'PIC (placeholder)', 'hba1c': 'HbA1c', 'glucosa': 'Glucosa', 'pcr_us': 'PCR-us', 'carga_metales_idx': 'Carga de metales',
       'fuerza_agarre_kg': 'Fuerza de agarre', 'hrv_rmssd_ms': 'HRV', 'homa_ir': 'HOMA-IR', 'ldl': 'LDL', 'hdl': 'HDL', 'pa_sistolica': 'Presión sistólica', 'grasa_corporal_pct': '% grasa corporal',
       'homocisteina': 'Homocisteína', 'creatinina': 'Creatinina', 'trigliceridos': 'Triglicéridos', 'masa_magra_kg': 'Masa magra', 'sexo_m': 'Sexo', 'ferritina': 'Ferritina', 'vitamina_d': 'Vitamina D',
       'imc': 'IMC', 'insulina': 'Insulina', 'alt': 'ALT', 'ast': 'AST', 'b12': 'B12', 'tsh': 'TSH', 'colesterol_total': 'Colesterol total', 'sueno_horas': 'Sueño (horas)', 'pasos_dia': 'Pasos/día',
       'ratio_zn_cu': 'Zn/Cu', 'ratio_ca_mg': 'Ca/Mg', 'hora_acostarse': 'Hora de acostarse', 'celular_en_cama': 'Celular en la cama', 'sesiones_fuerza_sem': 'Sesiones de fuerza', 'min_cardio_sem': 'Cardio (min/sem)',
       'sedentarismo_h_dia': 'Horas sentado', 'ultraprocesados_sem': 'Ultraprocesados', 'alcohol_sem': 'Alcohol', 'dieta_mediterranea_score': 'Dieta mediterránea', 'estres_percibido': 'Estrés percibido',
       'ansiedad_score': 'Ansiedad', 'calidad_sueno': 'Calidad de sueño'}
lab = lambda c: LBL.get(c, c.replace('oligo_', 'Oligo: ').capitalize())
importancia = [dict(variable=lab(c), valor=round(float(v), 3)) for c, v in sorted([(c, v) for c, v in zip(FB, pi.importances_mean) if c != 'edad_cronologica'], key=lambda t: -t[1])[:12]]
def drivers(row):
    contrib = coef * ((row[FB].values.astype(float) - sc.mean_) / sc.scale_); contrib[FB.index('edad_cronologica')] = 0; o = np.argsort(contrib)
    return ([dict(v=lab(FB[j]), a=round(float(contrib[j]), 2)) for j in o[::-1][:3] if contrib[j] > 0.02], [dict(v=lab(FB[j]), a=round(float(contrib[j]), 2)) for j in o[:3] if contrib[j] < -0.02])

# ------------------------------------------------------------------ 2) GENÉTICA FIJA (solo PRO) vs MODIFICABLE
GEN_W = dict(apoe_e4=0.9, mthfr_tt=0.5, fto=0.35, prs=0.45, centro=-0.6)   # reglas de ejemplo, editables
pro = df.programa == 'PRO'
df['brecha_genetica_fija'] = np.where(pro, GEN_W['apoe_e4'] * df.apoe_e4_carrier + GEN_W['mthfr_tt'] * df.mthfr_tt + GEN_W['fto'] * df.fto_alelos_riesgo + GEN_W['prs'] * df.prs_metabolico + GEN_W['centro'], np.nan)
df['brecha_total_pro'] = df.brecha_modificable + df.brecha_genetica_fija

# ------------------------------------------------------------------ 3) SCORES POR DOMINIO + LONGEVIDAD + SEGMENTOS
DOM = {'Metabolismo': ('score_metabolismo', [('glucosa', 1, 0), ('hba1c', 1, 0), ('homa_ir', 1, 1), ('trigliceridos', 1, 1), ('grasa_corporal_pct', 1, 0), ('imc', 1, 0)]),
       'Inflamación': ('score_inflamacion', [('pcr_us', 1, 1), ('drom_ucarr', 1, 0), ('pic_indice', 1, 0), ('ferritina', 1, 1)]),
       'Cardiovascular': ('score_cardiovascular', [('ldl', 1, 0), ('ratio_tg_hdl', 1, 1), ('hdl', -1, 0), ('pa_sistolica', 1, 0), ('homocisteina', 1, 1)]),
       'Detoxificación': ('score_detoxificacion', [('carga_metales_idx', 1, 1), ('oligo_zinc', -1, 0), ('oligo_magnesio', -1, 0), ('oligo_selenio', -1, 0), ('ratio_zn_cu', -1, 0)]),
       'Rendimiento físico y cognitivo': ('score_rendimiento', [('vo2max_ml_kg_min', -1, 0), ('fuerza_agarre_kg', -1, 0), ('hrv_rmssd_ms', -1, 1), ('pasos_dia', -1, 1), ('sueno_horas', -1, 0), ('claridad_mental', -1, 0)])}
DN = list(DOM); SC = [v[0] for v in DOM.values()]
b0 = df[df.hito == '0m']
for d, (col, vs) in DOM.items():
    zs = []
    for v, s, lg in vs:
        x = np.log(df[v]) if lg else df[v]; bx = np.log(b0[v]) if lg else b0[v]
        zs.append(s * (x - df.sexo.map(bx.groupby(b0.sexo).mean())) / df.sexo.map(bx.groupby(b0.sexo).std()))
    df[col] = np.clip(50 - 15 * np.mean(zs, axis=0), 0, 100)
LONG_W = dict(dominios=0.7, brecha=0.3, pendiente_brecha=5.0)   # score_longevidad = 0.7*promedio(5 dominios) + 0.3*(50 - 5*brecha), recortado a 0-100
df['score_longevidad'] = np.clip(LONG_W['dominios'] * df[SC].mean(axis=1) + LONG_W['brecha'] * np.clip(50 - LONG_W['pendiente_brecha'] * df.brecha_modificable, 0, 100), 0, 100)
ZMAP = dict(zip(SC, ['z_metabolico', 'z_inflamatorio', 'z_cardio', 'z_minerales', 'z_fitness']))
slopes = {}
for col, zc in ZMAP.items():
    zt = df.visit_id.map(T[zc]); slopes[col] = float(np.cov(df[col], zt)[0, 1] / np.var(zt, ddof=1))
Z = StandardScaler().fit(df[df.hito == '0m'][SC]); bs = df[df.hito == '0m'].copy(); Zb = Z.transform(bs[SC])
sil = {k: float(silhouette_score(Zb, KMeans(k, n_init=20, random_state=0).fit_predict(Zb))) for k in range(3, 8)}; K = max(sil, key=sil.get)
km = KMeans(K, n_init=20, random_state=0).fit(Zb); cent = km.cluster_centers_
ROAD = {'Metabolismo': dict(nutricion='Plan metabólico: carga glucémica y distribución de proteínas', entrenamiento='Fuerza 2-3 veces por semana más zona 2', suplementacion='A criterio médico según laboratorio'),
        'Inflamación': dict(nutricion='Patrón antiinflamatorio, menos ultraprocesados', entrenamiento='Actividad regular de intensidad moderada', suplementacion='Antioxidantes según evaluación médica'),
        'Cardiovascular': dict(nutricion='Perfil lipídico y sodio, fibra', entrenamiento='Aeróbico progresivo y fuerza', suplementacion='Revisar homocisteína y lípidos con el médico'),
        'Detoxificación': dict(nutricion='Fuentes dietarias de Zn, Mg y Se', entrenamiento='Mantener actividad general', suplementacion='Minerales según estudio, bajo control médico'),
        'Rendimiento físico y cognitivo': dict(nutricion='Proteína suficiente para masa magra', entrenamiento='Bloque de VO2 máx (intervalos) y fuerza', suplementacion='Sueño y recuperación primero')}
names, roadmap = {}, {}
for c in range(K):
    weak = [DN[j] for j in np.argsort(cent[c]) if cent[c][j] < -0.45][:2]
    if not weak:
        names[c] = 'Perfil óptimo' if cent[c].mean() > 0.3 else 'Perfil balanceado'
        roadmap[names[c]] = dict(nutricion='Mantener hábitos', entrenamiento='Sostener VO2 máx y fuerza', suplementacion='Sin prioridad detectada')
    else:
        names[c] = 'Foco: ' + ' + '.join(w.lower() for w in weak)
        roadmap[names[c]] = {k: ROAD[weak[0]][k] + (f' (y {ROAD[weak[1]][k].lower()})' if len(weak) > 1 else '') for k in ('nutricion', 'entrenamiento', 'suplementacion')}
bs['segmento'] = [names[c] for c in km.labels_]; df['segmento'] = df.patient_id.map(dict(zip(bs.patient_id, bs.segmento)))
P2 = PCA(2, random_state=0).fit_transform(Zb)

COND = {'cond_prediabetes': 'prediabetes', 'cond_resistencia_insulinica': 'resistencia a la insulina', 'cond_dislipidemia': 'dislipidemia', 'cond_presion_elevada': 'presión elevada',
        'cond_deficit_vitamina_d': 'déficit de vitamina D', 'cond_inflamacion_baja_grado': 'inflamación de bajo grado', 'cond_carga_metales_alta': 'carga de metales alta'}
def informe(r):
    """borrador para que el médico revise antes de la consulta de integración (no es una indicación)"""
    prios = [d for d in DN if r[DOM[d][0]] < 45]
    hab = []
    if r.celular_en_cama == 1: hab.append('usa el celular en la cama')
    if r.ultraprocesados_sem >= 8: hab.append(f'{int(r.ultraprocesados_sem)} comidas ultraprocesadas por semana')
    if r.sesiones_fuerza_sem <= 1: hab.append('pocas sesiones de fuerza')
    if r.sedentarismo_h_dia >= 10: hab.append(f'{r.sedentarismo_h_dia:.0f} horas sentado por día')
    if r.estres_percibido >= 7: hab.append('estrés percibido alto')
    if r.calidad_sueno <= 4.5: hab.append('mala calidad de sueño')
    if r.alcohol_sem >= 10: hab.append('consumo de alcohol elevado')
    gen = []
    if r.programa == 'PRO':
        if r.apoe_e4_carrier == 1: gen.append('portador APOE e4: vigilar perfil cardiovascular y sueño')
        if r.mthfr_tt == 1: gen.append('MTHFR TT: revisar homocisteína')
        if r.lct_13910 == 'CC': gen.append('posible intolerancia a lactosa')
        if r.hla_dq2_dq8 == 1: gen.append('predisposición celíaca: confirmar con estudios médicos')
        if r.cyp1a2_cafeina == 'lento': gen.append('metabolizador lento de cafeína')
        if r.vdr_foki == 'ff': gen.append('vigilar vitamina D')
        if r.gstt1 == 'nulo': gen.append('GSTT1 nulo: observar detoxificación')
    cond = [v for k, v in COND.items() if r[k] == 1]
    return dict(prioridades=prios, habitos=hab, genetica=gen, padecimientos=cond, hallazgo=r.hallazgo_principal)

# ------------------------------------------------------------------ 4) LONGITUDINAL
UMBRAL_RESP = -0.5
df = df.sort_values(['patient_id', 'meses_desde_baseline']).reset_index(drop=True)
prev_h = df.groupby('patient_id').homa_ir.shift(1)
df['alerta_metabolica_temprana'] = ((df.homa_ir - prev_h >= 0.4) & (df.glucosa < 100) & (df.hba1c < 5.7)).astype(int)
SYM = ['energia', 'dolor', 'claridad_mental', 'molestias_digestivas']; HB = ['ultraprocesados_sem', 'sesiones_fuerza_sem', 'estres_percibido', 'calidad_sueno', 'celular_en_cama', 'min_cardio_sem', 'dieta_mediterranea_score']
VARS = ['brecha_modificable', 'score_longevidad', 'n_condiciones'] + SC + SYM + HB
w = df.pivot_table(index='patient_id', columns='hito', values=VARS, aggfunc='first')
base = df[df.hito == '0m'].set_index('patient_id')
pt = base[['sexo', 'edad_cronologica', 'programa', 'protocolo', 'adherencia', 'segmento', 'intol_gluten_detectada', 'intol_lactosa_detectada']].copy()
pt['brecha_0'] = w['brecha_modificable']['0m']; pt['longevidad_0'] = w['score_longevidad']['0m']
for v in VARS:
    for h in ('6m', '12m'): pt[f'd_{v}_{h}'] = w[v][h] - w[v]['0m']
for s in SC: pt[s + '_0'] = w[s]['0m']
rit = {}
for pid, gdf in df.groupby('patient_id'):
    t = gdf.meses_desde_baseline.values / 12
    if len(gdf) >= 2 and t.max() - t.min() > 0.3: rit[pid] = np.polyfit(t, gdf.edad_biologica_modificable.values, 1)[0]
pt['ritmo_envejecimiento'] = pd.Series(rit)
pt['resp_6m'] = (pt.d_brecha_modificable_6m <= UMBRAL_RESP).astype(float).where(pt.d_brecha_modificable_6m.notna())
pt['resp_12m'] = (pt.d_brecha_modificable_12m <= UMBRAL_RESP).astype(float).where(pt.d_brecha_modificable_12m.notna())
tb = truth[truth.visit_n == 0].set_index('patient_id'); pt['intol_gluten_real'] = tb.intol_gluten_real; pt['intol_lactosa_real'] = tb.intol_lactosa_real
pt['tratado'] = pt.protocolo != 'Seguimiento estándar'
def ci(s):
    s = s.dropna()
    if len(s) < 2: return None
    m, se = s.mean(), s.std() / np.sqrt(len(s)); return dict(n=int(len(s)), m=round(float(m), 2), lo=round(float(m - 1.96 * se), 2), hi=round(float(m + 1.96 * se), 2))
def rate(s): s = s.dropna(); return dict(n=int(len(s)), r=round(float(s.mean()) * 100, 1)) if len(s) else None
ORDER = ['Seguimiento estándar', 'Nutrición metabólica', 'Suplementación antioxidante', 'Entrenamiento VO2máx + sueño', 'Suplementación y minerales', 'Combinado integral']
by_proto = [dict(protocolo=p, n=int((pt.protocolo == p).sum()), d6=ci(pt[pt.protocolo == p].d_brecha_modificable_6m), d12=ci(pt[pt.protocolo == p].d_brecha_modificable_12m), ritmo=ci(pt[pt.protocolo == p].ritmo_envejecimiento),
                 r6=rate(pt[pt.protocolo == p].resp_6m), r12=rate(pt[pt.protocolo == p].resp_12m), longevidad12=ci(pt[pt.protocolo == p].d_score_longevidad_12m)) for p in ORDER]
by_adh = [dict(adherencia=a, d12=ci(pt[pt.adherencia == a].d_brecha_modificable_12m), ritmo=ci(pt[pt.adherencia == a].ritmo_envejecimiento), r6=rate(pt[pt.adherencia == a].resp_6m), r12=rate(pt[pt.adherencia == a].resp_12m)) for a in ['Alta', 'Media', 'Baja']]
trend = [dict(protocolo=p, pts=[ci(df[(df.protocolo == p) & (df.hito == h)].brecha_modificable) for h in ['0m', '6m', '12m']]) for p in ORDER]
long_trend = {grp: [f1(df[(df.protocolo.eq('Seguimiento estándar') == (grp == 'control')) & (df.hito == h)].score_longevidad.mean()) for h in ['0m', '6m', '12m']] for grp in ('control', 'plan')}
dom_delta = {h: {d: {'plan': f1(pt[pt.tratado][f'd_{DOM[d][0]}_{h}'].mean()), 'control': f1(pt[~pt.tratado][f'd_{DOM[d][0]}_{h}'].mean())} for d in DN} for h in ('6m', '12m')}
habitos = [dict(protocolo=p, **{v: f1(pt[pt.protocolo == p][f'd_{v}_12m'].mean(), 2) for v in HB}) for p in ORDER]
sint = [dict(protocolo=p, **{v: ci(pt[pt.protocolo == p][f'd_{v}_12m']) for v in SYM}) for p in ORDER]
sint_adh = [dict(adherencia=a, **{v: f1(pt[pt.adherencia == a][f'd_{v}_12m'].mean(), 2) for v in SYM}) for a in ['Alta', 'Media', 'Baja']]
def grp_gl(r):
    if r.intol_gluten_real != 1: return None
    return 'Detectada y con plan' if (r.intol_gluten_detectada == 1 and r.tratado) else 'No detectada' if r.intol_gluten_detectada == 0 else 'Detectada, sin plan'
def grp_la(r):
    if r.intol_lactosa_real != 1: return None
    return 'Detectada y con plan' if (r.intol_lactosa_detectada == 1 and r.tratado) else 'No detectada' if r.intol_lactosa_detectada == 0 else 'Detectada, sin plan'
pt['grp_gluten'] = pt.apply(grp_gl, axis=1); pt['grp_lactosa'] = pt.apply(grp_la, axis=1)
hallazgo = dict(gluten=[dict(grupo=g, dolor12=ci(pt[pt.grp_gluten == g].d_dolor_12m), dolor6=ci(pt[pt.grp_gluten == g].d_dolor_6m), n=int((pt.grp_gluten == g).sum())) for g in ['No detectada', 'Detectada y con plan']],
                lactosa=[dict(grupo=g, dig12=ci(pt[pt.grp_lactosa == g].d_molestias_digestivas_12m), dig6=ci(pt[pt.grp_lactosa == g].d_molestias_digestivas_6m), n=int((pt.grp_lactosa == g).sum())) for g in ['No detectada', 'Detectada y con plan']])
# señales tempranas: insulina/HOMA-IR sube con glucosa y HbA1c aún normales -> ¿prediabetes en el control siguiente?
df['pred_next'] = df.groupby('patient_id').cond_prediabetes.shift(-1)
ok = df[(df.glucosa < 100) & (df.hba1c < 5.7) & df.pred_next.notna() & df.homa_ir.sub(prev_h).notna()]
señal = {k: dict(n=int(len(g)), pct=round(float(g.pred_next.mean()) * 100, 1)) for k, g in [('con alerta', ok[ok.alerta_metabolica_temprana == 1]), ('sin alerta', ok[ok.alerta_metabolica_temprana == 0])]}
cond_tab = []
for k, nm in COND.items():
    r0 = df[df.hito == '0m'][k].mean() * 100; row = dict(condicion=nm, baseline=f1(r0))
    for grp, m in (('plan', True), ('control', False)):
        ids = pt[pt.tratado == m].index; d12 = df[(df.hito == '12m') & df.patient_id.isin(ids)]; d0 = df[(df.hito == '0m') & df.patient_id.isin(d12.patient_id)]
        row[grp + '_0'] = f1(d0[k].mean() * 100); row[grp + '_12'] = f1(d12[k].mean() * 100)
    cond_tab.append(row)
ev_n = pac.set_index('patient_id').n_eventos_previos; pt['n_eventos'] = ev_n; pt['n_cond_0'] = base.n_condiciones
ev_tab = [dict(grupo=lab_, n=int(m.sum()), brecha=f1(pt[m].brecha_0.mean(), 2), condiciones=f1(pt[m].n_cond_0.mean(), 2)) for lab_, m in [('0 eventos', pt.n_eventos == 0), ('1 evento', pt.n_eventos == 1), ('2 o más', pt.n_eventos >= 2)]]
# genética fija vs modificable (PRO)
pr = df[(df.programa == 'PRO')]; p0 = pr[pr.hito == '0m']; p12 = pr[pr.hito == '12m']
gen_tab = dict(n_pro=int(p0.patient_id.nunique()), mod0=f1(p0.brecha_modificable.mean(), 2), gen=f1(p0.brecha_genetica_fija.mean(), 2), total0=f1(p0.brecha_total_pro.mean(), 2),
               mod12_plan=f1(p12[p12.protocolo != 'Seguimiento estándar'].brecha_modificable.mean(), 2), gen12_plan=f1(p12[p12.protocolo != 'Seguimiento estándar'].brecha_genetica_fija.mean(), 2),
               mod12_control=f1(p12[p12.protocolo == 'Seguimiento estándar'].brecha_modificable.mean(), 2),
               pct_gen_positiva=f1((p0.brecha_genetica_fija > 0.5).mean() * 100), hist=np.histogram(p0.brecha_genetica_fija, bins=np.arange(-1.5, 3.01, 0.5))[0].tolist(),
               mod_hist=np.histogram(p0.brecha_modificable, bins=np.arange(-1.5, 3.01, 0.5))[0].tolist())
# clasificador de respondedores
FE = ['brecha_0', 'edad_cronologica', 'sexo_m'] + [s + '_0' for s in SC]
cl = pt.dropna(subset=['resp_6m']).copy(); cl['sexo_m'] = (cl.sexo == 'M').astype(int); cl['proto'] = cl.protocolo.map({p: i for i, p in enumerate(ORDER)}); cl['adh_n'] = cl.adherencia.map({'Alta': 2, 'Media': 1, 'Baja': 0})
cl['estres0'] = base.estres_percibido; cl['sueno0'] = base.calidad_sueno; FE += ['estres0', 'sueno0']
auc = {}
for nm, cols in [('Solo datos de baseline y protocolo', FE + ['proto']), ('Con adherencia (señal temprana)', FE + ['proto', 'adh_n'])]:
    pp = cross_val_predict(HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_depth=3, random_state=0), cl[cols], cl.resp_6m.astype(int), cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]
    auc[nm] = round(float(roc_auc_score(cl.resp_6m.astype(int), pp)), 3)

# ------------------------------------------------------------------ 5) OPERACIÓN
pac['d_c_e'] = (pac.fecha_estudios - pac.fecha_consulta).dt.days; pac['d_e_i'] = (pac.fecha_integracion - pac.fecha_estudios).dt.days
nb = pac.groupby('programa').size()
def retencion(h): return {pg: f1(100 * pt[(pt.programa == pg)][f'd_brecha_modificable_{h}'].notna().mean()) for pg in ('BASE', 'PRO')}
oper = dict(embudo=embudo, n_programa={k: int(v) for k, v in nb.items()}, retencion_6m=retencion('6m'), retencion_12m=retencion('12m'),
            med_consulta_estudios=f1(pac.d_c_e.median(), 0), med_estudios_integracion=f1(pac.d_e_i.median(), 0), hist_e_i=np.histogram(pac.d_e_i, bins=np.arange(5, 27, 3))[0].tolist(),
            cobertura_media=f1(pac.cobertura_anamnesis_pct.mean()), cobertura_lt80=f1((pac.cobertura_anamnesis_pct < 80).mean() * 100),
            retencion_adh={a: dict(r6=f1(100 * pt[pt.adherencia == a].d_brecha_modificable_6m.notna().mean()), r12=f1(100 * pt[pt.adherencia == a].d_brecha_modificable_12m.notna().mean())) for a in ['Alta', 'Media', 'Baja']})

# ------------------------------------------------------------------ SALIDAS
df.drop(columns=['sexo_m']).to_csv(f'{RES}/visitas_con_modelos.csv', index=False); pt.reset_index().to_csv(f'{RES}/pacientes_resumen_longitudinal.csv', index=False)
inf = bs.apply(lambda r: pd.Series(informe(r)), axis=1); inf['patient_id'] = bs.patient_id.values
pd.DataFrame(dict(patient_id=inf.patient_id, segmento=bs.segmento.values, prioridades=inf.prioridades.map(', '.join), habitos_a_conversar=inf.habitos.map('; '.join), genetica_para_evaluar=inf.genetica.map('; '.join),
                  padecimientos_detectados=inf.padecimientos.map(', '.join), hallazgo=inf.hallazgo)).to_csv(f'{RES}/informe_integracion_borrador.csv', index=False)
kpi = dict(pacientes=int(df.patient_id.nunique()), visitas=int(len(df)), pro=int((base.programa == 'PRO').sum()), edad_media=f1(base.edad_cronologica.mean()), brecha_media=f1(base.brecha_modificable.mean(), 2),
           pct_acelerados=f1((base.brecha_modificable >= 2).mean() * 100), ret6=f1(100 * pt.d_brecha_modificable_6m.notna().mean(), 0), ret12=f1(100 * pt.d_brecha_modificable_12m.notna().mean(), 0),
           resp6_plan=rate(pt[pt.tratado].resp_6m), resp6_control=rate(pt[~pt.tratado].resp_6m), d12_plan=ci(pt[pt.tratado].d_brecha_modificable_12m), d12_control=ci(pt[~pt.tratado].d_brecha_modificable_12m),
           long_plan=ci(pt[pt.tratado].d_score_longevidad_12m), long_control=ci(pt[~pt.tratado].d_score_longevidad_12m), n_cond_0=f1(base.n_condiciones.mean(), 2),
           cond_plan_12=ci(pt[pt.tratado].d_n_condiciones_12m), cond_control_12=ci(pt[~pt.tratado].d_n_condiciones_12m))
hist = {s: np.histogram(base[base.sexo == s].brecha_modificable, bins=np.arange(-10, 10.1, 1.0))[0].tolist() for s in ['F', 'M']}
seg_tab = sorted([dict(nombre=nm, n=int((bs.segmento == nm).sum()), scores={d: f1(bs[bs.segmento == nm][DOM[d][0]].mean(), 0) for d in DN}, brecha=f1(bs[bs.segmento == nm].brecha_modificable.mean()), roadmap=roadmap[nm],
                       pct_pro=f1((bs[bs.segmento == nm].programa == 'PRO').mean() * 100, 0)) for nm in names.values()], key=lambda r: -r['n'])
sm = bs.sample(450, random_state=1)
full = df.groupby('patient_id').filter(lambda g: len(g) == 3); ids = []
for p in ORDER:
    for pg in ('PRO', 'BASE'): ids += list(full[(full.protocolo == p) & (full.programa == pg) & (full.hito == '0m')].patient_id.sample(2, random_state=3))
pats = []
for pid in ids:
    g = df[df.patient_id == pid].sort_values('meses_desde_baseline'); r0 = g.iloc[0]; up, dn_ = drivers(r0); ip = informe(bs[bs.patient_id == pid].iloc[0])
    evs = [f'{e.tipo_evento} ({e.anio})' for e in evt[evt.patient_id == pid].itertuples()]
    fam = [k.replace('fam_', '').replace('neurodegenerativa', 'neurodegenerativa') for k in ['fam_cardiovascular', 'fam_diabetes', 'fam_cancer', 'fam_neurodegenerativa'] if r0[k] == 1]
    pats.append(dict(id=pid, sexo=r0.sexo, edad=float(r0.edad_cronologica), programa=r0.programa, protocolo=r0.protocolo, adherencia=r0.adherencia, segmento=r0.segmento, hallazgo=r0.hallazgo_principal,
                     eventos=evs, familia=fam, intol=[x for x, c in (('gluten', r0.intol_gluten_detectada), ('lactosa', r0.intol_lactosa_detectada)) if c == 1],
                     genetica=None if r0.programa != 'PRO' else dict(apoe=r0.apoe, mthfr=r0.mthfr_c677t, fto=int(r0.fto_alelos_riesgo), ace=r0.ace_id, lct=r0.lct_13910, hla=int(r0.hla_dq2_dq8), vdr=r0.vdr_foki, cyp=r0.cyp1a2_cafeina, gstt1=r0.gstt1),
                     gen=f1(r0.brecha_genetica_fija, 2) if r0.programa == 'PRO' else None, up=up, dn=dn_, ritmo=f1(pt.loc[pid, 'ritmo_envejecimiento'], 2), informe=ip,
                     base=dict(scores={d: f1(r0[DOM[d][0]], 1) for d in DN}, brecha=f1(r0.brecha_modificable, 2), ult=int(r0.ultraprocesados_sem), fuerza=int(r0.sesiones_fuerza_sem), estres=f1(r0.estres_percibido), sueno=f1(r0.calidad_sueno), cron=float(r0.edad_cronologica)),
                     visitas=[dict(mes=float(v.meses_desde_baseline), bio=f1(v.edad_biologica_modificable), cron=float(v.edad_cronologica), brecha=f1(v.brecha_modificable), longevidad=f1(v.score_longevidad, 0), scores={d: f1(v[DOM[d][0]], 0) for d in DN},
                                   drom=float(v.drom_ucarr), pic=float(v.pic_indice), pcr=float(v.pcr_us), glu=float(v.glucosa), ins=float(v.insulina), homa=float(v.homa_ir), vo2=float(v.vo2max_ml_kg_min), metales=float(v.carga_metales_idx), ldl=float(v.ldl),
                                   celu=int(v.celular_en_cama), ult=int(v.ultraprocesados_sem), fuerza=int(v.sesiones_fuerza_sem), estres=float(v.estres_percibido), ansiedad=float(v.ansiedad_score), sueno_cal=float(v.calidad_sueno),
                                   energia=float(v.energia), dolor=float(v.dolor), claridad=float(v.claridad_mental), digest=float(v.molestias_digestivas), alerta=int(v.alerta_metabolica_temprana),
                                   cond=[nm for k, nm in COND.items() if v[k] == 1]) for _, v in g.iterrows()]))
sim = dict(effect={'Nutrición metabólica': (-0.55, -0.25, -0.25, 0.00, 0.10), 'Suplementación antioxidante': (-0.05, -0.55, -0.10, -0.10, 0.00), 'Entrenamiento VO2máx + sueño': (-0.30, -0.20, -0.30, 0.00, 0.60),
                   'Suplementación y minerales': (0.00, -0.15, -0.05, -0.45, 0.00), 'Combinado integral': (-0.45, -0.40, -0.40, -0.20, 0.40), 'Seguimiento estándar': (0, 0, 0, 0, 0)},
           habw={'Nutrición metabólica': (1.0, 0.2, 0.2), 'Suplementación antioxidante': (0.3, 0.1, 0.2), 'Entrenamiento VO2máx + sueño': (0.2, 1.0, 1.0), 'Suplementación y minerales': (0.3, 0.1, 0.1), 'Combinado integral': (0.9, 0.9, 0.9), 'Seguimiento estándar': (0, 0, 0)},
           gapw=(0.30, 0.25, 0.25, 0.10, -0.10), gapk=3.2, drift=dict(normal=0.03, acelerado=0.16), slopes=[round(slopes[c], 2) for c in SC], long_w=LONG_W, ramp_tau=5)
out = dict(kpi=kpi, relojes=dict(A=dict(desc='Predice la edad cronológica', mae_edad=f1(mae_A, 2), corr_brecha=f1(corr_A, 2)), B=dict(desc='Calibrado con referencia simulada en 25% de pacientes', n_ref=len(lab_ids), corr_no_vistos=f1(corr_B, 2), mae_no_vistos=f1(mae_B, 2))),
           importancia=importancia, silhouette={str(k): round(v, 3) for k, v in sil.items()}, K=K, scatter=[dict(c=float(r.edad_cronologica), b=f1(r.edad_biologica_modificable)) for _, r in sm.iterrows()], hist=hist, segmentos=seg_tab,
           pca=[dict(x=f1(P2[i, 0], 2), y=f1(P2[i, 1], 2), c=bs.segmento.iloc[i]) for i in rng.choice(len(bs), 500, replace=False)], proto=by_proto, adh=by_adh, trend=trend, long_trend=long_trend, dom_delta=dom_delta, habitos=habitos,
           sintomas=sint, sintomas_adh=sint_adh, hallazgo=hallazgo, señal=señal, condiciones=cond_tab, eventos=ev_tab, gen=gen_tab, auc=auc, oper=oper, calidad=calidad, pacientes=pats, dominios=DN, simulador=sim, gen_w=GEN_W)
json.dump(out, open(f'{RES}/dashboard_data.json', 'w'), ensure_ascii=False, separators=(',', ':'), default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print(json.dumps(dict(relojes=out['relojes'], K=K, sil=out['silhouette'], auc=auc, kpi=kpi, señal=señal, gen=dict((k, v) for k, v in gen_tab.items() if 'hist' not in k)), ensure_ascii=False, indent=1, default=str))
print('segmentos:', [(s['nombre'], s['n'], s['pct_pro']) for s in seg_tab])
for p in by_proto: print(p['protocolo'], p['n'], p['d12'] and p['d12']['m'], p['ritmo'] and p['ritmo']['m'], p['r6'] and p['r6']['r'])
print('hallazgo gluten:', hallazgo['gluten']); print('hallazgo lactosa:', hallazgo['lactosa']); print('long_trend', long_trend)
print('habitos', habitos[0], habitos[-1]); print('tamaño json KB:', os.path.getsize(f'{RES}/dashboard_data.json') // 1024)
