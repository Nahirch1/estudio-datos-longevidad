"""Catálogo compartido (fuente única) de analitos de laboratorio y marcadores genéticos. Datos 100 % ficticios.

Lo usan el generador de la cohorte (decimales), las fuentes crudas (nombres, unidades, variantes), la limpieza (patrones y
conversiones de unidad), la exportación (dim_biomarcador) y las pruebas. Agregar un analito acá lo agrega en todo el circuito.

Cada analito: key, nombre (el que sale primero en los informes), unidad, ref (texto), dec (decimales), cat (categoría), alias
(nombres con los que lo informan distintos laboratorios), pat (regex sobre el nombre sin tildes y en minúsculas), lo/hi (rango numérico
de referencia), sexref (rango por sexo, si cambia) y alts (unidades alternativas: valor_alt = valor_limpio * multiplicador).
"""
import re, unicodedata

noacc = lambda s: ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')
LAB = []


def _a(key, nombre, unidad, ref, dec, cat, alias, pat, lo=None, hi=None, alts=(), sexref=None):
    LAB.append(dict(key=key, nombre=nombre, unidad=unidad, ref=ref, dec=dec, cat=cat, alias=[nombre] + list(alias), pat=pat, lo=lo, hi=hi,
                    alts=list(alts), sexref=sexref))


MMOL_COL = ('mmol/L', 0.02586, 2)
# ---- metabólico (las dos insulinas y las dos glucemias van primero: sus patrones son más específicos)
_a('glucosa_post_carga', 'Glucemia 2 h post carga (75 g)', 'mg/dL', '< 140', 0, 'Metabólico', ['GLUCOSA POST SOBRECARGA 2H', 'Glucosa 2 h post carga'],
   r'(glucemia|glucosa).*(post|sobrecarga|carga)', None, 139.9, [('mmol/L', 1 / 18.016, 2)])
_a('glucosa', 'Glucemia en ayunas', 'mg/dL', '70 - 99', 0, 'Metabólico', ['GLUCOSA', 'Glucemia', 'Glucosa en ayunas'], r'glucemia|glucosa', 70, 99.9, [('mmol/L', 1 / 18.016, 2)])
_a('hba1c', 'Hemoglobina glicosilada (HbA1c)', '%', '4.0 - 5.6', 1, 'Metabólico', ['HbA1c', 'Hb glicosilada'], r'hba1c|hemoglobina glic|hb glic', 4.0, 5.6)
_a('insulina_post_carga', 'Insulina 2 h post carga (no ayunas)', 'µU/mL', '< 60', 1, 'Metabólico', ['Insulina post carga (2 h)', 'INSULINA POSTPRANDIAL 2H', 'Insulina no ayunas (2 h)'],
   r'insulina.*(post|carga|2 ?h|no ayun)', None, 59.9)
_a('insulina_ayunas', 'Insulina en ayunas', 'µU/mL', '2.6 - 24.9', 1, 'Metabólico', ['Insulina basal', 'INSULINA BASAL (ayunas)'], r'^insulina', 2.6, 24.9)
# ---- lípidos
_a('colesterol_total', 'Colesterol total', 'mg/dL', '< 200', 0, 'Lípidos', ['COLESTEROL TOTAL'], r'colesterol total', None, 199.9, [MMOL_COL])
_a('hdl', 'HDL colesterol', 'mg/dL', '> 40 (H) / > 50 (M)', 0, 'Lípidos', ['Col HDL'], r'hdl', None, None, [MMOL_COL], {'M': (40, None), 'F': (50, None)})
_a('ldl', 'LDL colesterol', 'mg/dL', '< 130', 0, 'Lípidos', ['Col LDL (calculado)'], r'ldl', None, 129.9, [MMOL_COL])
_a('trigliceridos', 'Triglicéridos', 'mg/dL', '< 150', 0, 'Lípidos', ['TRIGLICERIDOS'], r'trigliceridos', None, 149.9, [('mmol/L', 0.01129, 2)])
_a('apob', 'Apolipoproteína B', 'mg/dL', '< 90', 0, 'Lípidos', ['APO B', 'ApoB'], r'apo ?(lipoproteina )?b\b|apolipoproteina b', None, 89.9)
_a('lipoproteina_a', 'Lipoproteína (a)', 'mg/dL', '< 30', 0, 'Lípidos', ['Lp(a)', 'LP A'], r'lipoproteina \(a\)|lp ?\(a\)|lp a\b', None, 29.9, [('nmol/L', 2.5, 1)])
# ---- inflamación y nutrientes
_a('pcr_us', 'PCR ultrasensible', 'mg/L', '< 3.0', 2, 'Inflamación', ['Proteína C reactiva (us)', 'PCR-us'], r'pcr|proteina c reactiva', None, 2.99, [('mg/dL', 0.1, 3)])
_a('homocisteina', 'Homocisteína', 'µmol/L', '5.0 - 15.0', 1, 'Inflamación', ['HOMOCISTEINA'], r'homocisteina', 5.0, 15.0)
_a('ferritina', 'Ferritina', 'ng/mL', '15 - 300', 0, 'Nutrientes', ['FERRITINA'], r'ferritina', 15, 300, (), {'M': (30, 400), 'F': (15, 150)})
_a('vitamina_d', 'Vitamina D (25-OH)', 'ng/mL', '30 - 100', 1, 'Nutrientes', ['25 OH Vitamina D'], r'vitamina d|25 oh', 30, 100, [('nmol/L', 2.496, 1)])
_a('b12', 'Vitamina B12', 'pg/mL', '200 - 900', 0, 'Nutrientes', ['B12'], r'b12', 200, 900)
# ---- tiroides
_a('tsh', 'TSH (tirotrofina)', 'µUI/mL', '0.27 - 4.20', 2, 'Tiroides', ['TSH'], r'\btsh\b|tirotrofina', 0.27, 4.20)
_a('t4_libre', 'T4 libre (tiroxina efectiva)', 'ng/dL', '0.93 - 1.70', 2, 'Tiroides', ['T4 libre', 'T4L'], r't4|tiroxina', 0.93, 1.70)
# ---- hemograma (el informe real trae estos valores y la fórmula leucocitaria)
_a('hematocrito', 'Hematocrito', '%', '40 - 54 (H) / 36 - 46 (M)', 1, 'Hemograma', ['HTO'], r'hematocrito|^hto$', 36, 54, (), {'M': (40, 54), 'F': (36, 46)})
_a('eritrocitos', 'Eritrocitos', '10^12/L', '4.5 - 5.9 (H) / 4.0 - 5.2 (M)', 2, 'Hemograma', ['Glóbulos rojos'], r'eritrocitos|globulos rojos', 4.0, 5.9, (), {'M': (4.5, 5.9), 'F': (4.0, 5.2)})
_a('hemoglobina', 'Hemoglobina (Hb)', 'g/dL', '13.0 - 18.0 (H) / 12.0 - 16.0 (M)', 1, 'Hemograma', ['HB', 'Hemoglobina sérica'], r'^hemoglobina( \(hb\))?$|^hb$|hemoglobina serica', 12, 18, [('g/L', 10, 0)], {'M': (13, 18), 'F': (12, 16)})
_a('vcm', 'Volumen corpuscular medio', 'fL', '80 - 94', 0, 'Hemograma', ['VCM'], r'volumen corpuscular|^vcm', 80, 94)
_a('hcm', 'HbCM (hemoglobina corpuscular media)', 'pg', '26 - 32', 1, 'Hemograma', ['HCM'], r'(?<!c)hbcm|^hcm|hemoglobina corpuscular', 26, 32)
_a('chcm', 'CHbCM (concentración corpuscular media)', 'g/dL', '32 - 36', 1, 'Hemograma', ['CHCM'], r'chbcm|^chcm|concentracion corpuscular', 32, 36)
_a('ade_cv', 'ADE-CV (ancho de distribución eritrocitaria)', '%', '11.5 - 14.5', 1, 'Hemograma', ['RDW-CV', 'ADE CV'], r'ade[- ]?cv|rdw[- ]?cv', 11.5, 14.5)
_a('ade_sd', 'ADE-SD', 'fL', '39.0 - 46.0', 1, 'Hemograma', ['RDW-SD', 'ADE SD'], r'ade[- ]?sd|rdw[- ]?sd', 39, 46)
_a('leucocitos', 'Leucocitos', '10^9/L', '4.5 - 11.0', 1, 'Hemograma', ['Glóbulos blancos', 'GB'], r'leucocitos|globulos blancos|^gb$', 4.5, 11.0)
_a('neutrofilos_pct', 'Neutrófilos segmentados', '%', '40 - 70', 1, 'Hemograma', ['Neutrófilos'], r'neutrofilos', 40, 70)
_a('linfocitos_pct', 'Linfocitos', '%', '20 - 45', 1, 'Hemograma', ['LINFOCITOS'], r'linfocitos', 20, 45)
_a('monocitos_pct', 'Monocitos', '%', '2 - 10', 1, 'Hemograma', ['MONOCITOS'], r'monocitos', 2, 10)
_a('eosinofilos_pct', 'Eosinófilos', '%', '0 - 6', 1, 'Hemograma', ['EOSINOFILOS'], r'eosinofilos', 0, 6)
_a('basofilos_pct', 'Basófilos', '%', '0 - 2', 1, 'Hemograma', ['BASOFILOS'], r'basofilos', 0, 2)
_a('plaquetas', 'Plaquetas', '10^9/L', '150 - 450', 0, 'Hemograma', ['PLAQUETAS', 'Recuento de plaquetas'], r'^plaquetas|recuento de plaquetas', 150, 450)
_a('vpm', 'Volumen plaquetario medio', 'fL', '7.5 - 11.5', 1, 'Hemograma', ['VPM'], r'volumen plaquetario|^vpm', 7.5, 11.5)
# ---- hepático y proteínas
_a('alt', 'TGP (ALT)', 'U/L', '10 - 41', 0, 'Hepático', ['ALT', 'GPT (ALT)'], r'tgp|\balt\b|\bgpt\b', 10, 41)
_a('ast', 'TGO (AST)', 'U/L', '< 40', 0, 'Hepático', ['AST', 'GOT (AST)'], r'tgo|\bast\b|\bgot\b', None, 40)
_a('fosfatasa_alcalina', 'Fosfatasa alcalina', 'U/L', '40 - 129 (H) / 35 - 104 (M)', 0, 'Hepático', ['FAL', 'Fosfatasa alcalina (IFCC)'], r'fosfatasa alcalina|^fal$', 35, 129, (), {'M': (40, 129), 'F': (35, 104)})
_a('ggt', 'GGT (glutamil transpeptidasa)', 'U/L', '10 - 71', 0, 'Hepático', ['Gamma GT', 'GGT'], r'ggt|glutamil|gamma ?gt', 10, 71)
_a('bilirrubina_indirecta', 'Bilirrubina indirecta', 'mg/dL', '< 0.80', 2, 'Hepático', ['BILIRRUBINA INDIRECTA', 'Bil. indirecta'], r'bil\w*\.? ?indirect', None, 0.8, [('mg/L', 10, 1)])
_a('bilirrubina_directa', 'Bilirrubina directa', 'mg/dL', '< 0.30', 2, 'Hepático', ['BILIRRUBINA DIRECTA', 'Bil. directa'], r'bil\w*\.? ?directa', None, 0.3, [('mg/L', 10, 1)])
_a('bilirrubina_total', 'Bilirrubina total', 'mg/dL', '< 1.20', 2, 'Hepático', ['BILIRRUBINA TOTAL', 'Bil. total'], r'bil\w*\.? ?total', None, 1.2, [('mg/L', 10, 1)])
_a('proteinas_totales', 'Proteínas totales', 'g/L', '66.0 - 87.0', 1, 'Hepático', ['PROTEINAS TOTALES'], r'proteinas totales', 66, 87, [('g/dL', 0.1, 2)])
_a('relacion_alb_glob', 'Relación albúmina/globulina', 'relación', '1.20 - 2.20', 2, 'Hepático', ['Relación A/G', 'Alb/Glob'], r'relacion|alb.*glob', 1.2, 2.2)
_a('albumina', 'Albúmina', 'g/L', '35.0 - 52.0', 1, 'Hepático', ['ALBUMINA'], r'albumina', 35, 52, [('g/dL', 0.1, 2)])
# ---- renal y electrolitos
_a('urea', 'Urea', 'g/L', '0.17 - 0.48', 2, 'Renal', ['UREMIA', 'Urea en sangre'], r'urea|uremia', 0.17, 0.48, [('mg/dL', 100, 0)])
_a('creatinina', 'Creatinina', 'mg/dL', '0.70 - 1.20', 2, 'Renal', ['CREATININA', 'Creatinina en sangre'], r'creatinina', 0.5, 1.2, [('µmol/L', 88.4, 0)], {'M': (0.7, 1.2), 'F': (0.5, 0.9)})
_a('egfr', 'Filtrado glomerular estimado (CKD-EPI 2021)', 'ml/min/1,73 m²', '> 90', 0, 'Renal', ['FGe CKD-EPI', 'Filtrado glomerular'], r'filtrado|egfr|\bfge\b|ckd', 90, None)
_a('acido_urico', 'Ácido úrico', 'mg/dL', '3.4 - 7.0 (H) / 2.4 - 6.0 (M)', 1, 'Renal', ['ACIDO URICO', 'Uricemia'], r'acido urico|uricemia', 2.4, 7.0, [('µmol/L', 59.48, 0)], {'M': (3.4, 7.0), 'F': (2.4, 6.0)})
_a('sodio', 'Sodio', 'mEq/L', '135 - 145', 0, 'Ionograma', ['Natremia', 'SODIO'], r'^sodio|natremia', 135, 145)
_a('potasio', 'Potasio', 'mEq/L', '3.5 - 5.1', 1, 'Ionograma', ['Kalemia', 'POTASIO'], r'^potasio|kalemia', 3.5, 5.1)
_a('cloro', 'Cloro', 'mEq/L', '98 - 110', 0, 'Ionograma', ['Cloremia', 'CLORO'], r'^cloro|cloremia', 98, 110)

# el orden de la lista es el orden de las columnas en las fuentes crudas; los patrones se prueban en este orden
LAB_KEYS = [a['key'] for a in LAB]
LAB_BY_KEY = {a['key']: a for a in LAB}
DERIVADOS = [('homa_ir', 'HOMA-IR (con insulina en ayunas)', 'Metabólico', 'índice'), ('ratio_tg_hdl', 'Relación triglicéridos / HDL', 'Lípidos', 'índice'),
             ('colesterol_no_hdl', 'Colesterol no HDL', 'Lípidos', 'mg/dL'), ('nlr', 'Relación neutrófilos / linfocitos', 'Hemograma', 'índice'),
             ('ratio_insulina_post_ayunas', 'Insulina post carga / en ayunas', 'Metabólico', 'índice')]


def canon_analyte(nombre):
    """Devuelve la clave del analito a partir del nombre tal como lo escribió el laboratorio (o None)."""
    n = noacc(nombre).lower().strip()
    for a in LAB:
        if re.search(a['pat'], n):
            return a['key']
    return None


def _u(s):
    return noacc(str(s)).lower().replace(' ', '').replace('µ', 'u').replace('μ', 'u')


def a_unidad_limpia(key, valor, unidad):
    """Convierte un valor informado en una unidad alternativa a la unidad del catálogo. Devuelve (valor, se_convirtio)."""
    u = _u(unidad)
    for lbl, mult, _dec in LAB_BY_KEY[key]['alts']:
        if u == _u(lbl) and u != _u(LAB_BY_KEY[key]['unidad']):
            return valor / mult, True
    return valor, False


def rango_ref(key, sexo):
    a = LAB_BY_KEY[key]
    if a['sexref'] and sexo in a['sexref']:
        return a['sexref'][sexo]
    return a['lo'], a['hi']


def egfr_ckdepi_2021(creat_mg_dl, edad, sexo):
    """Filtrado glomerular estimado, ecuación CKD-EPI 2021 (sin raza), en ml/min/1,73 m²."""
    f = sexo == 'F'
    k, al = (0.7, -0.241) if f else (0.9, -0.302)
    c = creat_mg_dl / k
    return 142 * (min(c, 1) ** al) * (max(c, 1) ** -1.200) * (0.9938 ** edad) * (1.012 if f else 1)


# ------------------------------------------------------------------ genética (ficticia; frecuencias aproximadas, solo para el simulador)
# (clave, gen, rsid, genotipos [0, 1 y 2 alelos de efecto], frecuencia del alelo de efecto, sentido, área)
GENES = [
    ('mthfr_a1298c', 'MTHFR A1298C', 'rs1801131', ['AA', 'AC', 'CC'], 0.30, 'riesgo', 'Homocisteína y metilación'),
    ('comt_val158met', 'COMT Val158Met', 'rs4680', ['GG', 'AG', 'AA'], 0.50, 'riesgo', 'Respuesta al estrés'),
    ('tcf7l2', 'TCF7L2', 'rs7903146', ['CC', 'CT', 'TT'], 0.28, 'riesgo', 'Glucosa y diabetes tipo 2'),
    ('pparg_pro12ala', 'PPARG Pro12Ala', 'rs1801282', ['CC', 'CG', 'GG'], 0.12, 'protector', 'Sensibilidad a la insulina'),
    ('lpa_rs10455872', 'LPA (lipoproteína a)', 'rs10455872', ['AA', 'AG', 'GG'], 0.07, 'riesgo', 'Lipoproteína (a) y riesgo cardiovascular'),
    ('chr9p21', '9p21 (cardiovascular)', 'rs10757274', ['AA', 'AG', 'GG'], 0.48, 'riesgo', 'Riesgo cardiovascular'),
    ('cetp_taqib', 'CETP TaqIB', 'rs708272', ['GG', 'AG', 'AA'], 0.42, 'protector', 'Nivel de HDL'),
    ('sod2_ala16val', 'SOD2 Ala16Val', 'rs4880', ['CC', 'CT', 'TT'], 0.50, 'riesgo', 'Estrés oxidativo'),
    ('gpx1_pro198leu', 'GPX1 Pro198Leu', 'rs1050450', ['CC', 'CT', 'TT'], 0.30, 'riesgo', 'Defensa antioxidante'),
    ('gc_vitd', 'GC (transporte de vitamina D)', 'rs2282679', ['TT', 'GT', 'GG'], 0.28, 'riesgo', 'Vitamina D'),
    ('mc4r', 'MC4R', 'rs17782313', ['TT', 'CT', 'CC'], 0.24, 'riesgo', 'Peso corporal y apetito'),
    ('actn3', 'ACTN3 R577X', 'rs1815739', ['RR', 'RX', 'XX'], 0.40, 'riesgo', 'Fuerza y potencia muscular'),
    ('bdnf_val66met', 'BDNF Val66Met', 'rs6265', ['GG', 'AG', 'AA'], 0.20, 'riesgo', 'Función cognitiva'),
    ('il6_174', 'IL6 -174 G/C', 'rs1800795', ['GG', 'CG', 'CC'], 0.40, 'riesgo', 'Inflamación'),
    ('tnf_308', 'TNF -308 G/A', 'rs1800629', ['GG', 'AG', 'AA'], 0.12, 'riesgo', 'Inflamación'),
    ('foxo3', 'FOXO3 (longevidad)', 'rs2802292', ['TT', 'GT', 'GG'], 0.35, 'protector', 'Longevidad'),
    ('nos3_glu298asp', 'NOS3 Glu298Asp', 'rs1799983', ['GG', 'GT', 'TT'], 0.30, 'riesgo', 'Presión arterial'),
    ('fut2_b12', 'FUT2 (vitamina B12)', 'rs601338', ['GG', 'AG', 'AA'], 0.45, 'riesgo', 'Vitamina B12'),
]
HFE_CATS = ['sin variantes', 'H63D portador', 'C282Y portador', 'compuesto u homocigota']
HFE_P = [0.70, 0.22, 0.06, 0.02]
GENES_BY_KEY = {g[0]: g for g in GENES}
# genética que ya existía (columnas propias del simulador)
GENES_BASE = [('apoe', 'APOE', 'rs429358/rs7412', 'Riesgo cardiovascular y neurodegenerativo'), ('mthfr_c677t', 'MTHFR C677T', 'rs1801133', 'Homocisteína y metilación'),
              ('fto_alelos_riesgo', 'FTO', 'rs9939609', 'Peso corporal'), ('ace_id', 'ACE I/D', 'rs4646994', 'Presión arterial y rendimiento'),
              ('lct_13910', 'LCT -13910', 'rs4988235', 'Tolerancia a la lactosa'), ('hla_dq2_dq8', 'HLA DQ2/DQ8', 'HLA', 'Predisposición celíaca'),
              ('vdr_foki', 'VDR FokI', 'rs2228570', 'Vitamina D'), ('cyp1a2_cafeina', 'CYP1A2', 'rs762551', 'Metabolismo de la cafeína'), ('gstt1', 'GSTT1', 'deleción', 'Detoxificación')]
GEN_COLS = [g[0] for g in GENES] + ['hfe']
