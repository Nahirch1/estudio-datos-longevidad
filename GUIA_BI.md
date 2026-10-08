# Guía para armar el tablero en Looker Studio

Looker Studio es gratis y se usa con una cuenta personal de Google (Gmail), no hace falta cuenta de empresa. Funciona desde el navegador en Debian. Las tablas de `bi/looker/` son planas (ya traen los datos del paciente en cada fila), así que no hace falta combinar fuentes. No hay datos personales: solo `patient_id`.

Los pasos y menús pueden cambiar con las versiones de Looker Studio; si algo no coincide, buscá la opción equivalente.

## 1. Cargar los datos (dos opciones)
- **Subir los CSV directo:** en Looker Studio, Crear → Fuente de datos → conector "Carga de archivos" (File Upload). Subí los 10 CSV de `bi/looker/`. El más grande, `lk_biomarcadores.csv`, pesa unos 22 MB; si el conector rechaza ese tamaño, usá la opción siguiente.
- **Google Sheets o BigQuery:** subí los CSV a Google Drive y abrilos como hojas de cálculo, o cargalos en BigQuery (el modo sandbox es gratis y no pide tarjeta).

Los CSV de `bi/looker/` usan **punto decimal** (0.76): el conector de carga de CSV interpreta la coma como separador de miles y rompe los promedios. Al conectar cada fuente, revisá los tipos de campo: `fecha_visita` hay que pasarla a Fecha (AAAA-MM-DD), y los campos numéricos que tienen celdas vacías (`brecha_genetica_fija`, `brecha_total_pro`, `resp_6m`, `resp_12m`, `ritmo_envejecimiento` y los `d_*`) llegan como Texto: cambiales el tipo a Número.

## 2. Campos calculados (los mismos números que `sql/consultas_kpi.sql`)
En `lk_visitas`:
- **Brecha inicial:** `AVG(CASE WHEN visit_n = 0 THEN brecha_modificable END)` → control: 0,33
- **% Acelerados:** `COUNT_DISTINCT(CASE WHEN visit_n = 0 AND brecha_modificable >= 2 THEN patient_id END) / COUNT_DISTINCT(CASE WHEN visit_n = 0 THEN patient_id END)` → control: 21,4%
- **Pacientes:** `COUNT_DISTINCT(patient_id)` → 8.000

En `lk_resultados`:
- **Δ Brecha 12m:** `AVG(d_brecha_modificable_12m)` → control: con plan −0,38 y seguimiento estándar +0,10
- **Δ Longevidad 12m:** `AVG(d_score_longevidad_12m)`
- **% Respondedores 6m:** `AVG(resp_6m)`
- **Ritmo de envejecimiento:** `AVG(ritmo_envejecimiento)`

En `lk_embudo`:
- **Retención 12m:** `SUM(CASE WHEN etapa = 'control_12m' THEN pacientes END) / SUM(CASE WHEN etapa = 'estudios' THEN pacientes END)`

Semáforo: en las tablas de scores, formato condicional ≥55 verde, 40–54 ámbar, <40 rojo.

## 3. Páginas del informe (5)
1. **Resumen:** tarjetas con Pacientes, Brecha inicial, % Acelerados y Retención 12m; embudo (`lk_embudo`); filtros de programa, sexo y grupo etario.
2. **Ficha del paciente:** control de filtro por `patient_id`; línea de edad biológica y cronológica por `meses_desde_baseline`; tabla de semáforos con los 5 `score_*`; hábitos y síntomas por visita; padecimientos (`lk_condiciones`); informe de integración (`lk_informes`); genética (`lk_genetica_pro`).
3. **Edad biológica:** dispersión de edad cronológica contra biológica, histograma de `brecha_modificable` y, para el programa PRO, genética fija contra parte modificable.
4. **Prevención en el tiempo:** brecha media por protocolo en 0, 6 y 12 meses; Δ Longevidad y % Respondedores por protocolo; ritmo por adherencia; cambios de síntomas y hábitos; padecimientos al inicio y a los 12 meses.
5. **Calidad de datos:** `lk_calidad_problemas` y `lk_calidad_validacion`. Muestra el trabajo de ordenar los datos sueltos.

## 4. Textos que van en el informe
- "Datos 100% sintéticos. Los efectos de los protocolos son parámetros del simulador. Apoyo a la decisión médica, no diagnóstico."
- El PIC es un índice genérico (placeholder) y el Oligoscan usa valores ficticios.

## Si no querés depender de ninguna cuenta
`bi/estudio_longevidad.sqlite` tiene las 14 tablas del modelo en estrella y se abre con DBeaver (gratis, para Debian) para correr las consultas de `sql/consultas_kpi.sql`. Herramientas de código abierto como Apache Superset o Metabase se pueden instalar en tu propia máquina y conectarse a esa base; verificá en su documentación el conector de SQLite.

## Alternativa: Power BI
Si algún día tenés una cuenta que lo permita, `bi/estudio_longevidad_modelo.xlsx` (14 tablas relacionables) y `bi/medidas_DAX.md` dejan el modelo listo. Power BI Desktop solo corre en Windows.

## Para el portfolio
Capturas de las 5 páginas en el README, el HTML publicado como vista previa con simulador, y los scripts 01 a 06 en GitHub.
