# Diccionario de datos

Generado automáticamente desde `bi/estudio_longevidad.sqlite` (modelo en estrella). Todos los datos son sintéticos. Columnas: nombre, tipo, % de valores vacíos y un ejemplo.

## `dim_dominio` (5 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `dominio` | TEXT | 0 | Metabolismo |
| `columna_score` | TEXT | 0 | score_metabolismo |
| `orden` | INTEGER | 0 | 1 |

## `dim_fecha` (678 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `fecha` | TEXT | 0 | 2025-01-06 |
| `anio` | INTEGER | 0 | 2025 |
| `mes` | INTEGER | 0 | 1 |
| `anio_mes` | TEXT | 0 | 2025-01 |

## `dim_genetica_pro` (2.785 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00002 |
| `apoe` | TEXT | 0 | e3/e3 |
| `apoe_e4_carrier` | REAL | 0 | 0.0 |
| `mthfr_c677t` | TEXT | 0 | CC |
| `fto_alelos_riesgo` | REAL | 0 | 1.0 |
| `ace_id` | TEXT | 0 | II |
| `lct_13910` | TEXT | 0 | TT |
| `hla_dq2_dq8` | REAL | 0 | 0.0 |
| `vdr_foki` | TEXT | 0 | FF |
| `cyp1a2_cafeina` | TEXT | 0 | rápido |
| `gstt1` | TEXT | 0 | presente |
| `prs_metabolico` | REAL | 0 | -0.12 |
| `brecha_genetica_fija` | REAL | 0 | -0.304 |

## `dim_paciente` (8.000 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `sexo` | TEXT | 0 | M |
| `localidad` | TEXT | 0 | San Isidro |
| `programa` | TEXT | 0 | BASE |
| `protocolo` | TEXT | 0 | Suplementación y minerales |
| `adherencia` | TEXT | 0 | Media |
| `cobertura_anamnesis_pct` | INTEGER | 0 | 93 |
| `n_eventos_previos` | INTEGER | 0 | 1 |
| `fam_cardiovascular` | INTEGER | 0 | 1 |
| `fam_diabetes` | INTEGER | 0 | 0 |
| `fam_cancer` | INTEGER | 0 | 1 |
| `fam_neurodegenerativa` | INTEGER | 0 | 0 |
| `intol_lactosa_detectada` | INTEGER | 0 | 0 |
| `intol_gluten_detectada` | INTEGER | 0 | 0 |
| `edad_inicial` | REAL | 0 | 29.9 |
| `grupo_etario` | TEXT | 0 | <40 |
| `segmento` | TEXT | 0 | Perfil óptimo |
| `tiene_plan` | INTEGER | 0 | 1 |
| `intol_gluten_real` | INTEGER | 0 | 0 |
| `intol_lactosa_real` | INTEGER | 0 | 0 |

## `dim_protocolo` (6 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `protocolo` | TEXT | 0 | Seguimiento estándar |
| `orden` | INTEGER | 0 | 1 |
| `tiene_plan` | INTEGER | 0 | 0 |

## `fact_biomarcador` (806.793 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V00001 |
| `patient_id` | TEXT | 0 | P00001 |
| `biomarcador` | TEXT | 0 | glucosa |
| `valor` | REAL | 0 | 78.0 |
| `categoria` | TEXT | 0 | Metabólico |
| `unidad` | TEXT | 0 | mg/dL |

## `fact_calidad_problemas` (31 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `problema` | TEXT | 0 | fechas_como_texto |
| `cantidad` | INTEGER | 0 | 7137 |

## `fact_calidad_validacion` (8 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `grupo` | TEXT | 0 | Laboratorio (16 analitos) |
| `comparados` | INTEGER | 0 | 8259 |
| `correctos` | INTEGER | 0 | 8259 |
| `exactitud` | REAL | 0 | 100.0 |

## `fact_condicion` (144.809 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V00001 |
| `patient_id` | TEXT | 0 | P00001 |
| `condicion` | TEXT | 0 | prediabetes |
| `presente` | INTEGER | 0 | 0 |

## `fact_embudo` (5 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `etapa` | TEXT | 0 | consultas |
| `orden` | INTEGER | 0 | 1 |
| `pacientes` | INTEGER | 0 | 8696 |

## `fact_evento_previo` (4.479 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `tipo_evento` | TEXT | 0 | internación respiratoria |
| `anio` | INTEGER | 0 | 2013 |

## `fact_informe_integracion` (8.000 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `segmento` | TEXT | 0 | Perfil óptimo |
| `prioridades` | TEXT | 26 | Detoxificación |
| `habitos_a_conversar` | TEXT | 20 | pocas sesiones de fuerza; estrés percibi |
| `genetica_para_evaluar` | TEXT | 68 | GSTT1 nulo: observar detoxificación |
| `padecimientos_detectados` | TEXT | 45 | dislipidemia |
| `hallazgo` | TEXT | 0 | ninguno |

## `fact_resultado_paciente` (8.000 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `brecha_0` | REAL | 0 | -2.475223364650414 |
| `longevidad_0` | REAL | 0 | 62.71455008137527 |
| `d_brecha_modificable_6m` | REAL | 13 | 0.7661460642932976 |
| `d_brecha_modificable_12m` | REAL | 28 | 0.4604584847260057 |
| `d_score_longevidad_6m` | REAL | 13 | -4.238801671585186 |
| `d_score_longevidad_12m` | REAL | 28 | -3.13183219868008 |
| `d_n_condiciones_12m` | REAL | 28 | 0.0 |
| `d_energia_12m` | REAL | 28 | -0.7000000000000002 |
| `d_dolor_12m` | REAL | 28 | -1.2000000000000002 |
| `d_claridad_mental_12m` | REAL | 28 | -0.5 |
| `d_molestias_digestivas_12m` | REAL | 28 | 0.0 |
| `d_ultraprocesados_sem_12m` | REAL | 28 | 0.0 |
| `d_sesiones_fuerza_sem_12m` | REAL | 28 | 1.0 |
| `d_estres_percibido_12m` | REAL | 28 | -0.7000000000000002 |
| `d_calidad_sueno_12m` | REAL | 28 | 0.2000000000000001 |
| `ritmo_envejecimiento` | REAL | 10 | 1.5660810077393132 |
| `resp_6m` | REAL | 13 | 0.0 |
| `resp_12m` | REAL | 28 | 0.0 |
| `grp_gluten` | TEXT | 92 | Detectada y con plan |
| `grp_lactosa` | TEXT | 82 | Detectada y con plan |

## `fact_visita` (20.687 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V00001 |
| `patient_id` | TEXT | 0 | P00001 |
| `visit_n` | INTEGER | 0 | 0 |
| `hito` | TEXT | 0 | 0m |
| `meses_desde_baseline` | REAL | 0 | 0.0 |
| `fecha_visita` | TEXT | 0 | 2025-02-06 |
| `edad_cronologica` | REAL | 0 | 29.9 |
| `edad_biologica_modificable` | REAL | 0 | 27.424776635349584 |
| `brecha_modificable` | REAL | 0 | -2.475223364650414 |
| `brecha_genetica_fija` | REAL | 65 | -0.304 |
| `brecha_total_pro` | REAL | 65 | -0.1361579025913825 |
| `score_longevidad` | REAL | 0 | 62.71455008137527 |
| `score_metabolismo` | REAL | 0 | 74.4388150269255 |
| `score_inflamacion` | REAL | 0 | 53.70514781607905 |
| `score_cardiovascular` | REAL | 0 | 67.25872717391096 |
| `score_detoxificacion` | REAL | 0 | 39.35131299224445 |
| `score_rendimiento` | REAL | 0 | 79.54396152226607 |
| `n_condiciones` | INTEGER | 0 | 0 |
| `alerta_metabolica_temprana` | INTEGER | 0 | 0 |
| `celular_en_cama` | INTEGER | 0 | 0 |
| `sesiones_fuerza_sem` | INTEGER | 0 | 1 |
| `min_cardio_sem` | INTEGER | 0 | 179 |
| `sedentarismo_h_dia` | REAL | 0 | 5.3 |
| `ultraprocesados_sem` | INTEGER | 0 | 1 |
| `alcohol_sem` | INTEGER | 0 | 1 |
| `dieta_mediterranea_score` | REAL | 0 | 5.9 |
| `tabaquismo` | TEXT | 0 | Nunca |
| `estres_percibido` | REAL | 0 | 7.4 |
| `ansiedad_score` | REAL | 0 | 7.0 |
| `calidad_sueno` | REAL | 0 | 6.4 |
| `sueno_horas` | REAL | 0 | 8.4 |
| `hora_acostarse` | REAL | 0 | 21.56 |
| `energia` | REAL | 0 | 8.1 |
| `claridad_mental` | REAL | 0 | 8.1 |
| `dolor` | REAL | 0 | 1.9 |
| `molestias_digestivas` | REAL | 0 | 2.8 |
| `hallazgo_principal` | TEXT | 0 | ninguno |
