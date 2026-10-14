# Estudio de Datos de Longevidad

> **Esto es una demostración de método, no un hallazgo.** Todos los datos son sintéticos y los efectos de los protocolos son parámetros de mi simulador. Armé este proyecto para mostrar *cómo* trabajaría como analista de datos en una clínica de medicina preventiva —del dato sucio a la decisión—, no para probar que un tratamiento funcione. Más pacientes simulados no agregan evidencia: los 42.000 son una prueba de escala del proceso (volumen, tiempos de corrida, tamaño de las tablas), y mucho más grande que lo que tendría una clínica real.

Lo hice por iniciativa propia, a partir del tipo de trabajo analítico que hace una clínica de longevidad. Soy Nahir Ramón Chambi, analista de datos en Mendoza (SQL, BigQuery, dbt, Python), y este es mi proyecto de portfolio.

## La pregunta
¿Cómo se ve, con datos ordenados, la diferencia entre un plan preventivo y un seguimiento estándar? ¿A qué pacientes conviene priorizar y dónde se pierde el resultado? En [`docs/DECISIONES.md`](docs/DECISIONES.md) traduje cada indicador a una decisión posible y a cómo se vería si estuviera mal.

## Qué hice
1. **Cohorte sintética de 42.000 pacientes** con visitas a 0, 6 y 12 meses (108.101 visitas). Cada persona es distinta: hábitos, genética (solo programa PRO, panel de 28 marcadores), antecedentes familiares e intolerancias, un perfil propio por dominio (metabolismo, inflamación, cardiovascular, minerales, rendimiento), adherencia propia y una **respuesta individual al protocolo**: algunos responden mucho, otros poco y alrededor del 10 % casi nada. Hay también eventos intercurrentes en algún control y estacionalidad de la vitamina D. El laboratorio abarca **51 analitos** (hemograma completo con fórmula, química, función hepática y renal, iones, tiroides, lípidos con ApoB y Lp(a), vitaminas, oligoelementos) más los cálculos derivados. La **insulina se mide en ayunas y a las 2 horas de una carga de glucosa**, esta última solo en ~59 % de las visitas y no al azar (se pidió más cuando el HOMA-IR ya era alto), así que no se imputa.
2. **Datos crudos y sucios, sobre una muestra de 500 pacientes** (13 Excel de dos laboratorios y 51 PDF, con fechas ambiguas y de dos dígitos, DNI en formatos distintos, decimales con coma, resultados censurados como «Mayor a 90», unidades mezcladas, genotipos heterocigotas invertidos y duplicados). Los limpié con Python (pandas, pdfplumber), recalculé el eGFR con CKD-EPI 2021 y validé contra el origen: 99,8 a 100 % en casi todos los grupos y 96,0 % en identidad y plan. Es una validación optimista, porque los errores los inyecté yo. El análisis posterior usa la cohorte completa, sin pasar por ese circuito.
3. **Edad biológica** con tres relojes: A (predice la edad cronológica), B (calibrado con una referencia simulada en el 25 % de los pacientes) y C (**PhenoAge**, la fórmula publicada de Levine 2018, con 9 biomarcadores de rutina). Separada en parte genética fija y parte modificable. Sumé un Score de Longevidad, segmentos (K-Means) y hojas de ruta.
4. **Modelo en estrella** (`dim_*`, `fact_*`) en CSV, SQLite y un Excel de muestra (1.500 pacientes), con 13 consultas SQL de indicadores que verifiqué contra el tablero. A esta escala el laboratorio va en una tabla ancha (una fila por visita) en lugar de una tabla larga de ~10 millones de filas. El diccionario está en [`docs/DICCIONARIO_DATOS.md`](docs/DICCIONARIO_DATOS.md).
5. **Tablero en Apache Superset sobre Linux**, creado por código a través de su API REST (`superset/`), sin armar nada a mano.

## Resultados de control (datos sintéticos)
| Indicador | Valor |
|---|---|
| Pacientes / visitas | 42.000 / 108.101 |
| Brecha inicial media (edad biológica − cronológica) | 0,70 años |
| Pacientes con 2 o más años de aceleración | 27,4 % |
| Δ brecha a 12 meses, plan vs. estándar | −0,33 (n=25.202) vs. +0,17 (n=4.524) |
| Respondedores a 6 meses, plan vs. estándar | 33,3 % vs. 11,1 % |
| Con plan y adherencia alta, sin mejora de la brecha a 12 meses | 20,1 % |
| Hiperinsulinemia a las 2 h con insulina en ayunas normal (entre quienes tienen las dos mediciones) | 9,2 % |

## Capturas
![Tablero](docs/capturas/tablero_completo.jpg)

## Cómo correrlo
Los datos no se suben al repositorio: se generan con una semilla fija (el proceso completo tarda unos 10 minutos con 42.000 pacientes; el SQLite pesa ~150 MB).
```
python3 -m venv .venv-datos && . .venv-datos/bin/activate
pip install -r requirements.txt
./ejecutar_todo.sh              # cohorte, fuentes sucias, limpieza, modelos, SQLite y pruebas
cd superset
./instalar.sh                   # una sola vez
./iniciar.sh                    # Superset en http://localhost:8088
./cargar_tablero.sh             # en otra terminal: crea conexión, datasets, gráficos y tablero
```
Detalles y errores comunes en [`superset/README_SUPERSET.md`](superset/README_SUPERSET.md). Comparé otras herramientas que corren en Linux en [`docs/ALTERNATIVAS_LINUX.md`](docs/ALTERNATIVAS_LINUX.md).

## Contexto público de Argentina
Lo uso para dimensionar el problema, no para probar demanda. La esperanza de vida al nacer en 2019 era de 80,2 años en mujeres y 74,4 en hombres, y el peso de los mayores de 75 entre los mayores de 60 pasó de 23,7 % a 30,3 % ([INDEC](https://www.indec.gob.ar/ftp/cuadros/poblacion/dosier_personas_mayores_2026.pdf)). El Censo 2022 registró 53 mayores de 65 cada 100 menores de 15, contra 40 en el censo anterior ([Infobae](https://www.infobae.com/politica/2023/11/29/censo-2022-el-indice-de-envejecimiento-registro-el-aumento-mas-alto-en-los-ultimos-50-anos/)). Cerca del 18 % del gasto en salud es de bolsillo, dato de 2015 ([Fundar](https://fund.ar/wp-content/uploads/2022/05/Fundar-El_gasto_de_bolsillo_en_salud_como_indicador_clave.pdf)). El embudo y la retención de mi tablero son simulados.

## Límites que prefiero decir yo
- Los efectos de los protocolos son parámetros del simulador: ilustran el método, no prueban eficacia. Que el plan "gane" es consecuencia de cómo lo programé.
- La edad biológica sale de biomarcadores; no es un reloj epigenético. El Reloj A es débil (correlación 0,32 con la brecha simulada), el B es casi perfecto (0,99) porque el simulador es simple, y PhenoAge llega a 0,66 en parte por construcción, ya que el simulador mueve los mismos biomarcadores que esa fórmula usa. Los segmentos se separan poco (silhouette 0,17).
- La limpieza se probó sobre una muestra de 500 pacientes con errores que inyecté yo; con datos reales la exactitud sería menor.
- El panel genético y sus asociaciones con los biomarcadores (por ejemplo Lp(a) según el genotipo LPA) son parámetros que cargué en el simulador: muestran cómo se leería el panel, no evidencia clínica. Las frecuencias alélicas son aproximadas.
- La insulina post-carga falta en ~41 % de las visitas y no al azar; solo se comparan casos con las dos mediciones.
- PIC y Oligoscan son marcadores de posición: formatos, valores y genotipos ficticios.
- Con datos reales haría falta consentimiento y acceso restringido (Ley 25.326). Es apoyo a la decisión médica, no diagnóstico.

## Stack
Python (pandas, pdfplumber, scikit-learn), SQL/SQLite con modelo en estrella, Apache Superset (API REST), Linux Debian. Elegí herramientas gratuitas a propósito: es el stack que puede sostener una startup en etapa temprana.
