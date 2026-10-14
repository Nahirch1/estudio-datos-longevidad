"""
01 · COHORTE SINTÉTICA UNIFICADA (datos 100% ficticios)
42.000 pacientes (programa BASE y programa PRO), visitas a 0, ~6 y ~12 meses, con:
  estudios típicos de una clínica de longevidad (laboratorio completo de 51 analitos con insulina en ayunas y post carga, D-ROMs, PIC*, Oligoscan,
  ADN Test ampliado a 28 marcadores solo en PRO), anamnesis (hábitos, sueño, estrés,
  ansiedad, alimentación, actividad), antecedentes familiares, intolerancias, eventos clínicos previos, síntomas
  reportados, padecimientos derivados por umbrales editables, protocolos con adherencia y abandono.
* PIC y los rangos del Oligoscan son placeholders. Los efectos de los protocolos son parámetros del simulador.
"""
import numpy as np, pandas as pd, os, sys, json, unicodedata
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalogo import *

SEED, N = 7, 42000
rng = np.random.default_rng(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f'{HERE}/datos/cohorte'
os.makedirs(OUT, exist_ok=True)
noacc = lambda s: ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
sig = lambda x: 1 / (1 + np.exp(-x))
clip = np.clip

F_NAMES = ['María','Lucía','Sofía','Valentina','Camila','Julieta','Florencia','Agustina','Carolina','Paula','Natalia','Mariana','Romina','Claudia','Silvia',
           'Laura','Verónica','Gabriela','Daniela','Constanza','Marcela','Luciana','Cecilia','Andrea','Patricia','Ana','Belén','Candela','Micaela','Rocío']
M_NAMES = ['Juan','Martín','Santiago','Matías','Nicolás','Lucas','Federico','Diego','Sebastián','Pablo','Facundo','Gonzalo','Ignacio','Maximiliano','Fernando',
           'Rodrigo','Alejandro','Ezequiel','Tomás','Leandro','Hernán','Esteban','Marcelo','Gustavo','Javier','Ramiro','Bruno','Agustín','Emiliano','Damián']
SURNAMES = ['González','Rodríguez','Gómez','Fernández','López','Díaz','Martínez','Pérez','García','Sánchez','Romero','Sosa','Álvarez','Torres','Ruiz','Ramírez',
            'Flores','Benítez','Acosta','Medina','Herrera','Suárez','Aguirre','Giménez','Gutiérrez','Pereyra','Rojas','Molina','Castro','Ortiz','Silva','Núñez',
            'Luna','Juárez','Cabrera','Ríos','Morales','Domínguez','Moreno','Peralta','Vega','Carrizo','Ledesma','Ibarra','Quiroga','Barrios','Maldonado',
            'Figueroa','Villalba','Ponce','Bustos','Funes','Lencina','Paz','Correa','Franco','Montenegro','Arias','Cardozo','Bravo']
CITIES = ['CABA','Ciudad de Buenos Aires','Capital Federal','Vicente López','San Isidro','Tigre','Pilar','Lomas de Zamora','La Plata','Rosario','Córdoba','Mendoza','San Martín']

# ------------------------------------------------------------------ pacientes: básicos
sex = rng.choice(['F', 'M'], N, p=[0.54, 0.46]); M = (sex == 'M').astype(float); F = 1 - M
age0 = np.clip(rng.normal(50, 11, N), 28, 80).round(1)
programa = np.where(rng.random(N) < 0.35, 'PRO', 'BASE')
first = [rng.choice(F_NAMES) if s == 'F' else rng.choice(M_NAMES) for s in sex]
last = [rng.choice(SURNAMES) for _ in range(N)]
dnis = rng.choice(np.arange(14_000_000, 45_000_000), N, replace=False)
birth = [date(2026, 10, 7) - timedelta(days=int(a * 365.25 + rng.integers(0, 365))) for a in age0]
city = rng.choice(CITIES, N, p=[.2, .14, .08, .08, .06, .05, .05, .05, .06, .06, .05, .05, .07])
G = rng.normal(0, 1, N) + 0.35 * (age0 - 50) / 11
hab = 0.35 * G + rng.normal(0, 0.94, N)           # estilo de vida no saludable (más alto = peor)

# ------------------------------------------------------------------ hábitos / anamnesis basal
hora0 = clip(23.0 + 0.5 * hab + rng.normal(0, 0.8, N), 21, 26)          # 25.5 = 01:30
celu0 = (rng.random(N) < sig(0.4 + 0.6 * hab)).astype(int)
fuerza0 = clip(np.round(2.0 - 0.7 * hab + rng.normal(0, 1, N)), 0, 6).astype(int)
cardio0 = clip(150 - 45 * hab + rng.normal(0, 50, N), 0, 450)
sed0 = clip(8 + 1.2 * hab + rng.normal(0, 1.5, N), 3, 14)
ult0 = clip(np.round(6 + 2.5 * hab + rng.normal(0, 2, N)), 0, 21)
alc0 = clip(np.round(4 + 2 * hab + rng.normal(0, 3, N)), 0, 25)
dieta0 = clip(5.5 - 1.2 * hab + rng.normal(0, 1.3, N), 0, 10)
tabaco = rng.choice(['Nunca', 'Ex', 'Actual'], N, p=[.62, .26, .12])
estres0 = clip(5 + 0.8 * hab + rng.normal(0, 1.7, N), 0, 10)
ansi0 = clip(3.5 + 0.6 * (estres0 - 5) + rng.normal(0, 1.6, N), 0, 10)
sue0 = clip(7.3 - 0.5 * hab - 0.3 * (estres0 - 5) - 0.6 * celu0 + rng.normal(0, 1.2, N), 0, 10)
FAM = {k: (rng.random(N) < p).astype(int) for k, p in [('fam_cardiovascular', .30), ('fam_diabetes', .28), ('fam_cancer', .20), ('fam_neurodegenerativa', .10)]}

# ------------------------------------------------------------------ genética ficticia (el ADN Test solo existe en programa PRO)
apoe = rng.choice(['e3/e3', 'e3/e4', 'e2/e3', 'e4/e4', 'e2/e4'], N, p=[.62, .22, .11, .03, .02])
e4 = np.array(['4' in g for g in apoe]).astype(int)
mthfr = rng.choice(['CC', 'CT', 'TT'], N, p=[.45, .40, .15]); tt = (mthfr == 'TT').astype(int)
fto = rng.choice([0, 1, 2], N, p=[.36, .48, .16])
ace = rng.choice(['II', 'ID', 'DD'], N, p=[.25, .50, .25])
lct = rng.choice(['CC', 'CT', 'TT'], N, p=[.30, .45, .25])
hla = (rng.random(N) < 0.30).astype(int)
vdr = rng.choice(['FF', 'Ff', 'ff'], N, p=[.35, .45, .20])
cyp = rng.choice(['rápido', 'lento'], N, p=[.45, .55])
gstt1 = rng.choice(['presente', 'nulo'], N, p=[.80, .20])
# variantes adicionales (frecuencias aproximadas y ficticias; HWE): n = cantidad de alelos de efecto (0, 1 o 2)
def _geno(q): return rng.choice([0, 1, 2], N, p=[(1 - q) ** 2, 2 * q * (1 - q), q ** 2])
GN = {g[0]: _geno(g[4]) for g in GENES}
GL = {g[0]: np.array(g[3])[GN[g[0]]] for g in GENES}
hfe_n = rng.choice([0, 1, 2, 3], N, p=HFE_P); hfe_lab = np.array(HFE_CATS)[hfe_n]
zs_ = lambda x: (x - x.mean()) / x.std()
prs = zs_(0.45 * fto + 0.50 * GN['tcf7l2'] + 0.30 * GN['mc4r'] - 0.30 * GN['pparg_pro12ala'] + 0.15 * (ace == 'DD') + rng.normal(0, 0.6, N))   # riesgo metabólico
prs_card = zs_(0.50 * GN['chr9p21'] + 0.60 * GN['lpa_rs10455872'] + 0.40 * e4 + 0.20 * GN['nos3_glu298asp'] + 0.15 * GN['il6_174'] + 0.15 * GN['tnf_308'] - 0.20 * GN['cetp_taqib'] + rng.normal(0, 0.6, N))
GEN_PESOS = dict(apoe_e4=0.9, mthfr_tt=0.5, fto=0.35, prs=0.30, prs_card=0.25, foxo3=-0.25)
gap_raw = GEN_PESOS['apoe_e4'] * e4 + GEN_PESOS['mthfr_tt'] * tt + GEN_PESOS['fto'] * fto + GEN_PESOS['prs'] * prs + GEN_PESOS['prs_card'] * prs_card + GEN_PESOS['foxo3'] * GN['foxo3']
GEN_PESOS['centro'] = round(float(-gap_raw.mean()), 3)
gap_gen = gap_raw + GEN_PESOS['centro']          # componente FIJO de la brecha (no cambia con hábitos)
json.dump(GEN_PESOS, open(f'{OUT}/parametros_geneticos.json', 'w'))
nvr = (sum((GN[g[0]] > 0).astype(int) for g in GENES if g[5] == 'riesgo') + e4 + tt + (fto > 0) + hla + (hfe_n > 0)).astype(int)   # variantes de riesgo presentes
# efectos directos de algunas variantes sobre un analito o medida concreta (el resto actúa a través de los dominios latentes)
DIR = dict(hdl=3.0 * GN['cetp_taqib'], vitd=-2.0 * GN['gc_vitd'], b12=-22.0 * GN['fut2_b12'], ferr_log=np.array([0, 0.30, 0.65, 1.0])[hfe_n], sbp=1.2 * GN['nos3_glu298asp'],
           imc=0.30 * GN['mc4r'], grip=-1.2 * (GN['actn3'] == 2), clar=-0.25 * GN['bdnf_val66met'], drom=5.0 * GN['sod2_ala16val'], lpa_log=1.1 * GN['lpa_rs10455872'],
           hcy_log=0.04 * GN['mthfr_a1298c'])
estres0 = clip(estres0 + 0.30 * GN['comt_val158met'], 0, 10); ansi0 = clip(ansi0 + 0.25 * GN['comt_val158met'], 0, 10)

# intolerancias (ficticias) y detección
intol_lac = (rng.random(N) < 0.08 + 0.35 * (lct == 'CC')).astype(int)
intol_glu = (rng.random(N) < 0.04 + 0.12 * hla).astype(int)
det_p = np.where(programa == 'PRO', 0.85, 0.5)
lac_det = (intol_lac & (rng.random(N) < det_p)).astype(int)
glu_det = (intol_glu & (rng.random(N) < det_p)).astype(int)

# ------------------------------------------------------------------ dominios latentes
def dom(): return 0.5 * G + rng.normal(0, 0.85, N)
zm = dom() + 0.12 * hab + 0.30 * FAM['fam_diabetes'] + 0.15 * fto + 0.20 * GN['tcf7l2'] - 0.15 * GN['pparg_pro12ala'] + 0.08 * GN['mc4r']
zi = dom() + 0.10 * hab + 0.05 * (estres0 - 5) + 0.08 * GN['il6_174'] + 0.10 * GN['tnf_308'] + 0.05 * GN['sod2_ala16val'] + 0.06 * GN['gpx1_pro198leu']
zc = dom() + 0.08 * hab + 0.25 * FAM['fam_cardiovascular'] + 0.30 * e4 + 0.12 * GN['chr9p21'] + 0.12 * GN['lpa_rs10455872'] + 0.04 * GN['nos3_glu298asp'] - 0.05 * GN['cetp_taqib']
zx = dom()
zf = -0.4 * G + rng.normal(0, 0.9, N) - 0.15 * hab - 0.15 * (GN['actn3'] == 2)

# ------------------------------------------------------------------ protocolos
PROTOS = ['Nutrición metabólica', 'Suplementación antioxidante', 'Entrenamiento VO2máx + sueño', 'Suplementación y minerales', 'Combinado integral', 'Seguimiento estándar']
EFFECT = {'Nutrición metabólica': (-0.55, -0.25, -0.25, 0.00, 0.10), 'Suplementación antioxidante': (-0.05, -0.55, -0.10, -0.10, 0.00),
          'Entrenamiento VO2máx + sueño': (-0.30, -0.20, -0.30, 0.00, 0.60), 'Suplementación y minerales': (0.00, -0.15, -0.05, -0.45, 0.00),
          'Combinado integral': (-0.45, -0.40, -0.40, -0.20, 0.40), 'Seguimiento estándar': (0, 0, 0, 0, 0)}
HABW = {'Nutrición metabólica': (1.0, 0.2, 0.2), 'Suplementación antioxidante': (0.3, 0.1, 0.2), 'Entrenamiento VO2máx + sueño': (0.2, 1.0, 1.0),
        'Suplementación y minerales': (0.3, 0.1, 0.1), 'Combinado integral': (0.9, 0.9, 0.9), 'Seguimiento estándar': (0, 0, 0)}   # nutrición, entrenamiento, sueño/estrés
SUPP = {'Suplementación antioxidante', 'Suplementación y minerales', 'Combinado integral'}
weak = np.argmax(np.vstack([zm, zi, zc, zx, -zf]), axis=0)
by_weak = ['Nutrición metabólica', 'Suplementación antioxidante', 'Combinado integral', 'Suplementación y minerales', 'Entrenamiento VO2máx + sueño']
protocolo = np.array(['Seguimiento estándar' if (u := rng.random()) < 0.15 else rng.choice(PROTOS[:5]) if u < 0.55 else by_weak[weak[n]] for n in range(N)])
adh = rng.choice(['Alta', 'Media', 'Baja'], N, p=[.38, .40, .22])
adh_val = np.array([rng.uniform(*{'Alta': (.9, 1.1), 'Media': (.4, .6), 'Baja': (0, .2)}[a]) for a in adh])
acelerado = rng.random(N) < 0.18
# respuesta individual al protocolo: multiplicador por persona (log-normal) y ~10 % de no respondedores
resp = np.exp(rng.normal(-0.04, 0.40, N)) * np.where(rng.random(N) < 0.10, rng.uniform(0.0, 0.25, N), 1.0)
# evento intercurrente (infección, estrés agudo, viaje): afecta un solo control en ~6 % de los pacientes
evento_visita = np.where(rng.random(N) < 0.06, rng.integers(1, 3, N), -1)
drift = np.where(acelerado, rng.normal(0.16, 0.04, N), rng.normal(0.03, 0.03, N))

off = {k: rng.normal(0, 1, N) for k in ['tsh', 'crea', 'b12', 'vd', 'hb', 'vcm', 'rdw', 'wbc', 'plt', 'vpm', 'mono', 'eos', 'baso', 'neut', 'urea', 'uric', 'na', 'k', 'cl', 'alp', 'ggt', 'bil', 'bild', 'prot', 'alb', 'lpa']}
OLIGO = {'Calcio': ('m', 60, 120), 'Magnesio': ('m', 25, 50), 'Sodio': ('m', 700, 1000), 'Potasio': ('m', 250, 450), 'Zinc': ('m', 110, 200),
         'Cobre': ('m', 10, 22), 'Hierro': ('m', 20, 45), 'Selenio': ('m', 0.9, 1.6), 'Manganeso': ('m', 0.08, 0.2), 'Mercurio': ('t', 0, 0.8),
         'Plomo': ('t', 0, 1.5), 'Cadmio': ('t', 0, 0.12), 'Aluminio': ('t', 0, 7.0), 'Arsénico': ('t', 0, 0.2), 'Níquel': ('t', 0, 0.9)}
OKEY = {k: 'oligo_' + noacc(k.lower()) for k in OLIGO}
off_ol = {k: rng.normal(0, 0.8, N) for k in OLIGO}
base_date = [date(2023, 1, 9) + timedelta(days=int(d)) for d in rng.integers(0, 938, N)]
birth = [base_date[n] - timedelta(days=int(age0[n] * 365.25)) for n in range(N)]   # fecha de nacimiento coherente con la edad en la primera visita

# ------------------------------------------------------------------ padecimientos: umbrales EDITABLES (genéricos, no son los de ninguna clínica real)
UMBRALES = {
    'prediabetes': 'hba1c >= 5.7 o glucosa >= 100', 'resistencia_insulinica': 'homa_ir >= 2.5',
    'dislipidemia': 'ldl >= 130 o trigliceridos >= 150 o hdl < 40 (hombres) / < 50 (mujeres)', 'presion_elevada': 'pa_sistolica >= 130',
    'deficit_vitamina_d': 'vitamina_d < 20', 'inflamacion_baja_grado': 'pcr_us >= 3', 'carga_metales_alta': 'carga_metales_idx >= 0.6',
    'anemia': 'hemoglobina < 13 (hombres) / < 12 (mujeres)', 'hiperuricemia': 'acido_urico >= 7 (hombres) / >= 6 (mujeres)',
    'hiperinsulinemia_postcarga': 'insulina_post_carga >= 60 (solo si se midió)', 'enzimas_hepaticas_elevadas': 'alt > 41 o ggt > 71'}
def condiciones(r, female):
    return {'cond_prediabetes': int(r['hba1c'] >= 5.7 or r['glucosa'] >= 100), 'cond_resistencia_insulinica': int(r['homa_ir'] >= 2.5),
            'cond_dislipidemia': int(r['ldl'] >= 130 or r['trigliceridos'] >= 150 or r['hdl'] < (50 if female else 40)),
            'cond_presion_elevada': int(r['pa_sistolica'] >= 130), 'cond_deficit_vitamina_d': int(r['vitamina_d'] < 20),
            'cond_inflamacion_baja_grado': int(r['pcr_us'] >= 3), 'cond_carga_metales_alta': int(r['carga_metales_idx'] >= 0.6),
            'cond_anemia': int(r['hemoglobina'] < (12 if female else 13)), 'cond_hiperuricemia': int(r['acido_urico'] >= (6.0 if female else 7.0)),
            'cond_hiperinsulinemia_postcarga': int(r['insulina_post_carga'] >= 60), 'cond_enzimas_hepaticas_elevadas': int(r['alt'] > 41 or r['ggt'] > 71)}

def condiciones_vec(d):
    f = (d.sexo == 'F').values
    return pd.DataFrame({'cond_prediabetes': ((d.hba1c >= 5.7) | (d.glucosa >= 100)).astype(int), 'cond_resistencia_insulinica': (d.homa_ir >= 2.5).astype(int),
                         'cond_dislipidemia': ((d.ldl >= 130) | (d.trigliceridos >= 150) | (d.hdl < np.where(f, 50, 40))).astype(int), 'cond_presion_elevada': (d.pa_sistolica >= 130).astype(int),
                         'cond_deficit_vitamina_d': (d.vitamina_d < 20).astype(int), 'cond_inflamacion_baja_grado': (d.pcr_us >= 3).astype(int), 'cond_carga_metales_alta': (d.carga_metales_idx >= 0.6).astype(int),
                         'cond_anemia': (d.hemoglobina < np.where(f, 12, 13)).astype(int), 'cond_hiperuricemia': (d.acido_urico >= np.where(f, 6.0, 7.0)).astype(int),
                         'cond_hiperinsulinemia_postcarga': (d.insulina_post_carga >= 60).astype(int), 'cond_enzimas_hepaticas_elevadas': ((d.alt > 41) | (d.ggt > 71)).astype(int)}, index=d.index)

# ------------------------------------------------------------------ visitas
rows, truth, frames, tframes = [], [], [], []
for n in range(N):
    t_list = [0.0]
    came6 = rng.random() < 0.90 - (0.17 if adh[n] == 'Baja' else 0)
    if came6: t_list.append(float(clip(rng.normal(6, 0.6), 4.5, 8)))
    if (came6 and rng.random() < 0.82 - (0.22 if adh[n] == 'Baja' else 0)) or (not came6 and rng.random() < 0.25):
        t_list.append(float(clip(rng.normal(12, 0.8), 10, 14.5)))
    pw = HABW[protocolo[n]]
    for k, t in enumerate(t_list):
        ramp = (1 - np.exp(-t / 5)) / (1 - np.exp(-12 / 5)); yrs = t / 12
        phi = adh_val[n] * ramp
        e = np.array(EFFECT[protocolo[n]]) * adh_val[n] * ramp * resp[n]
        nz = lambda: rng.normal(0, 0.12)
        agudo = 1.0 if evento_visita[n] == k else 0.0   # picos transitorios el día del control
        m_ = zm[n] + drift[n] * yrs + e[0] + nz(); i_ = zi[n] + drift[n] * yrs + e[1] + nz() + 0.9 * agudo; c_ = zc[n] + drift[n] * yrs + e[2] + nz()
        x_ = zx[n] + 0.4 * drift[n] * yrs + e[3] + nz(); f_ = zf[n] - drift[n] * yrs + e[4] + nz()
        a = age0[n] + yrs; Fm = F[n]; Mm = M[n]
        supp = 12.0 * phi if protocolo[n] in SUPP else 0.0
        nut, ent, sue = pw[0] * phi, pw[1] * phi, pw[2] * phi
        # hábitos en este momento
        h_ult = int(clip(round(ult0[n] * (1 - 0.5 * nut) + rng.normal(0, 0.7)), 0, 21)); h_alc = int(clip(round(alc0[n] * (1 - 0.35 * nut) + rng.normal(0, 0.7)), 0, 25))
        h_die = float(clip(dieta0[n] + 2.5 * nut + rng.normal(0, 0.4), 0, 10)); h_fue = int(clip(round(fuerza0[n] + 2 * ent + rng.normal(0, 0.4)), 0, 6))
        h_car = float(clip(cardio0[n] + 90 * ent + rng.normal(0, 15), 0, 450)); h_sed = float(clip(sed0[n] - 2 * ent + rng.normal(0, 0.3), 3, 14))
        h_cel = int(celu0[n] == 1 and not (rng.random() < 0.7 * sue)); h_hor = float(clip(hora0[n] - 0.9 * sue + rng.normal(0, 0.2), 21, 26))
        h_est = float(clip(estres0[n] - 1.8 * sue - 0.4 * ent + rng.normal(0, 0.5), 0, 10)); h_ans = float(clip(ansi0[n] - 1.5 * sue + rng.normal(0, 0.5), 0, 10))
        h_sue = float(clip(sue0[n] + 1.8 * sue + rng.normal(0, 0.5), 0, 10))
        # síntomas reportados (0-10)
        trat = protocolo[n] != 'Seguimiento estándar'
        resolv = min(1.0, phi) if trat else 0.0
        g_f = intol_glu[n] * (1 - (glu_det[n] * resolv)); l_f = intol_lac[n] * (1 - (lac_det[n] * resolv))
        r = dict(patient_id=f'P{n+1:05d}', visit_n=k, meses_desde_baseline=round(t, 1), fecha_visita=base_date[n] + timedelta(days=int(t * 30.4)),
                 sexo=sex[n], edad_cronologica=round(a, 1), programa=programa[n], protocolo=protocolo[n], adherencia=adh[n])
        # metabólico
        r['glucosa'] = 90 + 0.15 * (a - 50) + 6 * m_ + rng.normal(0, 2.5); r['hba1c'] = 5.25 + 0.005 * (a - 50) + 0.22 * m_ + rng.normal(0, 0.05)
        r['insulina_ayunas'] = np.exp(2.0 + 0.35 * m_ + rng.normal(0, 0.1)); r['homa_ir'] = r['glucosa'] * r['insulina_ayunas'] / 405
        # curva con carga de 75 g de glucosa: se pide más a quien tiene señales metabólicas, así que la falta de dato NO es al azar
        post_ok = rng.random() < clip(0.55 + 0.12 * m_, 0.2, 0.9)
        r['glucosa_post_carga'] = 70 + 0.55 * r['glucosa'] + 14 * m_ + 0.25 * (a - 50) + rng.normal(0, 9) if post_ok else np.nan
        r['insulina_post_carga'] = clip(r['insulina_ayunas'] * np.exp(1.30 + 0.30 * m_ + rng.normal(0, 0.22)), 3, 350) if post_ok else np.nan
        r['ratio_insulina_post_ayunas'] = r['insulina_post_carga'] / r['insulina_ayunas'] if post_ok else np.nan
        r['trigliceridos'] = np.exp(4.6 + 0.30 * m_ + 0.003 * (a - 50) + rng.normal(0, 0.1))
        r['grasa_corporal_pct'] = clip(24 + 9 * Fm + 0.12 * (a - 50) + 3.5 * m_ + rng.normal(0, 1.5), 8, 55)
        r['imc'] = 24.5 + 0.8 * Mm + 2.2 * m_ + DIR['imc'][n] + rng.normal(0, 0.8)
        r['alt'] = max(8, 24 + 6 * Mm + 3.5 * m_ + rng.normal(0, 3)); r['ast'] = max(8, 23 + 4 * Mm + 2 * m_ + rng.normal(0, 3))
        # cardiovascular
        r['ldl'] = 112 + 0.4 * (a - 50) + 20 * c_ + rng.normal(0, 5); r['hdl'] = 48 + 10 * Fm - 7 * c_ - 2 * m_ + DIR['hdl'][n] + rng.normal(0, 3)
        r['colesterol_total'] = r['ldl'] + r['hdl'] + r['trigliceridos'] / 5; r['ratio_tg_hdl'] = r['trigliceridos'] / r['hdl']; r['colesterol_no_hdl'] = r['colesterol_total'] - r['hdl']
        r['apob'] = max(30, 0.62 * r['ldl'] + 0.07 * r['trigliceridos'] + 7 + rng.normal(0, 5))
        r['lipoproteina_a'] = np.exp(np.log(14) + 0.85 * off['lpa'][n] + DIR['lpa_log'][n] + rng.normal(0, 0.04))   # casi fija en cada persona
        r['pa_sistolica'] = 117 + 0.35 * (a - 50) + 7 * c_ + DIR['sbp'][n] + rng.normal(0, 4)
        r['homocisteina'] = max(4, np.exp(np.log(9.5) + 0.18 * c_ + 0.004 * (a - 50) + 0.35 * tt[n] + DIR['hcy_log'][n] + rng.normal(0, 0.08)) - 1.6 * supp / 12)
        # inflamación / estrés oxidativo
        r['pcr_us'] = np.exp(0.55 * i_ + 0.004 * (a - 50) + rng.normal(0, 0.2)); r['drom_ucarr'] = clip(290 + 0.5 * (a - 50) + 27 * i_ + DIR['drom'][n] + rng.normal(0, 12), 180, 520)
        r['pic_indice'] = clip(40 + 11 * i_ + rng.normal(0, 4), 2, 98)
        r['ferritina'] = np.exp(np.log(150 if Mm else 60) + 0.25 * i_ + rng.normal(0, 0.12) + 0.15 * m_ + DIR['ferr_log'][n])
        estac = 2.5 * np.cos(2 * np.pi * ((base_date[n] + timedelta(days=int(t * 30.4))).timetuple().tm_yday - 15) / 365)
        r['vitamina_d'] = max(6, 27 + estac + 5 * off['vd'][n] - (3 if vdr[n] == 'ff' else 0) + DIR['vitd'][n] + supp + rng.normal(0, 2))
        r['b12'] = max(150, 420 + 100 * off['b12'][n] + DIR['b12'][n] + supp * 6 + rng.normal(0, 25)); r['tsh'] = np.exp(np.log(2.1) + 0.35 * off['tsh'][n] + rng.normal(0, 0.08))
        r['creatinina'] = max(0.4, 0.75 + 0.2 * Mm + 0.1 * off['crea'][n] + 0.002 * (a - 50) + rng.normal(0, 0.03))
        # --- panel de laboratorio completo (como el de un informe hospitalario): hemograma, hepático, proteínas, renal, ionograma, tiroides
        hb = 13.4 + 1.8 * Mm - 0.012 * (a - 50) * (1 + 0.5 * Mm) - 0.12 * i_ + 0.65 * off['hb'][n] + rng.normal(0, 0.18)
        hto = 3.0 * hb + 0.9 + rng.normal(0, 0.45)
        vcm = 90.2 + 0.03 * (a - 50) + 2.6 * off['vcm'][n] - 0.004 * (r['b12'] - 420) + rng.normal(0, 0.5)
        r['hemoglobina'] = hb; r['hematocrito'] = hto; r['vcm'] = vcm
        r['eritrocitos'] = hto * 10 / vcm; r['hcm'] = hb * 10 / r['eritrocitos']; r['chcm'] = hb / hto * 100
        r['ade_cv'] = clip(13.3 + 0.015 * (a - 50) + 0.30 * i_ + 0.25 * off['rdw'][n] + rng.normal(0, 0.15), 11.2, 20)
        r['ade_sd'] = r['ade_cv'] * vcm / 100 * 3.45 + rng.normal(0, 0.6)
        r['leucocitos'] = np.exp(np.log(6.3) + 0.11 * i_ + 0.12 * (tabaco[n] == 'Actual') + 0.14 * off['wbc'][n] + rng.normal(0, 0.08))
        mono = clip(7.2 + 0.7 * off['mono'][n] + 0.2 * i_ + rng.normal(0, 0.6), 3, 13); eos = clip(2.4 * np.exp(0.5 * off['eos'][n] + rng.normal(0, 0.2)), 0.2, 12)
        baso = clip(0.55 + 0.2 * off['baso'][n] + rng.normal(0, 0.12), 0, 2.0)
        neut = min(clip(58 + 3.5 * i_ + 3.0 * off['neut'][n] + rng.normal(0, 1.8), 38, 80), 100 - mono - eos - baso - 12)
        r['neutrofilos_pct'] = neut; r['monocitos_pct'] = mono; r['eosinofilos_pct'] = eos; r['basofilos_pct'] = baso
        r['linfocitos_pct'] = 100 - neut - mono - eos - baso; r['nlr'] = neut / r['linfocitos_pct']
        r['plaquetas'] = np.exp(np.log(245) + 0.08 * Fm + 0.07 * i_ - 0.004 * (a - 50) + 0.14 * off['plt'][n] + rng.normal(0, 0.05))
        r['vpm'] = clip(10.4 - 2.2 * np.log(r['plaquetas'] / 245) + 0.25 * off['vpm'][n] + rng.normal(0, 0.12), 7, 14)
        r['urea'] = max(0.12, 0.31 + 0.045 * Mm + 0.0018 * (a - 50) + 0.04 * off['urea'][n] + 0.25 * (r['creatinina'] - 0.8) + rng.normal(0, 0.025))
        r['egfr'] = egfr_ckdepi_2021(round(r['creatinina'], 2), round(a, 1), sex[n])
        r['acido_urico'] = max(2.0, 4.5 + 1.4 * Mm + 0.45 * m_ + 0.012 * (a - 50) + 0.5 * off['uric'][n] + 0.01 * h_alc + rng.normal(0, 0.25))
        r['sodio'] = 140.0 + 1.1 * off['na'][n] + rng.normal(0, 0.7); r['potasio'] = 4.35 + 0.18 * off['k'][n] + rng.normal(0, 0.1)
        r['cloro'] = r['sodio'] - 35.5 + 0.9 * off['cl'][n] + rng.normal(0, 0.7)
        r['fosfatasa_alcalina'] = max(25, 68 + 5 * Mm + 0.25 * (a - 50) + 3.5 * m_ + 12 * off['alp'][n] + rng.normal(0, 4))
        r['ggt'] = np.exp(np.log(19) + 0.33 * Mm + 0.25 * m_ + 0.018 * h_alc + 0.25 * off['ggt'][n] + rng.normal(0, 0.10))
        bi = np.exp(np.log(0.46) + 0.12 * Mm + 0.22 * off['bil'][n] + rng.normal(0, 0.07)); bd = np.exp(np.log(0.19) + 0.10 * off['bild'][n] + rng.normal(0, 0.07))
        r['bilirrubina_indirecta'] = bi; r['bilirrubina_directa'] = bd; r['bilirrubina_total'] = bi + bd
        alb = 43.8 - 0.9 * i_ - 0.06 * (a - 50) + 1.2 * off['alb'][n] + rng.normal(0, 0.6); prot = max(alb + 12, 71 + 1.2 * i_ + 2.0 * off['prot'][n] + rng.normal(0, 0.8))
        r['albumina'] = alb; r['proteinas_totales'] = prot; r['relacion_alb_glob'] = alb / (prot - alb)
        r['t4_libre'] = 1.14 - 0.10 * off['tsh'][n] + rng.normal(0, 0.06)
        for name, (typ, lo, hi) in OLIGO.items():
            if typ == 'm':
                mid, sd = (lo + hi) / 2, (hi - lo) / 5
                r[OKEY[name]] = max(lo * 0.3, mid + sd * (-0.35 * x_ + 0.8 * off_ol[name][n]) + rng.normal(0, 0.15 * sd))
            else:
                r[OKEY[name]] = max(0.001, hi * 0.3 * np.exp(0.45 * x_ + 0.35 * off_ol[name][n] + rng.normal(0, 0.1)))
        r['carga_metales_idx'] = np.mean([r[OKEY[k]] / OLIGO[k][2] for k, v in OLIGO.items() if v[0] == 't'])
        r['ratio_zn_cu'] = r[OKEY['Zinc']] / r[OKEY['Cobre']]; r['ratio_ca_mg'] = r[OKEY['Calcio']] / r[OKEY['Magnesio']]
        # rendimiento físico / wearables
        r['vo2max_ml_kg_min'] = clip(35 + 7 * Mm - 0.38 * (a - 50) + 4.5 * f_ + rng.normal(0, 1.2), 12, 70)
        r['fuerza_agarre_kg'] = max(8, 25 + 15 * Mm - 0.25 * (a - 50) + 4 * f_ + DIR['grip'][n] + rng.normal(0, 1.5)); r['masa_magra_kg'] = max(25, 43 + 15 * Mm - 0.12 * (a - 50) + 3 * f_ + rng.normal(0, 1.5))
        r['hrv_rmssd_ms'] = np.exp(np.log(38) - 0.014 * (a - 50) + 0.22 * f_ - 0.08 * i_ - 0.03 * (h_est - 5) + rng.normal(0, 0.12))
        r['sueno_horas'] = clip(6.9 + 0.3 * f_ - 0.15 * i_ + 0.12 * (h_sue - 6.5) + rng.normal(0, 0.35), 4, 9); r['pasos_dia'] = np.exp(np.log(7000) + 0.35 * f_ + rng.normal(0, 0.18))
        # anamnesis (hábitos) y síntomas
        r.update(hora_acostarse=h_hor, celular_en_cama=h_cel, sesiones_fuerza_sem=h_fue, min_cardio_sem=h_car, sedentarismo_h_dia=h_sed, ultraprocesados_sem=h_ult,
                 alcohol_sem=h_alc, dieta_mediterranea_score=h_die, tabaquismo=tabaco[n], estres_percibido=h_est, ansiedad_score=h_ans, calidad_sueno=h_sue)
        r['energia'] = clip(6.3 - 0.9 * i_ - 0.5 * m_ + 0.6 * f_ - 0.15 * (h_est - 5) + rng.normal(0, 0.7), 0, 10)
        r['claridad_mental'] = clip(6.5 - 0.5 * i_ + 0.4 * f_ + 0.25 * (h_sue - 6.5) + DIR['clar'][n] + rng.normal(0, 0.7), 0, 10)
        r['dolor'] = clip(2.5 + 0.35 * (h_sed - 8) + 0.5 * (h_est - 5) + 0.5 * i_ + 2.0 * g_f + rng.normal(0, 0.7), 0, 10)
        r['molestias_digestivas'] = clip(1.5 + 3.0 * l_f + 2.0 * g_f + 0.3 * (h_est - 5) + rng.normal(0, 0.6), 0, 10)
        # estático por paciente
        r.update(FAM_ := {k: v[n] for k, v in FAM.items()})
        r['intol_lactosa_detectada'] = int(lac_det[n]); r['intol_gluten_detectada'] = int(glu_det[n])
        if programa[n] == 'PRO':
            r.update(apoe=apoe[n], apoe_e4_carrier=int(e4[n]), mthfr_c677t=mthfr[n], mthfr_tt=int(tt[n]), fto_alelos_riesgo=int(fto[n]), ace_id=ace[n],
                     lct_13910=lct[n], hla_dq2_dq8=int(hla[n]), vdr_foki=vdr[n], cyp1a2_cafeina=cyp[n], gstt1=gstt1[n], prs_metabolico=round(prs[n], 2),
                     prs_cardiovascular=round(prs_card[n], 2), hfe=hfe_lab[n], n_variantes_riesgo=int(nvr[n]), **{k: GL[k][n] for k in GL})
        else:
            r.update(apoe=None, apoe_e4_carrier=None, mthfr_c677t=None, mthfr_tt=None, fto_alelos_riesgo=None, ace_id=None, lct_13910=None, hla_dq2_dq8=None,
                     vdr_foki=None, cyp1a2_cafeina=None, gstt1=None, prs_metabolico=None, prs_cardiovascular=None, hfe=None, n_variantes_riesgo=None, **{k: None for k in GL})
        r.update(condiciones(r, bool(Fm)))
        hall = []
        if glu_det[n]: hall.append('intolerancia al gluten')
        if lac_det[n]: hall.append('intolerancia a la lactosa')
        if r['cond_deficit_vitamina_d']: hall.append('déficit de vitamina D')
        if r['cond_resistencia_insulinica']: hall.append('resistencia a la insulina')
        if r['cond_carga_metales_alta']: hall.append('carga de metales elevada')
        r['hallazgo_principal'] = hall[0] if hall else 'ninguno'; r['n_hallazgos'] = len(hall)
        rows.append(r)
        gm = 3.2 * (0.30 * m_ + 0.25 * i_ + 0.25 * c_ + 0.10 * x_ - 0.10 * f_)
        truth.append(dict(patient_id=r['patient_id'], visit_n=k, z_metabolico=m_, z_inflamatorio=i_, z_cardio=c_, z_minerales=x_, z_fitness=f_,
                          brecha_modificable_real=gm, brecha_genetica_real=gap_gen[n], acelerado_real=int(acelerado[n]),
                          intol_gluten_real=int(intol_glu[n]), intol_lactosa_real=int(intol_lac[n])))
    if (n + 1) % 3000 == 0 or n == N - 1:
        frames.append(pd.DataFrame(rows)); tframes.append(pd.DataFrame(truth)); rows, truth = [], []
    if (n + 1) % 6000 == 0: print(f'  {n + 1} pacientes generados...', flush=True)

df = pd.concat(frames, ignore_index=True).copy(); truth = pd.concat(tframes, ignore_index=True).to_dict('records')
dec = {'homa_ir': 2, 'grasa_corporal_pct': 1, 'imc': 1, 'colesterol_no_hdl': 0, 'nlr': 2, 'ratio_insulina_post_ayunas': 2,
       'ratio_tg_hdl': 2, 'pa_sistolica': 0, 'drom_ucarr': 0, 'pic_indice': 0, 'carga_metales_idx': 3, 'ratio_zn_cu': 2, 'ratio_ca_mg': 2, 'vo2max_ml_kg_min': 1,
       'fuerza_agarre_kg': 1, 'masa_magra_kg': 1, 'hrv_rmssd_ms': 0, 'sueno_horas': 1, 'pasos_dia': 0, 'hora_acostarse': 2, 'min_cardio_sem': 0,
       'sedentarismo_h_dia': 1, 'dieta_mediterranea_score': 1, 'estres_percibido': 1, 'ansiedad_score': 1, 'calidad_sueno': 1, 'energia': 1,
       'claridad_mental': 1, 'dolor': 1, 'molestias_digestivas': 1}
dec.update({a['key']: a['dec'] for a in LAB})   # decimales del catálogo (una sola fuente de verdad)
for c in df.columns:
    if c.startswith('oligo_'): dec[c] = 3 if df[c].max() < 5 else 1
for c, d in dec.items():
    df[c] = df[c].round(d)
    if d == 0 and df[c].notna().all(): df[c] = df[c].astype(int)
# las condiciones se recalculan con los valores redondeados (lo que vería la clínica)
cond = condiciones_vec(df)
for c in cond.columns: df[c] = cond[c]
df['n_condiciones'] = df[[c for c in df.columns if c.startswith('cond_')]].sum(axis=1)
df.insert(1, 'visit_id', [f'V{i+1:06d}' for i in range(len(df))])

# ------------------------------------------------------------------ eventos clínicos previos
EV = [('cirugía ortopédica', .5), ('cirugía abdominal', .5), ('cirugía cardiovascular', .2), ('internación respiratoria', .6), ('internación por infección', .5),
      ('diagnóstico de hipertensión', .5), ('diagnóstico de diabetes tipo 2', .3), ('cirugía de vesícula', .4)]
evp = np.array([w for _, w in EV]) / sum(w for _, w in EV)
ev_rows = []
for n in range(N):
    lam = clip(0.45 + 0.03 * (age0[n] - 50) + 0.15 * (zc[n] + zm[n]), 0.05, 3)
    for _ in range(int(rng.poisson(lam))):
        ev_rows.append(dict(patient_id=f'P{n+1:05d}', tipo_evento=EV[rng.choice(len(EV), p=evp)][0], anio=base_date[n].year - int(rng.integers(1, 16))))
ev = pd.DataFrame(ev_rows)

# ------------------------------------------------------------------ pacientes (estático + embudo)
cons = [base_date[n] for n in range(N)]
est = [cons[n] + timedelta(days=int(rng.integers(2, 15))) for n in range(N)]
integ = [est[n] + timedelta(days=int(rng.integers(5, 26))) for n in range(N)]
pac = pd.DataFrame(dict(patient_id=[f'P{n+1:05d}' for n in range(N)], dni=dnis, nombre=first, apellido=last, sexo=sex, fecha_nacimiento=birth, localidad=city,
                        programa=programa, protocolo=protocolo, adherencia=adh, fecha_consulta=cons, fecha_estudios=est, fecha_integracion=integ,
                        cobertura_anamnesis_pct=clip(rng.normal(88, 8, N), 50, 100).round(0).astype(int),
                        n_eventos_previos=pd.Series([f'P{n+1:05d}' for n in range(N)]).map(ev.patient_id.value_counts()).fillna(0).astype(int).values))
for k, v in FAM.items(): pac[k] = v
pac['intol_lactosa_detectada'] = lac_det; pac['intol_gluten_detectada'] = glu_det
extra = int(round(N / 0.92) - N)   # consultas que no llegaron a los estudios (no están en la cohorte)
embudo = dict(consultas=N + extra, estudios=N, integracion=N, control_6m=int((df.meses_desde_baseline.between(4, 9)).sum()), control_12m=int((df.meses_desde_baseline >= 10).sum()))

df.to_csv(f'{OUT}/visitas_longitudinal.csv', index=False)
pac.to_csv(f'{OUT}/pacientes.csv', index=False)
ev.to_csv(f'{OUT}/eventos_clinicos.csv', index=False)
pd.DataFrame(truth).merge(df[['patient_id', 'visit_n', 'visit_id']], on=['patient_id', 'visit_n']).to_csv(f'{OUT}/solucion_latentes.csv', index=False)
pd.DataFrame([dict(condicion=k, regla=v) for k, v in UMBRALES.items()]).to_csv(f'{OUT}/umbrales_condiciones.csv', index=False)
pd.Series(embudo).to_json(f'{OUT}/embudo.json')
print(df.shape, '| pacientes', N, '| PRO', int((programa == 'PRO').sum()), '| visitas por paciente', df.groupby('patient_id').size().value_counts().sort_index().to_dict())
print('eventos previos:', len(ev), '| embudo:', embudo)
print('prevalencia condiciones (visita 0, %):', (df[df.visit_n == 0][[c for c in df.columns if c.startswith('cond_')]].mean() * 100).round(1).to_dict())
print('detectadas: gluten', int(glu_det.sum()), 'lactosa', int(lac_det.sum()), '| intolerancias reales: gluten', int(intol_glu.sum()), 'lactosa', int(intol_lac.sum()))
