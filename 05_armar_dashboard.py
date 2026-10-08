"""Inserta resultados/dashboard_data.json y el contexto de Argentina en la plantilla HTML."""
import json, pathlib
b = pathlib.Path(__file__).parent
data = json.loads((b/'resultados/dashboard_data.json').read_text(encoding='utf-8'))
ctx = dict(
 aviso='Contexto público para dimensionar el problema. No prueba demanda por medicina preventiva: el embudo y la retención de este tablero son simulados.',
 items=[
  dict(titulo='Población que envejece.', texto='La esperanza de vida al nacer en 2019 era 80,2 años en mujeres y 74,4 en hombres, y el peso de los mayores de 75 entre los mayores de 60 pasó de 23,7% a 30,3%.', fuente='INDEC, dosier de personas mayores', url='https://www.indec.gob.ar/ftp/cuadros/poblacion/dosier_personas_mayores_2026.pdf'),
  dict(titulo='Índice de envejecimiento.', texto='El Censo 2022 registró el mayor aumento en 50 años: 53 mayores de 65 cada 100 menores de 15 contra 40 en el censo anterior, y 117 en CABA.', fuente='Infobae, sobre el Censo 2022', url='https://www.infobae.com/politica/2023/11/29/censo-2022-el-indice-de-envejecimiento-registro-el-aumento-mas-alto-en-los-ultimos-50-anos/'),
  dict(titulo='Gasto de bolsillo en salud.', texto='Cerca del 18% del gasto en salud se paga directamente (dato de 2015), frente a cerca de 30% en América Latina. Es un indicio de pago directo, no una medida de interés por prevención.', fuente='Fundar, gasto de bolsillo en salud', url='https://fund.ar/wp-content/uploads/2022/05/Fundar-El_gasto_de_bolsillo_en_salud_como_indicador_clave.pdf'),
 ])
t = (b/'plantilla_dashboard.html').read_text(encoding='utf-8')
t = t.replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('/*CTX*/', json.dumps(ctx, ensure_ascii=False))
(b/'dashboard_estudio_datos_longevidad.html').write_text(t, encoding='utf-8')
print('ok', len(t)//1024, 'KB')
