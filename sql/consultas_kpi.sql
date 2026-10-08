-- Consultas de ejemplo sobre el modelo en estrella (carpeta bi/). Sintaxis estándar: corre en SQLite y, cambiando nombres de tabla, en BigQuery.
-- name: kpi_cohorte
SELECT COUNT(DISTINCT patient_id) AS pacientes, COUNT(*) AS visitas, ROUND(AVG(CASE WHEN visit_n = 0 THEN brecha_modificable END), 2) AS brecha_media_inicial,
       ROUND(100.0 * AVG(CASE WHEN visit_n = 0 THEN (brecha_modificable >= 2) END), 1) AS pct_acelerados
FROM fact_visita;
-- name: plan_vs_estandar_12m
SELECT CASE WHEN p.tiene_plan = 1 THEN 'Con plan' ELSE 'Seguimiento estándar' END AS grupo, COUNT(r.d_brecha_modificable_12m) AS n,
       ROUND(AVG(r.d_brecha_modificable_12m), 2) AS delta_brecha_12m, ROUND(AVG(r.d_score_longevidad_12m), 2) AS delta_longevidad_12m, ROUND(AVG(r.d_n_condiciones_12m), 2) AS delta_condiciones_12m
FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) WHERE r.d_brecha_modificable_12m IS NOT NULL GROUP BY 1;
-- name: respondedores_6m_por_protocolo
SELECT p.protocolo, COUNT(r.resp_6m) AS n, ROUND(100.0 * AVG(r.resp_6m), 1) AS pct_respondedores
FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) WHERE r.resp_6m IS NOT NULL GROUP BY 1 ORDER BY 3 DESC;
-- name: ritmo_por_adherencia
SELECT p.adherencia, COUNT(*) AS n, ROUND(AVG(r.ritmo_envejecimiento), 2) AS ritmo_medio
FROM fact_resultado_paciente r JOIN dim_paciente p USING (patient_id) GROUP BY 1 ORDER BY 3;
-- name: genetica_fija_vs_modificable_pro
SELECT ROUND(AVG(g.brecha_genetica_fija), 2) AS genetica_media, ROUND(AVG(v.brecha_modificable), 2) AS modificable_media_inicial, COUNT(*) AS n
FROM dim_genetica_pro g JOIN fact_visita v ON v.patient_id = g.patient_id AND v.visit_n = 0;
-- name: embudo
SELECT etapa, pacientes, ROUND(100.0 * pacientes / (SELECT pacientes FROM fact_embudo WHERE orden = 1), 1) AS pct_de_consultas FROM fact_embudo ORDER BY orden;
-- name: padecimientos_inicio_vs_12m
SELECT c.condicion, ROUND(100.0 * AVG(CASE WHEN v.visit_n = 0 THEN c.presente END), 1) AS pct_inicio, ROUND(100.0 * AVG(CASE WHEN v.visit_n = 2 THEN c.presente END), 1) AS pct_12m
FROM fact_condicion c JOIN fact_visita v USING (visit_id) GROUP BY 1 ORDER BY 2 DESC;
-- name: alerta_metabolica_temprana
SELECT alerta_metabolica_temprana AS alerta, COUNT(*) AS visitas FROM fact_visita WHERE visit_n > 0 GROUP BY 1;
