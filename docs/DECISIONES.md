# Qué haría una clínica con esto

Esta página traduce los indicadores del tablero en decisiones. Es una demostración de método sobre datos sintéticos: los números ilustran **qué pregunta responde cada indicador**, no prueban que un protocolo funcione. Con datos reales, cada decisión pide validación médica.

| Lo que muestra el tablero | Pregunta de negocio | Decisión posible | Cómo se vería si estuviera mal |
|---|---|---|---|
| 21,9 % de pacientes con 2 o más años de aceleración (brecha inicial media 0,33) | ¿A quién priorizar en agenda? | Ofrecer primero la consulta de integración y el control a 6 meses al grupo acelerado | El grupo acelerado no usa más recursos ni mejora distinto: la prioridad no se justifica |
| Brecha modificable (histograma) separada de la parte genética fija | ¿Cuánto del problema se puede mover con hábitos? | Hablar con el paciente de lo modificable; usar la parte genética solo como contexto | La brecha modificable no cambia con la intervención: el indicador no sirve para medir progreso |
| Plan vs. seguimiento estándar a 12 meses (−0,32 vs. +0,18 años; Score de Longevidad +1,38 vs. −0,90) | ¿El plan preventivo se diferencia del control de rutina? | Mantener un tablero de seguimiento con grupo de comparación desde el primer día | En datos reales, la diferencia desaparece al ajustar por quién elige el plan (sesgo de selección) |
| Respondedores a 6 meses (34,0 % vs. 10,8 %) | ¿Se puede saber temprano si el plan está funcionando? | Revisión a los 6 meses: quien no responde pasa a revisar adherencia antes de cambiar el protocolo | La respuesta a 6 meses no anticipa la de 12: la revisión intermedia no aporta |
| Respuesta individual: entre pacientes con plan y adherencia alta, 19,5 % no mejora la brecha a 12 meses (mediana −0,55; el 10 % que más mejora baja −1,5 o más) | ¿Se puede prometer el mismo resultado a todos? | Comunicar rangos y no promedios; revisar a los que no responden antes de cambiar de protocolo | La dispersión viene de ruido de medición y no de diferencias reales entre personas |
| Ritmo de envejecimiento y retención por adherencia (retención a 12 meses: 77,6 % con adherencia alta, 50,7 % con baja) | ¿Dónde se pierde el resultado? | Seguimiento activo (recordatorios, contacto) a pacientes con adherencia baja | Contactar a los de adherencia baja no cambia su retención |
| Señal temprana: AUC 0,67 con baseline y protocolo, 0,74 sumando adherencia | ¿Se puede anticipar quién abandona? | Lista de pacientes en riesgo para el equipo de seguimiento | El modelo marca a casi todos o a casi nadie: no discrimina lo suficiente para usarse |
| Embudo simulado: 8.696 → 8.000 → 6.941 → 5.746 | ¿Dónde se pierde gente? | Atacar el tramo con mayor caída (entre el control a 6 meses y el de 12 meses: 1.195 pacientes) | La caída viene de una causa que el dato no ve (precio, distancia, derivaciones) |
| Segmentos (K=3, silhouette 0,18) y roadmaps editables | ¿Cómo estandarizar el primer plan? | Usar el segmento como punto de partida de la conversación, no como diagnóstico | Los segmentos se separan poco: no sostienen una oferta distinta por grupo |
| Validación de la limpieza (en el simulador: 100 % en casi todos los grupos y 94,4 % en identidad y plan) | ¿Se puede confiar en el dato? | Mantener la validación contra el origen en cada carga (sobre una muestra de 200 pacientes con fuentes sucias) y registrar los problemas detectados | Con datos reales la exactitud baja: se vuelve una lista de reglas por corregir con el equipo |

## Primeros 90 días de un primer analista de datos (propuesta)
1. **Semanas 1–3:** relevar de dónde sale cada dato (estudios, historia clínica, agenda) y armar la tabla única por paciente con validación contra el origen.
2. **Semanas 4–8:** definir con el equipo médico 5 a 8 indicadores y sus umbrales; publicar un tablero interno con acceso restringido.
3. **Semanas 9–12:** primera lectura longitudinal con grupo de comparación y revisión de qué se puede afirmar y qué no.

## Lo que hay que cuidar con datos reales
Consentimiento informado, acceso restringido a genética y salud mental, y la Ley 25.326 de protección de datos personales. El tablero es apoyo a la decisión médica, no diagnóstico.
