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
-- fact_condicion guarda solo las condiciones presentes: el denominador es el total de visitas de cada hito (fact_visita)
SELECT c.condicion,
       ROUND(100.0 * SUM(CASE WHEN v.visit_n = 0 THEN 1 ELSE 0 END) / (SELECT COUNT(*) FROM fact_visita WHERE visit_n = 0), 1) AS pct_inicio,
       ROUND(100.0 * SUM(CASE WHEN v.visit_n = 2 THEN 1 ELSE 0 END) / (SELECT COUNT(*) FROM fact_visita WHERE visit_n = 2), 1) AS pct_12m
FROM fact_condicion c JOIN fact_visita v USING (visit_id) GROUP BY 1 ORDER BY 2 DESC;
-- name: insulina_ayunas_vs_post_carga
-- ¿cuántos con insulina en ayunas normal (< 12) tienen hiperinsulinemia post-carga? (solo entre quienes se midieron las dos)
SELECT COUNT(*) AS medidos_ambas,
       ROUND(100.0 * AVG(CASE WHEN l.insulina_ayunas < 12 THEN 1.0 ELSE 0 END), 1) AS pct_ayunas_normal,
       ROUND(100.0 * SUM(CASE WHEN l.insulina_ayunas < 12 AND c.visit_id IS NOT NULL THEN 1 ELSE 0 END) / SUM(CASE WHEN l.insulina_ayunas < 12 THEN 1 ELSE 0 END), 1) AS pct_hiperinsulinemia_entre_ayunas_normal
FROM fact_laboratorio l JOIN fact_visita v USING (visit_id)
LEFT JOIN fact_condicion c ON c.visit_id = l.visit_id AND c.condicion = 'hiperinsulinemia_postcarga'
WHERE v.visit_n = 0 AND l.insulina_post_carga IS NOT NULL;
-- name: analitos_fuera_de_rango_por_hito
SELECT hito, ROUND(AVG(n_analitos_medidos), 1) AS analitos_medidos, ROUND(AVG(n_analitos_fuera_rango), 2) AS fuera_de_rango FROM fact_visita GROUP BY 1 ORDER BY 1;
-- name: genotipo_lpa_vs_lipoproteina_a
SELECT g.lpa_rs10455872 AS genotipo, COUNT(*) AS pacientes, ROUND(AVG(l.lipoproteina_a), 1) AS lp_a_media
FROM dim_genetica_pro g JOIN fact_visita v ON v.patient_id = g.patient_id AND v.visit_n = 0 JOIN fact_laboratorio l ON l.visit_id = v.visit_id GROUP BY 1 ORDER BY 1;
-- name: relojes_a_y_phenoage_por_hito
SELECT hito, ROUND(AVG(brecha_modificable), 2) AS brecha_reloj_biomarcadores_habitos, ROUND(AVG(brecha_phenoage), 2) AS brecha_phenoage_centrada FROM fact_visita GROUP BY 1 ORDER BY 1;
-- name: alerta_metabolica_temprana
SELECT alerta_metabolica_temprana AS alerta, COUNT(*) AS visitas FROM fact_visita WHERE visit_n > 0 GROUP BY 1;
