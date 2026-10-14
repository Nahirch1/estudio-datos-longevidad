"""Prueba rápida de la capa de datos: python3 tests/test_datos.py (requiere haber corrido 04 y 06).
Compara la base exportada (SQLite/CSV) contra los números que calculó el análisis (resultados/dashboard_data.json)."""
import json, pathlib, sys
RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'app'))
import datos

J = json.loads((RAIZ / 'resultados/dashboard_data.json').read_text(encoding='utf-8'))
K = J['kpi']
d = datos.cargar(); k = datos.kpis(d)
assert k['pacientes'] == K['pacientes'] and k['visitas'] == K['visitas'], (k, K)
assert round(k['brecha_inicial'], 2) == K['brecha_media'] and round(k['pct_acelerados'], 1) == K['pct_acelerados'], (k, K)
assert (round(k['d12_plan'], 2), k['n12_plan']) == (K['d12_plan']['m'], K['d12_plan']['n']), (k, K)
assert (round(k['d12_control'], 2), k['n12_control']) == (K['d12_control']['m'], K['d12_control']['n']), (k, K)
assert round(k['resp6_plan'], 1) == K['resp6_plan']['r'] and round(k['resp6_control'], 1) == K['resp6_control']['r'], (k, K)
f = datos.filtrar(d, programa=['PRO'])
assert datos.kpis(f)['pacientes'] == K['pro'] and len(f['dim_genetica_pro']) == K['pro']
assert len(datos.tendencia_brecha(d)) == 18 and len(datos.tabla_protocolos(d)) == 6 and len(datos.condiciones(d)) == 11
e = J['oper']['embudo']
assert datos.embudo(d).pacientes.tolist() == [e['consultas'], e['estudios'], e['integracion'], e['control_6m'], e['control_12m']]
p = datos.paciente(d, 'P00001'); assert len(p['visitas']) >= 1
# condiciones: los porcentajes de la base (solo guarda presentes) deben coincidir con los del análisis
cb = datos.condiciones(d).set_index('condicion').pct_inicio
for nombre, pct in [(c['condicion'], c['baseline']) for c in J['condiciones']]:
    k_ = {'prediabetes': 'prediabetes', 'resistencia a la insulina': 'resistencia_insulinica', 'dislipidemia': 'dislipidemia', 'presión elevada': 'presion_elevada', 'déficit de vitamina D': 'deficit_vitamina_d',
          'inflamación de bajo grado': 'inflamacion_baja_grado', 'carga de metales alta': 'carga_metales_alta', 'anemia': 'anemia', 'hiperuricemia': 'hiperuricemia',
          'hiperinsulinemia post-carga': 'hiperinsulinemia_postcarga', 'enzimas hepáticas elevadas': 'enzimas_hepaticas_elevadas'}[nombre]
    assert abs(cb[k_] - pct) < 0.11, (nombre, cb[k_], pct)
# insulina: ayunas y post-carga, post-carga medida en ~59% de las visitas
ins = datos.insulina(d); I = J['insulina']
assert abs(float(ins[ins.hito == '0m'].pct_con_post_carga.iloc[0]) - I['medido_pct']['0m']) < 0.11, (ins, I)
# relojes: PhenoAge (C) con la brecha esperada y reloj de biomarcadores
rl = datos.relojes(d).set_index('hito'); assert abs(rl.loc['0m', 'brecha_modificable'] - J['kpi']['brecha_media']) < 0.011
assert J['relojes']['C']['corr_brecha'] > 0.4 and J['relojes']['B']['corr_no_vistos'] > 0.9
# genética: el panel completo (28 marcadores) está en la base y Lp(a) sube con el alelo de riesgo
g = d['dim_genetica_pro']; assert len(g) == K['pro'] and len(d['dim_marcador_genetico']) == 28 and all(c in g.columns for c in d['dim_marcador_genetico'].columna)
lpa = datos.genotipo_vs_biomarcador(d, 'lpa_rs10455872', 'lipoproteina_a').set_index('lpa_rs10455872').media
assert lpa['GG'] > lpa['AG'] > lpa['AA'], lpa
# laboratorio completo: 51 analitos del catálogo + derivados en dim_biomarcador y en fact_laboratorio
import sqlite3
con = sqlite3.connect(d['_db']); cols = {r[1] for r in con.execute('PRAGMA table_info(fact_laboratorio)')}; con.close()
assert len(d['dim_biomarcador']) >= 85 and set(d['dim_biomarcador'].columna) <= cols, set(d['dim_biomarcador'].columna) - cols
assert 'insulina_ayunas' in cols and 'insulina_post_carga' in cols and 'glucosa_post_carga' in cols
print('OK', {a: round(b, 2) for a, b in k.items()})
