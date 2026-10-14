# Diccionario de datos

Generado automáticamente por `07_generar_diccionario.py` desde `bi/estudio_longevidad.sqlite` (modelo en estrella). Todos los datos son sintéticos. Columnas: nombre, tipo, % de valores vacíos y un ejemplo.

## `dim_biomarcador` (85 filas)

Catálogo de todo lo que se mide: analitos de laboratorio, derivados, oligoelementos y otras mediciones, con unidad y referencia.

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `columna` | TEXT | 0 | glucosa_post_carga |
| `biomarcador` | TEXT | 0 | Glucemia 2 h post carga (75 g) |
| `categoria` | TEXT | 0 | Metabólico |
| `unidad` | TEXT | 0 | mg/dL |
| `referencia` | TEXT | 40 | < 140 |
| `ref_bajo` | REAL | 55.3 | 70.0 |
| `ref_alto` | REAL | 42.4 | 139.9 |
| `derivado` | INTEGER | 0 | 0 |

## `dim_dominio` (5 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `dominio` | TEXT | 0 | Metabolismo |
| `columna_score` | TEXT | 0 | score_metabolismo |
| `orden` | INTEGER | 0 | 1 |

## `dim_fecha` (1.372 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `fecha` | TEXT | 0 | 2023-01-09 |
| `anio` | INTEGER | 0 | 2023 |
| `mes` | INTEGER | 0 | 1 |
| `anio_mes` | TEXT | 0 | 2023-01 |

## `dim_genetica_pro` (14.647 filas)

Panel genético completo del ADN Test, una fila por paciente del programa PRO (28 marcadores + 2 puntajes poligénicos).

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00002 |
| `apoe` | TEXT | 0 | e3/e4 |
| `apoe_e4_carrier` | REAL | 0 | 1.0 |
| `mthfr_c677t` | TEXT | 0 | CT |
| `mthfr_tt` | REAL | 0 | 0.0 |
| `fto_alelos_riesgo` | REAL | 0 | 1.0 |
| `ace_id` | TEXT | 0 | II |
| `lct_13910` | TEXT | 0 | CC |
| `hla_dq2_dq8` | REAL | 0 | 1.0 |
| `vdr_foki` | TEXT | 0 | Ff |
| `cyp1a2_cafeina` | TEXT | 0 | lento |
| `gstt1` | TEXT | 0 | nulo |
| `mthfr_a1298c` | TEXT | 0 | AC |
| `comt_val158met` | TEXT | 0 | AG |
| `tcf7l2` | TEXT | 0 | CT |
| `pparg_pro12ala` | TEXT | 0 | CG |
| `lpa_rs10455872` | TEXT | 0 | AA |
| `chr9p21` | TEXT | 0 | AG |
| `cetp_taqib` | TEXT | 0 | AG |
| `sod2_ala16val` | TEXT | 0 | CC |
| `gpx1_pro198leu` | TEXT | 0 | CC |
| `gc_vitd` | TEXT | 0 | GG |
| `mc4r` | TEXT | 0 | TT |
| `actn3` | TEXT | 0 | RX |
| `bdnf_val66met` | TEXT | 0 | AG |
| `il6_174` | TEXT | 0 | CC |
| `tnf_308` | TEXT | 0 | AG |
| `foxo3` | TEXT | 0 | TT |
| `nos3_glu298asp` | TEXT | 0 | GT |
| `fut2_b12` | TEXT | 0 | GG |
| `hfe` | TEXT | 0 | sin variantes |
| `prs_metabolico` | REAL | 0 | 1.15 |
| `prs_cardiovascular` | REAL | 0 | -0.22 |
| `n_variantes_riesgo` | REAL | 0 | 13.0 |
| `brecha_genetica_fija` | REAL | 0 | 1.12 |

## `dim_marcador_genetico` (28 filas)

Catálogo del panel genético: gen, rsID, área funcional y si el alelo de efecto es de riesgo o protector.

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `columna` | TEXT | 0 | apoe |
| `gen` | TEXT | 0 | APOE |
| `rsid` | TEXT | 0 | rs429358/rs7412 |
| `area` | TEXT | 0 | Riesgo cardiovascular y neurodegenerativo |
| `sentido` | TEXT | 32.1 | riesgo |

## `dim_paciente` (42.000 filas)

Una fila por paciente (sin DNI ni nombre: el BI trabaja solo con `patient_id`).

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `sexo` | TEXT | 0 | M |
| `localidad` | TEXT | 0 | Pilar |
| `programa` | TEXT | 0 | BASE |
| `protocolo` | TEXT | 0 | Combinado integral |
| `adherencia` | TEXT | 0 | Baja |
| `cobertura_anamnesis_pct` | INTEGER | 0 | 75 |
| `n_eventos_previos` | INTEGER | 0 | 0 |
| `fam_cardiovascular` | INTEGER | 0 | 1 |
| `fam_diabetes` | INTEGER | 0 | 1 |
| `fam_cancer` | INTEGER | 0 | 0 |
| `fam_neurodegenerativa` | INTEGER | 0 | 0 |
| `intol_lactosa_detectada` | INTEGER | 0 | 0 |
| `intol_gluten_detectada` | INTEGER | 0 | 0 |
| `edad_inicial` | REAL | 0 | 59.8 |
| `grupo_etario` | TEXT | 0 | 60-69 |
| `segmento` | TEXT | 0 | Foco: cardiovascular + metabolismo |
| `tiene_plan` | INTEGER | 0 | 1 |
| `intol_gluten_real` | INTEGER | 0 | 0 |
| `intol_lactosa_real` | INTEGER | 0 | 0 |

## `dim_protocolo` (6 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `protocolo` | TEXT | 0 | Seguimiento estándar |
| `orden` | INTEGER | 0 | 1 |
| `tiene_plan` | INTEGER | 0 | 0 |

## `fact_biomarcador_muestra` (322.336 filas)

Formato largo de una muestra de 1.500 pacientes, para herramientas que lo piden. El modelo completo en largo tendría ~10 millones de filas.

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V000046 |
| `patient_id` | TEXT | 0 | P00019 |
| `columna` | TEXT | 0 | glucosa_post_carga |
| `valor` | REAL | 0 | 144.0 |
| `categoria` | TEXT | 0 | Metabólico |

## `fact_calidad_problemas` (50 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `problema` | TEXT | 0 | dni_formatos_distintos |
| `cantidad` | INTEGER | 0 | 39542 |

## `fact_calidad_validacion` (10 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `grupo` | TEXT | 0 | Laboratorio: química, lípidos y hormonas (35 analitos) |
| `comparados` | INTEGER | 0 | 43537 |
| `correctos` | INTEGER | 0 | 43537 |
| `exactitud` | REAL | 0 | 100.0 |

## `fact_condicion` (158.334 filas)

Solo las condiciones PRESENTES por visita (el denominador sale de `fact_visita`).

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V000002 |
| `patient_id` | TEXT | 0 | P00001 |
| `condicion` | TEXT | 0 | prediabetes |
| `presente` | INTEGER | 0 | 1 |

## `fact_embudo` (5 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `etapa` | TEXT | 0 | consultas |
| `orden` | INTEGER | 0 | 1 |
| `pacientes` | INTEGER | 0 | 45652 |

## `fact_evento_previo` (24.099 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00003 |
| `tipo_evento` | TEXT | 0 | internación por infección |
| `anio` | INTEGER | 0 | 2014 |

## `fact_informe_integracion` (42.000 filas)

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `segmento` | TEXT | 0 | Foco: cardiovascular + metabolismo |
| `prioridades` | TEXT | 26.2 | Metabolismo, Cardiovascular, Detoxificación |
| `habitos_a_conversar` | TEXT | 19.7 | usa el celular en la cama |
| `genetica_para_evaluar` | TEXT | 65.9 | portador APOE e4: vigilar perfil cardiovascular y sueño; pos |
| `padecimientos_detectados` | TEXT | 37.9 | dislipidemia, presión elevada |
| `hallazgo` | TEXT | 0 | ninguno |

## `fact_laboratorio` (108.101 filas)

Una fila por visita, una columna por analito (formato ancho). La insulina y la glucosa post-carga solo están en ~59% de las visitas.

| Columna | Tipo | % vacío | Ejemplo | Unidad |
|---|---|---|---|---|
| `visit_id` | TEXT | 0 | V000001 |  |
| `patient_id` | TEXT | 0 | P00001 |  |
| `glucosa_post_carga` | REAL | 41.6 | 163.0 | mg/dL |
| `glucosa` | INTEGER | 0 | 93 | mg/dL |
| `hba1c` | REAL | 0 | 5.6 | % |
| `insulina_post_carga` | REAL | 41.6 | 71.4 | µU/mL |
| `insulina_ayunas` | REAL | 0 | 9.6 | µU/mL |
| `colesterol_total` | INTEGER | 0 | 219 | mg/dL |
| `hdl` | INTEGER | 0 | 32 | mg/dL |
| `ldl` | INTEGER | 0 | 159 | mg/dL |
| `trigliceridos` | INTEGER | 0 | 140 | mg/dL |
| `apob` | INTEGER | 0 | 114 | mg/dL |
| `lipoproteina_a` | INTEGER | 0 | 20 | mg/dL |
| `pcr_us` | REAL | 0 | 1.21 | mg/L |
| `homocisteina` | REAL | 0 | 13.1 | µmol/L |
| `ferritina` | INTEGER | 0 | 179 | ng/mL |
| `vitamina_d` | REAL | 0 | 20.8 | ng/mL |
| `b12` | INTEGER | 0 | 157 | pg/mL |
| `tsh` | REAL | 0 | 1.77 | µUI/mL |
| `t4_libre` | REAL | 0 | 1.17 | ng/dL |
| `hematocrito` | REAL | 0 | 46.7 | % |
| `eritrocitos` | REAL | 0 | 5.09 | 10^12/L |
| `hemoglobina` | REAL | 0 | 15.5 | g/dL |
| `vcm` | INTEGER | 0 | 92 | fL |
| `hcm` | REAL | 0 | 30.4 | pg |
| `chcm` | REAL | 0 | 33.2 | g/dL |
| `ade_cv` | REAL | 0 | 12.9 | % |
| `ade_sd` | REAL | 0 | 41.0 | fL |
| `leucocitos` | REAL | 0 | 5.9 | 10^9/L |
| `neutrofilos_pct` | REAL | 0 | 59.2 | % |
| `linfocitos_pct` | REAL | 0 | 32.7 | % |
| `monocitos_pct` | REAL | 0 | 6.0 | % |
| `eosinofilos_pct` | REAL | 0 | 1.6 | % |
| `basofilos_pct` | REAL | 0 | 0.4 | % |
| `plaquetas` | INTEGER | 0 | 206 | 10^9/L |
| `vpm` | REAL | 0 | 10.6 | fL |
| `alt` | INTEGER | 0 | 31 | U/L |
| `ast` | INTEGER | 0 | 37 | U/L |
| `fosfatasa_alcalina` | INTEGER | 0 | 82 | U/L |
| `ggt` | INTEGER | 0 | 33 | U/L |
| `bilirrubina_indirecta` | REAL | 0 | 0.48 | mg/dL |
| `bilirrubina_directa` | REAL | 0 | 0.2 | mg/dL |
| `bilirrubina_total` | REAL | 0 | 0.68 | mg/dL |
| `proteinas_totales` | REAL | 0 | 69.6 | g/L |
| `relacion_alb_glob` | REAL | 0 | 1.95 | relación |
| `albumina` | REAL | 0 | 46.0 | g/L |
| `urea` | REAL | 0 | 0.46 | g/L |
| `creatinina` | REAL | 0 | 1.04 | mg/dL |
| `egfr` | INTEGER | 0 | 82 | ml/min/1,73 m² |
| `acido_urico` | REAL | 0 | 5.9 | mg/dL |
| `sodio` | INTEGER | 0 | 142 | mEq/L |
| `potasio` | REAL | 0 | 4.0 | mEq/L |
| `cloro` | INTEGER | 0 | 106 | mEq/L |
| `homa_ir` | REAL | 0 | 2.21 | índice |
| `ratio_tg_hdl` | REAL | 0 | 4.37 | índice |
| `colesterol_no_hdl` | INTEGER | 0 | 187 | mg/dL |
| `nlr` | REAL | 0 | 1.81 | índice |
| `ratio_insulina_post_ayunas` | REAL | 41.6 | 5.69 | índice |
| `oligo_calcio` | REAL | 0 | 86.5 | valor Oligoscan (ficticio) |
| `oligo_magnesio` | REAL | 0 | 36.9 | valor Oligoscan (ficticio) |
| `oligo_sodio` | REAL | 0 | 834.2 | valor Oligoscan (ficticio) |
| `oligo_potasio` | REAL | 0 | 373.3 | valor Oligoscan (ficticio) |
| `oligo_zinc` | REAL | 0 | 135.9 | valor Oligoscan (ficticio) |
| `oligo_cobre` | REAL | 0 | 14.5 | valor Oligoscan (ficticio) |
| `oligo_hierro` | REAL | 0 | 28.9 | valor Oligoscan (ficticio) |
| `oligo_selenio` | REAL | 0 | 1.131 | valor Oligoscan (ficticio) |
| `oligo_manganeso` | REAL | 0 | 0.127 | valor Oligoscan (ficticio) |
| `oligo_mercurio` | REAL | 0 | 0.405 | valor Oligoscan (ficticio) |
| `oligo_plomo` | REAL | 0 | 0.684 | valor Oligoscan (ficticio) |
| `oligo_cadmio` | REAL | 0 | 0.062 | valor Oligoscan (ficticio) |
| `oligo_aluminio` | REAL | 0 | 6.1 | valor Oligoscan (ficticio) |
| `oligo_arsenico` | REAL | 0 | 0.104 | valor Oligoscan (ficticio) |
| `oligo_niquel` | REAL | 0 | 0.409 | valor Oligoscan (ficticio) |
| `drom_ucarr` | INTEGER | 0 | 274 | U.CARR |
| `pic_indice` | INTEGER | 0 | 39 | índice |
| `carga_metales_idx` | REAL | 0 | 0.555 | índice |
| `ratio_zn_cu` | REAL | 0 | 9.36 | índice |
| `ratio_ca_mg` | REAL | 0 | 2.35 | índice |
| `pa_sistolica` | INTEGER | 0 | 137 | mmHg |
| `grasa_corporal_pct` | REAL | 0 | 27.9 | % |
| `imc` | REAL | 0 | 28.7 | kg/m² |
| `masa_magra_kg` | REAL | 0 | 55.0 | kg |
| `vo2max_ml_kg_min` | REAL | 0 | 33.9 | ml/kg/min |
| `fuerza_agarre_kg` | REAL | 0 | 36.1 | kg |
| `hrv_rmssd_ms` | INTEGER | 0 | 31 | ms |
| `pasos_dia` | INTEGER | 0 | 6700 | pasos |
| `phenoage` | REAL | 0 | 52.1259665140952 | años |

## `fact_resultado_paciente` (42.000 filas)

Una fila por paciente: cambios a 6 y 12 meses, ritmo de envejecimiento, respondedor.

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `patient_id` | TEXT | 0 | P00001 |
| `brecha_0` | REAL | 0 | 2.8044782594731084 |
| `longevidad_0` | REAL | 0 | 39.22664879822472 |
| `d_brecha_modificable_6m` | REAL | 13.4 | 0.4369655051627261 |
| `d_brecha_modificable_12m` | REAL | 29.2 | -0.0756692068875719 |
| `d_score_longevidad_6m` | REAL | 13.4 | -1.795723768317501 |
| `d_score_longevidad_12m` | REAL | 29.2 | 0.1480656769694377 |
| `d_n_condiciones_12m` | REAL | 29.2 | 4.0 |
| `d_energia_12m` | REAL | 29.2 | 1.9 |
| `d_dolor_12m` | REAL | 29.2 | -0.1 |
| `d_claridad_mental_12m` | REAL | 29.2 | -0.0999999999999996 |
| `d_molestias_digestivas_12m` | REAL | 29.2 | -0.7 |
| `d_ultraprocesados_sem_12m` | REAL | 29.2 | 1.0 |
| `d_sesiones_fuerza_sem_12m` | REAL | 29.2 | -1.0 |
| `d_estres_percibido_12m` | REAL | 29.2 | -1.0999999999999996 |
| `d_calidad_sueno_12m` | REAL | 29.2 | 0.7000000000000011 |
| `ritmo_envejecimiento` | REAL | 10 | 0.8944787511359391 |
| `resp_6m` | REAL | 13.4 | 0.0 |
| `resp_12m` | REAL | 29.2 | 0.0 |
| `grp_gluten` | TEXT | 92.3 | Detectada y con plan |
| `grp_lactosa` | TEXT | 81.7 | No detectada |

## `fact_visita` (108.101 filas)

Una fila por visita (0, 6 y 12 meses): edad biológica, brechas, scores, hábitos, síntomas y conteo de analitos fuera de rango.

| Columna | Tipo | % vacío | Ejemplo |
|---|---|---|---|
| `visit_id` | TEXT | 0 | V000001 |
| `patient_id` | TEXT | 0 | P00001 |
| `visit_n` | INTEGER | 0 | 0 |
| `hito` | TEXT | 0 | 0m |
| `meses_desde_baseline` | REAL | 0 | 0.0 |
| `fecha_visita` | TEXT | 0 | 2023-04-07 |
| `edad_cronologica` | REAL | 0 | 59.8 |
| `edad_biologica_modificable` | REAL | 0 | 62.60447825947311 |
| `brecha_modificable` | REAL | 0 | 2.8044782594731084 |
| `brecha_genetica_fija` | REAL | 65.2 | 1.12 |
| `brecha_total_pro` | REAL | 65.2 | 0.1998319807618434 |
| `phenoage` | REAL | 0 | 52.1259665140952 |
| `brecha_phenoage` | REAL | 0 | -1.5681217426374348 |
| `score_longevidad` | REAL | 0 | 39.22664879822472 |
| `score_metabolismo` | REAL | 0 | 39.87865693228807 |
| `score_inflamacion` | REAL | 0 | 53.8292500596992 |
| `score_cardiovascular` | REAL | 0 | 27.220126907869407 |
| `score_detoxificacion` | REAL | 0 | 37.09188375497646 |
| `score_rendimiento` | REAL | 0 | 45.0755551125553 |
| `n_condiciones` | INTEGER | 0 | 2 |
| `n_analitos_medidos` | INTEGER | 0 | 49 |
| `n_analitos_fuera_rango` | INTEGER | 0 | 7 |
| `alerta_metabolica_temprana` | INTEGER | 0 | 0 |
| `celular_en_cama` | INTEGER | 0 | 0 |
| `sesiones_fuerza_sem` | INTEGER | 0 | 2 |
| `min_cardio_sem` | INTEGER | 0 | 260 |
| `sedentarismo_h_dia` | REAL | 0 | 8.4 |
| `ultraprocesados_sem` | INTEGER | 0 | 4 |
| `alcohol_sem` | INTEGER | 0 | 0 |
| `dieta_mediterranea_score` | REAL | 0 | 6.5 |
| `tabaquismo` | TEXT | 0 | Nunca |
| `estres_percibido` | REAL | 0 | 3.3 |
| `ansiedad_score` | REAL | 0 | 1.3 |
| `calidad_sueno` | REAL | 0 | 8.6 |
| `sueno_horas` | REAL | 0 | 6.8 |
| `hora_acostarse` | REAL | 0 | 21.2 |
| `energia` | REAL | 0 | 6.3 |
| `claridad_mental` | REAL | 0 | 7.1 |
| `dolor` | REAL | 0 | 1.1 |
| `molestias_digestivas` | REAL | 0 | 1.0 |
| `hallazgo_principal` | TEXT | 0 | ninguno |
