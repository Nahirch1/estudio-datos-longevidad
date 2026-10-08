"""
03 · PIPELINE DE LIMPIEZA: de archivos sueltos a una tabla longitudinal confiable
Lee las fuentes crudas (Excel, PDFs, formularios con texto libre), resuelve identidad (DNI y, si falta, nombre + fecha),
normaliza fechas, decimales y unidades, descarta duplicados y arma una fila por visita.
Luego se valida contra la cohorte limpia (la "verdad" del simulador) y se guarda un informe de calidad.
Salida: datos/pipeline_salida/visitas_unificadas.csv y calidad_datos.json
"""
import pandas as pd, numpy as np, re, json, os, glob, unicodedata, difflib
from collections import Counter
from datetime import datetime
import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = f'{HERE}/datos/fuentes_crudas'; COH = f'{HERE}/datos/cohorte'; OUT = f'{HERE}/datos/pipeline_salida'
os.makedirs(OUT, exist_ok=True)
stats, ex = Counter(), {}
noacc = lambda s: ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')
isna = lambda x: x is None or (not isinstance(x, str) and pd.isna(x))
def example(key, origen, limpio):
    ex.setdefault(key, dict(origen=origen, limpio=limpio))

# ------------------------------------------------------------------ parsers básicos
def parse_dni(x):
    if isna(x) or (isinstance(x, str) and not x.strip()): return None
    if isinstance(x, (int, float, np.integer, np.floating)):
        stats['dni_formatos_distintos'] += 0; return str(int(x))
    s = str(x); d = re.sub(r'\D', '', s)
    if s.strip() != d:
        stats['dni_formatos_distintos'] += 1; example('dni', s, d)
    return d or None

def parse_date(x):
    if isna(x): return pd.NaT
    if isinstance(x, (datetime, pd.Timestamp)): return pd.Timestamp(x).normalize()
    s = str(x).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            d = datetime.strptime(s, fmt); stats['fechas_como_texto'] += 1
            if fmt != '%Y-%m-%d':
                a, b = s.split('/')[:2]
                if int(a) <= 12 and int(b) <= 12: stats['fechas_ambiguas_dia_mes'] += 1; example('fecha', s, d.strftime('%Y-%m-%d') + ' (se asume día/mes)')
            return pd.Timestamp(d)
        except ValueError: pass
    return pd.NaT

MISSING = {'pendiente', 'n/r', 'nr', 'n/d', '-', '', 'nan', 'none'}
def parse_num(x):
    """devuelve (valor, censurado)"""
    if isna(x): return np.nan, False
    if isinstance(x, (int, float, np.integer, np.floating)): return float(x), False
    s = str(x).strip(); low = noacc(s).lower()
    if low in MISSING: stats['valores_pendientes_o_faltantes'] += 1; return np.nan, False
    cens = s.startswith('<')
    if cens: stats['valores_censurados'] += 1; s = s[1:]
    s = re.sub(r'/10$', '', s.strip()); s = re.sub(r'[^\d,\.\-]', '', s.replace(' ', ''))
    if ',' in s: stats['decimales_con_coma'] += 1; s = s.replace(',', '.')
    try: return float(s), cens
    except ValueError: return np.nan, False

def toks(s): return [t for t in re.sub(r'[^a-z\s]', ' ', noacc(s).lower()).split() if t]

# ------------------------------------------------------------------ 1) maestro de pacientes (registro, con duplicados)
recs = []
r25 = pd.read_excel(f'{RAW}/01_registro_pacientes.xlsx', sheet_name='Pacientes 2025', dtype=object)
r26 = pd.read_excel(f'{RAW}/01_registro_pacientes.xlsx', sheet_name='Pacientes 2026', dtype=object)
for r in r25.itertuples(index=False):
    recs.append(dict(dni=parse_dni(r[0]), name=f'{r[1]} {r[2]}', nac=parse_date(r[3]), sexo=r[4], loc=r[5], prog=r[6], origen=1))
for r in r26.itertuples(index=False):
    recs.append(dict(dni=parse_dni(r[0]), name=str(r[1]), nac=parse_date(r[2]), sexo=r[3], loc=r[4], prog=r[5], origen=2))
reg = pd.DataFrame(recs).dropna(subset=['dni']).sort_values('origen')
stats['filas_registro'] = len(reg); stats['pacientes_duplicados_fusionados'] = len(reg) - reg.dni.nunique()
reg = reg.drop_duplicates('dni', keep='first')
def sexo_n(s):
    if isna(s): return None
    s = noacc(str(s)).lower().strip()
    return 'F' if s in ('f', 'femenino', 'fem', 'mujer') else 'M' if s in ('m', 'masculino', 'masc', 'hombre') else None
master = {}
for r in reg.itertuples():
    master[r.dni] = dict(dni=r.dni, nac=r.nac, sexo=sexo_n(r.sexo), localidad=r.loc, programa='PRO' if 'PRO' in str(r.prog).upper() else 'BASE',
                         toks=set(toks(r.name)), key=' '.join(sorted(toks(r.name))))
master_list = list(master.values())

# ------------------------------------------------------------------ 2) agenda: define las visitas
ag = pd.read_excel(f'{RAW}/02_agenda_consultas.xlsx', dtype=object)
ag.columns = ['fecha', 'dni', 'paciente', 'tipo', 'prof', 'pa', 'estado', 'f_est', 'f_int', 'notas']
ag['dni'] = ag.dni.map(parse_dni); ag['fecha'] = ag.fecha.map(parse_date)
stats['filas_agenda'] = len(ag); stats['turnos_ausentes_excluidos'] = int((ag.estado.map(lambda s: noacc(str(s)).lower()) != 'asistio').sum())
ag = ag[ag.estado.map(lambda s: noacc(str(s)).lower()) == 'asistio'].drop_duplicates(['dni', 'fecha']).sort_values(['dni', 'fecha']).reset_index(drop=True)
ag['pa_sistolica'] = ag.pa.map(lambda s: float(re.findall(r'\d+', str(s))[0]) if not isna(s) else np.nan)
ag['fecha_estudios'] = ag.f_est.map(parse_date); ag['fecha_integracion'] = ag.f_int.map(parse_date)
vdates = ag.groupby('dni').fecha.apply(list).to_dict()

def assign_visit(dni, fecha, tol=7):
    if dni is None or pd.isna(fecha) or dni not in vdates: return None
    best = min(vdates[dni], key=lambda d: abs((d - fecha).days))
    return best if abs((best - fecha).days) <= tol else None

_cache = {}
def match_name(s, fecha):
    """identifica al paciente por nombre cuando falta el DNI (tolera orden, tildes, iniciales y errores de tipeo)"""
    if isna(s): return None
    key = (str(s), fecha)
    if key in _cache: return _cache[key]
    t = toks(str(s)); init = [x for x in t if len(x) == 1]; full = [x for x in t if len(x) > 1]; c = []
    for m in master_list:
        if init:
            ok = all(any(w == f or difflib.SequenceMatcher(None, w, f).ratio() >= .85 for w in m['toks']) for f in full) and any(w.startswith(i) for i in init for w in m['toks'])
            sc = .9 if ok else 0
        else: sc = difflib.SequenceMatcher(None, ' '.join(sorted(t)), m['key']).ratio()
        if sc >= .85: c.append((sc, m['dni']))
    res = None
    if c:
        near = [x for x in c if assign_visit(x[1], fecha, 5) is not None]
        res = max(near or c)[1]
        if init: stats['nombres_con_inicial_resueltos'] += 1; example('nombre_inicial', str(s), 'paciente identificado por apellido + inicial + fecha')
    _cache[key] = res
    return res

# ------------------------------------------------------------------ 3) laboratorio (3 formatos: largo A, ancho B, PDF)
def canon_analyte(n):
    n = noacc(n).lower()
    for pat, k in [(r'hba1c|hemoglobina glic|hb glic', 'hba1c'), (r'glucemia|glucosa', 'glucosa'), (r'insulina', 'insulina'), (r'colesterol total', 'colesterol_total'), (r'hdl', 'hdl'),
                   (r'ldl', 'ldl'), (r'trigliceridos', 'trigliceridos'), (r'pcr|proteina c reactiva', 'pcr_us'), (r'homocisteina', 'homocisteina'), (r'vitamina d|25 oh', 'vitamina_d'),
                   (r'b12', 'b12'), (r'\btsh\b', 'tsh'), (r'ferritina', 'ferritina'), (r'creatinina', 'creatinina'), (r'tgp|\balt\b', 'alt'), (r'tgo|\bast\b', 'ast')]:
        if re.search(pat, n): return k
    return None
def convert(k, v, unit, raw):
    u = noacc(str(unit)).lower() if not isna(unit) else ''
    if k == 'glucosa' and 'mmol' in u: stats['conversiones_unidad_glucosa'] += 1; example('unidad', raw, f'{round(v * 18.016)} mg/dL'); return v * 18.016
    if k == 'pcr_us' and 'mg/dl' in u: stats['conversiones_unidad_pcr'] += 1; return v * 10
    if k == 'vitamina_d' and 'nmol' in u: stats['conversiones_unidad_vitD'] += 1; return v / 2.496
    return v
LAB_ORDER = ['glucosa', 'hba1c', 'insulina', 'colesterol_total', 'hdl', 'ldl', 'trigliceridos', 'pcr_us', 'homocisteina', 'vitamina_d', 'b12', 'tsh', 'ferritina', 'creatinina', 'alt', 'ast']
lab = []   # (dni, fecha, analito, valor, censurado, fuente)
for f in sorted(glob.glob(f'{RAW}/03_laboratorio_proveedorA_*.xlsx')):
    d = pd.read_excel(f, header=3, dtype=object); d.columns = ['fecha', 'dni', 'paciente', 'det', 'res', 'unidad', 'ref']
    d = d.dropna(subset=['det', 'dni'])
    n0 = len(d); d['_k'] = d.fecha.astype(str) + d.dni.astype(str) + d.det.astype(str) + d.res.astype(str); d = d.drop_duplicates('_k')
    stats['filas_duplicadas_eliminadas'] += n0 - len(d); stats['filas_laboratorio_A'] += len(d)
    for r in d.itertuples():
        k = canon_analyte(r.det)
        if not k: stats['determinaciones_no_reconocidas'] += 1; continue
        v, cens = parse_num(r.res)
        if cens: example('censurado', f'{r.det} {r.res} {r.unidad}', f'{k} = {v} (marcado como censurado)')
        if not np.isnan(v): v = convert(k, v, r.unidad, f'{r.det} {r.res} {r.unidad}')
        lab.append((parse_dni(r.dni), parse_date(r.fecha), k, v, cens, 'A'))
d = pd.read_excel(f'{RAW}/03_laboratorio_proveedorB_2026.xlsx', header=2, dtype=object)
stats['filas_laboratorio_B'] = len(d)
for r in d.itertuples(index=False):
    for j, k in enumerate(LAB_ORDER):
        v, cens = parse_num(r[4 + j]); lab.append((parse_dni(r[2]), parse_date(r[3]), k, v, cens, 'B'))
PDFN = [('Hemoglobina glicosilada (HbA1c)', 'hba1c'), ('Vitamina D (25-OH)', 'vitamina_d'), ('Glucemia', 'glucosa'), ('Insulina basal', 'insulina'), ('Colesterol total', 'colesterol_total'),
        ('HDL colesterol', 'hdl'), ('LDL colesterol', 'ldl'), ('Triglicéridos', 'trigliceridos'), ('PCR ultrasensible', 'pcr_us'), ('Homocisteína', 'homocisteina'), ('Vitamina B12', 'b12'),
        ('TSH', 'tsh'), ('Ferritina', 'ferritina'), ('Creatinina', 'creatinina'), ('TGP (ALT)', 'alt'), ('TGO (AST)', 'ast')]
for f in sorted(glob.glob(f'{RAW}/pdfs_laboratorio/*.pdf')):
    with pdfplumber.open(f) as pdf: txt = '\n'.join((p.extract_text() or '') for p in pdf.pages)
    dni = parse_dni(re.search(r'DNI:\s*([\d\.]+)', txt).group(1)); fe = parse_date(re.search(r'extracción:\s*(\d{2}/\d{2}/\d{4})', txt).group(1)); stats['pdfs_leidos'] += 1
    for line in txt.split('\n'):
        for nm, k in PDFN:
            if line.startswith(nm):
                t = line[len(nm):].split()
                if not t: break
                v, cens = parse_num(t[0]); unit = t[1] if len(t) > 1 and v == v else ''
                if not np.isnan(v): v = convert(k, v, unit, f'{nm} {t[0]} {unit}')
                lab.append((dni, fe, k, v, cens, 'PDF')); stats['determinaciones_desde_pdf'] += 1
                if k == 'vitamina_d' and not np.isnan(v): example('pdf', f'{os.path.basename(f)}: "{line.strip()}"', f'vitamina_d = {round(v, 1)} ng/mL')
                break
L = pd.DataFrame(lab, columns=['dni', 'fecha', 'k', 'v', 'cens', 'src'])
L['visita'] = [assign_visit(a, b) for a, b in zip(L.dni, L.fecha)]
stats['determinaciones_sin_visita'] = int(L.visita.isna().sum())
L = L.dropna(subset=['visita']).drop_duplicates(['dni', 'visita', 'k'])
labw = L.pivot(index=['dni', 'visita'], columns='k', values='v')
labc = L[L.cens].pivot(index=['dni', 'visita'], columns='k', values='cens').add_suffix('_censurado')
srcs = L.groupby(['dni', 'visita']).src.first().rename('fuente_laboratorio')

# ------------------------------------------------------------------ 4) Oligoscan (una hoja por mes) y D-ROMs/PIC (a mano, sin DNI)
OL = ['Calcio', 'Magnesio', 'Sodio', 'Potasio', 'Zinc', 'Cobre', 'Hierro', 'Selenio', 'Manganeso', 'Mercurio', 'Plomo', 'Cadmio', 'Aluminio', 'Arsénico', 'Níquel']
SYM = ['Ca', 'Mg', 'Na', 'K', 'Zn', 'Cu', 'Fe', 'Se', 'Mn', 'Hg', 'Pb', 'Cd', 'Al', 'As', 'Ni']
omap = {noacc(n).lower(): 'oligo_' + noacc(n).lower() for n in OL}; omap.update({s.lower(): 'oligo_' + noacc(n).lower() for s, n in zip(SYM, OL)})
orows = []
sheets = pd.read_excel(f'{RAW}/04_oligoscan_exportaciones.xlsx', sheet_name=None, header=2, dtype=object); stats['hojas_oligoscan'] = len(sheets)
for sh, d in sheets.items():
    d = d.rename(columns={c: omap.get(noacc(str(c)).lower(), c) for c in d.columns}); d = d[d.iloc[:, 0].astype(str) != 'Ref. mín - máx']
    for r in d.to_dict('records'):
        fe = parse_date(r[d.columns[0]]); dni = parse_dni(r['DNI'])
        if dni is None:
            dni = match_name(r['Paciente'], fe); stats['oligoscan_filas_sin_dni_resueltas_por_nombre'] += int(dni is not None)
            if dni: example('nombre_sin_dni', f'Oligoscan: "{r["Paciente"]}" (sin DNI)', 'paciente identificado por nombre + fecha de estudio')
        vis_ = assign_visit(dni, fe)
        if vis_ is None: stats['oligoscan_filas_sin_asignar'] += 1; continue
        orows.append(dict(dni=dni, visita=vis_, **{c: parse_num(r[c])[0] for c in omap.values() if c in r}))
O = pd.DataFrame(orows).drop_duplicates(['dni', 'visita']).set_index(['dni', 'visita']) if orows else pd.DataFrame()
drows = []
for sh, cols in [('Registro 2025', ['fecha', 'pac', 'drom', 'pic', 'obs']), ('Registro 2026', ['fecha', 'pac', 'drom', 'pic', 'nivel', 'obs'])]:
    d = pd.read_excel(f'{RAW}/05_drom_pic_registro_manual.xlsx', sheet_name=sh, dtype=object); d.columns = cols
    for r in d.itertuples():
        fe = parse_date(r.fecha); dni = match_name(r.pac, fe); vis_ = assign_visit(dni, fe)
        if vis_ is None: stats['drom_pic_filas_sin_asignar'] += 1; continue
        stats['drom_pic_filas_identificadas_por_nombre'] += 1
        drows.append(dict(dni=dni, visita=vis_, drom_ucarr=parse_num(r.drom)[0], pic_indice=parse_num(r.pic)[0]))
example('nombre_sin_dni_drom', 'D-ROMs/PIC: registro manual solo con nombre (ej. "Pérez, J.")', 'cada fila se asigna a un paciente y a una visita por nombre + fecha')
D = pd.DataFrame(drows).drop_duplicates(['dni', 'visita']).set_index(['dni', 'visita'])

# ------------------------------------------------------------------ 5) ADN Test (solo PRO)
adn = pd.read_excel(f'{RAW}/06_adn_test_PRO.xlsx', header=2, dtype=object); adn.columns = ['fecha', 'dni', 'paciente', 'apoe', 'mthfr', 'fto', 'ace', 'lct', 'hla', 'vdr', 'cyp', 'gstt1', 'obs']
def let(s): return re.sub(r'[^A-Za-z]', '', str(s))
FTOC = {'TT': 0, 'AT': 1, 'TA': 1, 'AA': 2}
arows = {}
for r in adn.itertuples():
    dni = parse_dni(r.dni)
    if dni is None: continue
    ap = sorted(re.findall(r'e[234]', str(r.apoe).lower()))
    arows[dni] = dict(apoe='/'.join(ap), apoe_e4_carrier=int('e4' in ap), mthfr_c677t=let(r.mthfr).upper(), ace_id=let(r.ace).upper(), lct_13910=let(r.lct).upper(),
                      fto_alelos_riesgo=FTOC.get(let(r.fto).upper()), hla_dq2_dq8=int(noacc(str(r.hla)).lower() in ('positivo', '+')),
                      vdr_foki='Ff' if let(r.vdr).lower() == 'ff' and let(r.vdr) not in ('FF', 'ff') else let(r.vdr), cyp1a2_cafeina='rápido' if 'rapid' in noacc(str(r.cyp)).lower() else 'lento',
                      gstt1='nulo' if 'nulo' in str(r.gstt1).lower() else 'presente')
    arows[dni]['mthfr_tt'] = int(arows[dni]['mthfr_c677t'] == 'TT')
stats['pacientes_con_adn'] = len(arows)

# ------------------------------------------------------------------ 6) anamnesis (formularios con texto libre)
def parse_hora(s):
    if isna(s): return np.nan
    s = str(s).strip().lower()
    m = re.match(r'^(\d{1,2})(?::|h)(\d{2})\s*(am|pm)?$', s)
    if not m: return np.nan
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'pm': h = h % 12 + 12
    elif ap == 'am': h = h % 12
    if h < 12: h += 24
    return round(h + mi / 60, 2)
def kw(txt, pat): return int(bool(re.search(pat, noacc(str(txt)).lower())))
EVT = [('cirug', 'ortop', 'cirugía ortopédica'), ('cirug', 'abdom', 'cirugía abdominal'), ('cirug', 'cardio', 'cirugía cardiovascular'), ('cirug', 'vesic', 'cirugía de vesícula'),
       ('internac', 'respir', 'internación respiratoria'), ('internac', 'infecc', 'internación por infección'), ('diagn', 'hipertens', 'diagnóstico de hipertensión'), ('diagn', 'diabetes', 'diagnóstico de diabetes tipo 2')]
an = pd.read_excel(f'{RAW}/07_anamnesis_formularios.xlsx', dtype=object)
an.columns = ['fecha', 'dni', 'paciente', 'hora', 'celu', 'fuerza', 'cardio', 'sed', 'ultra', 'alc', 'dieta', 'tabaco', 'estres', 'ansi', 'sueno', 'energia', 'dolor', 'claridad', 'digest', 'fam', 'intol', 'eventos']
an['dni'] = an.dni.map(parse_dni); an['fecha'] = an.fecha.map(parse_date); stats['formularios_anamnesis'] = len(an)
arow, estat = [], {}
for r in an.itertuples():
    vis_ = assign_visit(r.dni, r.fecha, 3)
    if vis_ is None: stats['anamnesis_sin_visita'] += 1; continue
    tb = noacc(str(r.tabaco)).lower()
    arow.append(dict(dni=r.dni, visita=vis_, hora_acostarse=parse_hora(r.hora), celular_en_cama=int(noacc(str(r.celu)).lower() in ('si', 'a veces')),
                     sesiones_fuerza_sem=parse_num(r.fuerza)[0], min_cardio_sem=parse_num(r.cardio)[0], sedentarismo_h_dia=parse_num(r.sed)[0], ultraprocesados_sem=parse_num(r.ultra)[0],
                     alcohol_sem=parse_num(r.alc)[0], dieta_mediterranea_score=parse_num(r.dieta)[0], tabaquismo='Nunca' if ('nunca' in tb or 'no fuma' in tb) else 'Ex' if tb.startswith('ex') else 'Actual',
                     estres_percibido=parse_num(r.estres)[0], ansiedad_score=parse_num(r.ansi)[0], calidad_sueno=parse_num(r.sueno)[0], energia=parse_num(r.energia)[0],
                     dolor=parse_num(r.dolor)[0], claridad_mental=parse_num(r.claridad)[0], molestias_digestivas=parse_num(r.digest)[0]))
    if not isna(r.fam) or not isna(r.eventos) or not isna(r.intol):   # texto libre del primer formulario
        nf = noacc(str(r.fam)).lower()
        fam = dict(fam_cardiovascular=kw(nf, r'infarto|acv|cardiop|hipertens'), fam_diabetes=kw(nf, r'diabet|dbt'), fam_cancer=kw(nf, r'cancer|tumor'), fam_neurodegenerativa=kw(nf, r'alzheimer|parkinson|demencia'))
        if sum(fam.values()) >= 2: example('anamnesis_texto', f'Antecedentes familiares: "{r.fam}"', ', '.join(f'{k}=1' for k, v in fam.items() if v))
        ev_txt = '' if isna(r.eventos) else str(r.eventos); evs = []
        if not re.search(r'sin antecedentes|no refiere', noacc(ev_txt).lower()) and ev_txt.strip():
            for part in re.split(r'\s*;\s*|\s+/\s+', ev_txt):
                pn = noacc(part).lower(); typ = next((n for a, b, n in EVT if a in pn and b in pn), None)
                evs.append((typ, (re.search(r'(19|20)\d{2}', pn) or [None])[0]))
        estat[r.dni] = dict(**fam, intol_gluten_detectada=kw(r.intol, r'gluten|trigo'), intol_lactosa_detectada=kw(r.intol, r'lactosa|lacteos'), n_eventos_previos=len(evs), _eventos=evs)
stats['textos_libres_interpretados'] = len(estat)
A = pd.DataFrame(arow).drop_duplicates(['dni', 'visita']).set_index(['dni', 'visita'])

# ------------------------------------------------------------------ 7) protocolos
PROT = ['Nutrición metabólica', 'Suplementación antioxidante', 'Entrenamiento VO2máx + sueño', 'Suplementación y minerales', 'Combinado integral', 'Seguimiento estándar']
HALL = ['intolerancia al gluten', 'intolerancia a la lactosa', 'déficit de vitamina D', 'resistencia a la insulina', 'carga de metales elevada']
def adh_n(s):
    if isna(s): return None
    t = noacc(str(s)).lower().strip()
    if t.endswith('%'): n = float(t[:-1]); return 'Alta' if n >= 75 else 'Media' if n >= 40 else 'Baja'
    return {'alta': 'Alta', 'buena': 'Alta', 'media': 'Media', 'regular': 'Media', 'baja': 'Baja', 'mala': 'Baja'}.get(t)
pr = pd.read_excel(f'{RAW}/08_protocolos.xlsx', dtype=object); pr.columns = ['dni', 'paciente', 'fecha', 'protocolo', 'adh', 'hallazgo']
prot = {}
for r in pr.itertuples():
    dni = parse_dni(r.dni)
    p = next((x for x in PROT if noacc(x).lower() == noacc(str(r.protocolo)).lower()), None)
    h = 'ninguno' if isna(r.hallazgo) else next((x for x in HALL if noacc(x).lower() == noacc(str(r.hallazgo)).lower()), 'ninguno')
    prot[dni] = dict(protocolo=p, adherencia=adh_n(r.adh), hallazgo_principal=h)
stats['adherencia_sin_dato'] = sum(1 for v in prot.values() if v['adherencia'] is None)

# ------------------------------------------------------------------ 8) ensamble: una fila por visita
U = ag[['dni', 'fecha', 'pa_sistolica']].rename(columns={'fecha': 'visita'}).set_index(['dni', 'visita'])
for part in (labw, labc, srcs, O, D, A): U = U.join(part, how='left')
U = U.reset_index().rename(columns={'visita': 'fecha_visita'})
U['visit_n'] = U.groupby('dni').fecha_visita.rank().astype(int) - 1
U['meses_desde_baseline'] = ((U.fecha_visita - U.groupby('dni').fecha_visita.transform('min')).dt.days / 30.4).round(1)
for c in ('programa', 'sexo'): U[c] = U.dni.map(lambda d: master.get(d, {}).get(c))
U['edad_cronologica'] = ((U.fecha_visita - U.dni.map(lambda d: master[d]['nac'])).dt.days / 365.25).round(1)
for k in ('protocolo', 'adherencia', 'hallazgo_principal'): U[k] = U.dni.map(lambda d: prot.get(d, {}).get(k))
for k in ('apoe', 'apoe_e4_carrier', 'mthfr_c677t', 'mthfr_tt', 'fto_alelos_riesgo', 'ace_id', 'lct_13910', 'hla_dq2_dq8', 'vdr_foki', 'cyp1a2_cafeina', 'gstt1'):
    U[k] = U.dni.map(lambda d: arows.get(d, {}).get(k))
for k in ('fam_cardiovascular', 'fam_diabetes', 'fam_cancer', 'fam_neurodegenerativa', 'intol_gluten_detectada', 'intol_lactosa_detectada', 'n_eventos_previos'):
    U[k] = U.dni.map(lambda d: estat.get(d, {}).get(k))
U['homa_ir'] = (U.glucosa * U.insulina / 405).round(2); U['ratio_tg_hdl'] = (U.trigliceridos / U.hdl).round(2)
U['carga_metales_idx'] = (U[['oligo_mercurio', 'oligo_plomo', 'oligo_cadmio', 'oligo_aluminio', 'oligo_arsenico', 'oligo_niquel']].div([0.8, 1.5, 0.12, 7.0, 0.2, 0.9]).mean(axis=1)).round(3)
U['ratio_zn_cu'] = (U.oligo_zinc / U.oligo_cobre).round(2); U['ratio_ca_mg'] = (U.oligo_calcio / U.oligo_magnesio).round(2)
U['fecha_visita'] = U.fecha_visita.dt.strftime('%Y-%m-%d')
U.to_csv(f'{OUT}/visitas_unificadas.csv', index=False)
pd.DataFrame([dict(dni=d, evento=t, anio=a) for d, v in estat.items() for t, a in v['_eventos']]).to_csv(f'{OUT}/eventos_previos_texto_libre.csv', index=False)

# ------------------------------------------------------------------ 9) validación contra la verdad del simulador
coh = pd.read_csv(f'{COH}/visitas_longitudinal.csv'); pac = pd.read_csv(f'{COH}/pacientes.csv'); ev_true = pd.read_csv(f'{COH}/eventos_clinicos.csv')
T = coh.merge(pac[['patient_id', 'dni']], on='patient_id'); T['dni'] = T.dni.astype(str)
T = T[T.dni.isin(set(U.dni))]
M = U.merge(T, on=['dni', 'fecha_visita'], suffixes=('', '_t')); stats['visitas_en_agenda'] = len(U); stats['visitas_cohorte_subset'] = len(T); stats['visitas_emparejadas_con_la_verdad'] = len(M)
GR = {'Laboratorio (16 analitos)': ('num', LAB_ORDER), 'Oligoscan (15 minerales y metales)': ('num', [omap[k] for k in omap if k.startswith('')][:0] or sorted(set(omap.values()))),
      'D-ROMs y PIC': ('num', ['drom_ucarr', 'pic_indice']),
      'Hábitos y síntomas (numéricos)': ('num', ['hora_acostarse', 'sesiones_fuerza_sem', 'min_cardio_sem', 'sedentarismo_h_dia', 'ultraprocesados_sem', 'alcohol_sem', 'dieta_mediterranea_score', 'estres_percibido', 'ansiedad_score',
                                                  'calidad_sueno', 'energia', 'dolor', 'claridad_mental', 'molestias_digestivas']),
      'Hábitos (categóricos) y antecedentes en texto libre': ('cat', ['celular_en_cama', 'tabaquismo', 'fam_cardiovascular', 'fam_diabetes', 'fam_cancer', 'fam_neurodegenerativa', 'intol_gluten_detectada', 'intol_lactosa_detectada']),
      'Genética (ADN Test, solo PRO)': ('cat', ['apoe', 'mthfr_c677t', 'fto_alelos_riesgo', 'ace_id', 'lct_13910', 'hla_dq2_dq8', 'vdr_foki', 'cyp1a2_cafeina', 'gstt1']),
      'Identidad y plan': ('cat', ['programa', 'sexo', 'protocolo', 'adherencia', 'hallazgo_principal'])}
val = []
for g, (typ, cols) in GR.items():
    n = ok = 0
    for c in cols:
        if c not in M or c + '_t' not in M:
            print('AVISO: columna sin contraparte en la verdad, no se valida:', c); continue
        a, b = M[c], M[c + '_t']
        mask = a.notna() & b.notna()
        if c == 'hallazgo_principal': mask &= (M['visit_n'] == 0)   # el hallazgo se registra en la consulta de integración (primera visita)
        if c in LAB_ORDER and c + '_censurado' in M: mask &= ~M[c + '_censurado'].fillna(False).astype(bool)
        if typ == 'num':
            tol = np.maximum(0.015 * b[mask].abs(), 0.06 if c in LAB_ORDER or c.startswith('oligo') else 0.025)
            good = ((a[mask].astype(float) - b[mask].astype(float)).abs() <= tol)
        else: good = (a[mask].astype(str).str.strip().str.lower() == b[mask].astype(str).str.strip().str.lower())
        n += int(mask.sum()); ok += int(good.sum())
    val.append(dict(grupo=g, comparados=n, correctos=ok, exactitud=round(100 * ok / n, 1) if n else None))
# eventos previos: cantidad por paciente
ec = ev_true.groupby('patient_id').size(); P = pac[pac.dni.astype(str).isin(set(U.dni))].copy(); P['dni'] = P.dni.astype(str); P['n_true'] = P.patient_id.map(ec).fillna(0).astype(int)
Pn = U.drop_duplicates('dni').set_index('dni').n_eventos_previos; P['n_pipe'] = P.dni.map(Pn)
val.append(dict(grupo='Eventos clínicos previos (conteo por paciente, texto libre)', comparados=int(P.n_pipe.notna().sum()), correctos=int((P.n_pipe == P.n_true).sum()), exactitud=round(100 * float((P.n_pipe == P.n_true).sum()) / max(1, int(P.n_pipe.notna().sum())), 1)))
fuente = {k: int(v) for k, v in U.fuente_laboratorio.value_counts().items()}
rep = dict(problemas_resueltos={k: int(v) for k, v in stats.items()}, validacion=val, fuente_laboratorio=fuente, ejemplos=ex, pacientes=int(U.dni.nunique()), visitas=int(len(U)),
           columnas_unificadas=int(U.shape[1]), nota='Wearables y composición corporal no vienen de estas fuentes; solo existen en la cohorte limpia simulada.')
json.dump(rep, open(f'{OUT}/calidad_datos.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(dict(problemas=rep['problemas_resueltos'], validacion=val, fuente=fuente), ensure_ascii=False, indent=1))
