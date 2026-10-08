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
assert len(datos.tendencia_brecha(d)) == 18 and len(datos.tabla_protocolos(d)) == 6 and len(datos.condiciones(d)) == 7
e = J['oper']['embudo']
assert datos.embudo(d).pacientes.tolist() == [e['consultas'], e['estudios'], e['integracion'], e['control_6m'], e['control_12m']]
p = datos.paciente(d, 'P00001'); assert len(p['visitas']) >= 1
print('OK', {a: round(b, 2) for a, b in k.items()})
