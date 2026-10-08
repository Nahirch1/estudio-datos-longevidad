"""Estudio de Datos de Longevidad: tablero en Streamlit sobre la base SQLite.
Ejecutar:  streamlit run app/app_streamlit.py   (después de correr 06_exportar_bi.py)"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import streamlit as st
import datos

st.set_page_config(page_title='Estudio de Datos de Longevidad', layout='wide')


@st.cache_data
def base():
    return datos.cargar()


D = base()
st.title('Estudio de Datos de Longevidad')
st.caption('Datos 100% sintéticos. Apoyo a la decisión médica, no diagnóstico. Los efectos de los protocolos son parámetros del simulador.')

with st.sidebar:
    st.header('Filtros')
    prog = st.multiselect('Programa', ['BASE', 'PRO'])
    sexo = st.multiselect('Sexo', ['F', 'M'])
    edad = st.multiselect('Grupo etario', ['<40', '40-49', '50-59', '60-69', '70+'])
F = datos.filtrar(D, prog, sexo, edad)
K = datos.kpis(F)

t1, t2, t3, t4, t5 = st.tabs(['Resumen', 'Edad biológica', 'Prevención', 'Paciente', 'Calidad de datos'])

with t1:
    c = st.columns(4)
    c[0].metric('Pacientes', f"{K['pacientes']:,}".replace(',', '.'))
    c[1].metric('Brecha inicial (años)', f"{K['brecha_inicial']:.2f}")
    c[2].metric('% acelerados (2 o más años)', f"{K['pct_acelerados']:.1f}%")
    c[3].metric('Δ brecha 12 m: plan vs estándar', f"{K['d12_plan']:+.2f}", f"estándar {K['d12_control']:+.2f}", delta_color='off')
    e = datos.embudo(F)
    st.plotly_chart(px.bar(e, x='pacientes', y='etapa', orientation='h', title='Embudo (simulado)').update_yaxes(autorange='reversed'))

with t2:
    v0 = F['fact_visita'][F['fact_visita'].visit_n == 0]
    a, b = st.columns(2)
    a.plotly_chart(px.scatter(v0, x='edad_cronologica', y='edad_biologica_modificable', opacity=.5, title='Edad biológica vs. cronológica'))
    b.plotly_chart(px.histogram(v0, x='brecha_modificable', nbins=30, title='Brecha modificable (años)'))
    g = F['dim_genetica_pro']
    if len(g):
        mod = v0.merge(g[['patient_id']], on='patient_id').brecha_modificable.mean()
        st.info(f"Programa PRO ({len(g)} pacientes): aporte genético fijo {g.brecha_genetica_fija.mean():+.2f} años; parte modificable {mod:+.2f} años. La genética no cambia con los hábitos.")
    st.caption('La edad biológica sale de biomarcadores; no es un reloj epigenético.')

with t3:
    st.plotly_chart(px.line(datos.tendencia_brecha(F), x='hito', y='brecha_modificable', color='protocolo', markers=True, title='Brecha media por protocolo'))
    st.dataframe(datos.tabla_protocolos(F), hide_index=True)
    a, b = st.columns(2)
    a.plotly_chart(px.bar(datos.ritmo_por_adherencia(F), x='adherencia', y='ritmo_envejecimiento', title='Ritmo de envejecimiento por adherencia'))
    b.dataframe(datos.condiciones(F), hide_index=True)
    marcador = st.selectbox('Biomarcador', sorted(F['fact_biomarcador'].biomarcador.unique()), index=0)
    st.plotly_chart(px.line(datos.biomarcador(F, marcador), x='meses_desde_baseline', y='valor', color='protocolo', markers=True))
    st.caption('Las diferencias vienen de efectos cargados en el simulador: muestran qué preguntas se podrían responder con datos reales.')

with t4:
    ids = sorted(F['dim_paciente'].patient_id)
    if ids:
        pid = st.selectbox('Paciente', ids)
        p = datos.paciente(F, pid)
        st.write(p['perfil'][['patient_id', 'sexo', 'programa', 'protocolo', 'adherencia', 'segmento']].to_frame().T)
        cols = ['hito', 'meses_desde_baseline', 'edad_cronologica', 'edad_biologica_modificable', 'brecha_modificable', 'score_longevidad', 'score_metabolismo', 'score_inflamacion', 'score_cardiovascular', 'score_detoxificacion', 'score_rendimiento']
        st.dataframe(p['visitas'][cols], hide_index=True)
        if len(p['informe']):
            st.subheader('Informe de integración (borrador para el médico)')
            st.write(p['informe'].drop(columns=['patient_id']).iloc[0])
        if len(p['genetica']):
            st.subheader('Genética (solo programa PRO)')
            st.write(p['genetica'].drop(columns=['patient_id']).iloc[0])
        if len(p['eventos']):
            st.subheader('Eventos clínicos previos')
            st.dataframe(p['eventos'], hide_index=True)

with t5:
    st.dataframe(D['fact_calidad_validacion'], hide_index=True)
    st.dataframe(D['fact_calidad_problemas'], hide_index=True)
    st.caption('Cada valor limpio se comparó con el dato de origen del simulador. El 100% es optimista: con archivos reales aparecerán casos nuevos.')
