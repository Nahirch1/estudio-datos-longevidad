"""Genera docs/DICCIONARIO_DATOS.md a partir de bi/estudio_longevidad.sqlite (modelo en estrella).
Por cada tabla: filas y, por columna, tipo, % de vacíos y un ejemplo. Para fact_laboratorio agrega la unidad y la referencia de dim_biomarcador."""
import pathlib, sqlite3
import pandas as pd
b = pathlib.Path(__file__).resolve().parent
con = sqlite3.connect(b / 'bi/estudio_longevidad.sqlite')
tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
dbm = pd.read_sql('SELECT columna, biomarcador, unidad, referencia FROM dim_biomarcador', con).set_index('columna')
DESC = {
    'dim_paciente': 'Una fila por paciente (sin DNI ni nombre: el BI trabaja solo con `patient_id`).',
    'dim_genetica_pro': 'Panel genético completo del ADN Test, una fila por paciente del programa PRO (28 marcadores + 2 puntajes poligénicos).',
    'dim_marcador_genetico': 'Catálogo del panel genético: gen, rsID, área funcional y si el alelo de efecto es de riesgo o protector.',
    'dim_biomarcador': 'Catálogo de todo lo que se mide: analitos de laboratorio, derivados, oligoelementos y otras mediciones, con unidad y referencia.',
    'fact_visita': 'Una fila por visita (0, 6 y 12 meses): edad biológica, brechas, scores, hábitos, síntomas y conteo de analitos fuera de rango.',
    'fact_laboratorio': 'Una fila por visita, una columna por analito (formato ancho). La insulina y la glucosa post-carga solo están en ~59% de las visitas.',
    'fact_condicion': 'Solo las condiciones PRESENTES por visita (el denominador sale de `fact_visita`).',
    'fact_biomarcador_muestra': 'Formato largo de una muestra de 1.500 pacientes, para herramientas que lo piden. El modelo completo en largo tendría ~10 millones de filas.',
    'fact_resultado_paciente': 'Una fila por paciente: cambios a 6 y 12 meses, ritmo de envejecimiento, respondedor.',
}
out = ['# Diccionario de datos', '',
       'Generado automáticamente por `07_generar_diccionario.py` desde `bi/estudio_longevidad.sqlite` (modelo en estrella). Todos los datos son sintéticos. Columnas: nombre, tipo, % de valores vacíos y un ejemplo.', '']
for t in tablas:
    df = pd.read_sql(f'SELECT * FROM {t}', con)
    tipos = {r[1]: r[2] for r in con.execute(f'PRAGMA table_info({t})')}
    out += [f'## `{t}` ({len(df):,} filas)'.replace(',', '.'), '']
    if t in DESC: out += [DESC[t], '']
    lab = t == 'fact_laboratorio'
    out += ['| Columna | Tipo | % vacío | Ejemplo |' + (' Unidad |' if lab else ''), '|---|---|---|---|' + ('---|' if lab else '')]
    for c in df.columns:
        ej = df[c].dropna().iloc[0] if df[c].notna().any() else ''
        ej = str(ej).replace('|', '/')[:60]
        extra = f" {dbm.unidad.get(c, '')} |" if lab else ''
        out.append(f'| `{c}` | {tipos[c]} | {round(100 * df[c].isna().mean(), 1):g} | {ej} |{extra}')
    out.append('')
(b / 'docs/DICCIONARIO_DATOS.md').write_text('\n'.join(out), encoding='utf-8')
print('diccionario:', len(tablas), 'tablas')
