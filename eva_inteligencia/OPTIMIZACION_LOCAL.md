# Segunda etapa de optimización local

La recomendación es **conservar el candidato anterior de caracteres de v03_01** como
referencia de diagnóstico. No se ha activado ejecución, reemplazado un modelo anterior
ni modificado `main.py`. La cobertura aumentó en algunos candidatos, pero no de forma
consistente con el rechazo requerido. Tampoco el adaptador anterior garantiza seguridad
fuera de los ejemplos ya ensayados.

## Datos y método

Se analizaron los errores del conjunto de **validación anterior**. Los mayores déficits
aparecían en aplicaciones, ayuda, detener alarmas y expresiones de música. Había además
peticiones conocidas sin fecha/asunto/canción concreta: clasificarlas correctamente no
significa que puedan convertirse en acciones completas.

Se redactaron 198 frases sintéticas adicionales en `datos/ampliacion_v04.csv`: vocabulario
de arranque/cierre de aplicaciones, orientación sobre capacidades, control musical,
paráfrasis temporales y negativos difíciles (negaciones, órdenes compuestas, condiciones,
acciones destructivas, confusiones léxicas y servicios ajenos). No se usaron datos personales.

Se conservan intactos el corpus original, los cuatro artefactos anteriores, las 58 frases
de prueba agrupada y el desafío anterior de 72 frases. Sus hashes quedan en el nuevo informe.
Se añadió `datos/desafio_v04.csv`, congelado antes de entrenar: **85 frases**, de las cuales
33 son comandos completos conocidos, 10 conocidas incompletas/ambiguas y 42 desconocidas.
Las transcripciones con «Eba», «al arma», «Sierra» o «espotifai» son errores simulados,
no transcripciones recogidas de usuarios ni estimaciones de la tasa de error de Whisper.

Se agrupan componentes conexas con las mismas reglas léxicas de la etapa anterior:
normalización, plantillas de números/cortesía y similitud >= 0,80. Las familias de cualquier
reserva se excluyen de desarrollo, incluso cuando esto exige retirar ejemplos antiguos
de entrenamiento. La consulta de texto reservado se limita a impedir contaminación;
no se usa su resultado de clasificación para redactar o ajustar el entrenamiento.
Se excluyeron 26 registros por cercanía a reservas o duplicación. El desarrollo resultante
contiene **296 frases de entrenamiento y 100 de validación**, separadas por familia con
`StratifiedGroupKFold`, semilla 104. `particiones.json` y `excluidos.json` permiten auditarlo.

No hay familias detectadas compartidas entre entrenamiento, validación y reservas.
La agrupación es léxica: no demuestra independencia semántica absoluta de toda paráfrasis.
Las reservas antiguas ya habían sido examinadas en la etapa anterior; se conservan como
regresión fija. El desafío nuevo es sintético y comparte autor/criterios con el desarrollo,
por lo que tampoco sustituye una prueba con hablantes independientes.

Se comparan tres modelos ligeros con los hiperparámetros previamente definidos: regresión
logística de caracteres, regresión logística de palabras y caracteres, y SVM lineal.
Cada uno usa umbrales globales o por intención. IDF y pesos sólo se ajustan en entrenamiento.
La grilla de score/margen/similitud sólo recibe validación. Se maximiza cobertura correcta
entre configuraciones con **cero propuestas erróneas observadas en validación**; se incluye
rechazar todo como alternativa. Umbrales específicos requieren al menos cinco ejemplos
reales de la intención y tres propuestas correctas; si falta soporte heredan el global.
En SVM el score es un margen, no una probabilidad calibrada.

Selección, umbrales y métricas de validación se escriben en
`seleccion_antes_de_prueba.json` antes de abrir la evaluación. El ganador por validación fue
`lr_palabras_caracteres_por_intencion`. No se eligió otro tras observar la prueba.
La condición de recomendación estaba fijada: mejorar cobertura correcta en prueba antigua
y desafío nuevo sin aumentar errores ni empeorar rechazo, y ningún error de propuesta del
adaptador en el desafío. El candidato no la cumplió. Todos los candidatos se conservan
separados en `experimentos/v04_01/`; ninguno se instala ni activa.

## Comparación sobre los mismos ejemplos

Prueba agrupada conservada: 50 conocidas y 8 desconocidas. Cobertura es la proporción
de conocidas para las que se ofrece alguna intención; puede incluir una intención equivocada.
El JSON incluye también `cobertura_correcta_conocidas`, precisión/recall por intención,
matriz de confusión, falsos positivos y todas las frases erróneas.

| Modelo | Cobertura conocidas | Precisión propuestas | Rechazo desconocidas | Propuestas erróneas |
|---|---:|---:|---:|---:|
| Anterior LR caracteres | 54,0 % | 100,0 % | 100,0 % | 0 |
| Anterior SVM | 90,0 % | 81,3 % | 62,5 % | 9 |
| Nuevo LR caracteres global | 42,0 % | 100,0 % | 100,0 % | 0 |
| Nuevo LR caracteres por intención | 80,0 % | 95,1 % | 87,5 % | 2 |
| Nuevo LR palabras + caracteres global | 56,0 % | 100,0 % | 100,0 % | 0 |
| Nuevo LR palabras + caracteres por intención | 78,0 % | 92,7 % | 75,0 % | 3 |
| Nuevo SVM global | 28,0 % | 100,0 % | 100,0 % | 0 |
| Nuevo SVM por intención | 80,0 % | 92,9 % | 75,0 % | 3 |

Desafío nuevo, **clasificador sin adaptador**: 43 conocidas (incluye las 10 incompletas)
y 42 desconocidas. Clasificar intención no evalúa todavía completitud de parámetros.

| Modelo | Cobertura conocidas | Precisión propuestas | Rechazo desconocidas |
|---|---:|---:|---:|
| Anterior LR caracteres | 67,4 % | 70,7 % | 71,4 % |
| Anterior SVM | 93,0 % | 58,2 % | 35,7 % |
| Nuevo LR caracteres global | 46,5 % | 76,9 % | 85,7 % |
| Nuevo LR caracteres por intención | 76,7 % | 68,8 % | 64,3 % |
| Nuevo LR palabras + caracteres global | 65,1 % | 80,0 % | 83,3 % |
| Nuevo LR palabras + caracteres por intención | 83,7 % | 66,0 % | 59,5 % |
| Nuevo SVM global | 37,2 % | 94,1 % | 97,6 % |
| Nuevo SVM por intención | 81,4 % | 72,9 % | 69,0 % |

El LR combinado global mejora de 27 a 28 conocidas aceptadas en la prueba antigua, pero
pasa de 29 a 28 en el desafío nuevo. Un ejemplo de diferencia no es evidencia suficiente
para proclamar superioridad. El SVM global mejora rechazo a costa de rechazar muchos
comandos válidos. Los umbrales por intención sobreajustan una validación todavía pequeña:
cero errores allí no implica ausencia de errores fuera de ella.

Con el **mismo adaptador existente** aplicado a ambos modelos se evaluaron por separado
los 33 comandos completos y las 42 desconocidas; las otras 10 frases exigen aclaración:

| Adaptador | Cobertura completas | Precisión propuestas | Rechazo desconocidas | Propuestas desconocidas | Incompletas propuestas |
|---|---:|---:|---:|---:|---:|
| Con LR anterior | 57,6 % (19/33) | 86,4 % | 92,9 % (39/42) | 3 | 1/10 |
| Con nuevo ganador de validación | 75,8 % (25/33) | 83,3 % | 88,1 % (37/42) | 5 | 0/10 |

Errores comprobados del adaptador anterior: «Cuál es la fecha de mi examen de ingreso»
se confunde con consultar fecha actual; «Necesito ayuda para hacer una monografía» y
«Ya sabes qué tienes que hacer» con ayuda. Además, «Pon una canción cualquiera» se acepta
como consulta musical aunque requiere aclaración.
El candidato nuevo conserva los tres primeros errores y añade «Qué hora comienza la
película» y la orden compuesta «Inicia Chrome mientras detienes la alarma».
No se ejecutó ninguna de esas propuestas. Los detalles por categoría, incluidos errores
de transcripción, negaciones, instrucciones destructivas y compuestas, están en
`informe.json → adaptador → anterior/seleccionado → categorias/detalles`.

Las protecciones no se relajaron ni se ajustaron para mejorar las cifras de este desafío.
Estos hallazgos quedan documentados; cambiar reglas y volver a presentarlos como prueba
ciega sería engañoso. Cualquier siguiente ciclo necesita nuevos ejemplos de desarrollo
autorizados y una reserva distinta. Conservar el modelo anterior no equivale a autorizarlo
para ejecutar acciones: los nuevos errores del propio modelo anterior lo desaconsejan.

## Diagnóstico de Whisper Small

`diagnostico_whisper.py` acepta transcripciones reales por entrada estándar o un WAV
seleccionado explícitamente. Informa intención candidata, score/margen/similitud y sus
umbrales, parámetros, resultado y motivo de aceptación/rechazo. Siempre devuelve
`ejecutable=False`; una intención candidata no implica autorización.

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --modelo eva_inteligencia/experimentos/v03_01/lr_caracteres_original.joblib
```

Pega una transcripción por línea; Ctrl+Z y Enter termina en Windows. No guarda textos,
audio, asociaciones ni preferencias, ni captura el micrófono. La salida sólo se muestra
en consola. El usuario puede redirigirla explícitamente, pero no se crea un registro.

Para transcribir una grabación elegida:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --modelo eva_inteligencia/experimentos/v03_01/lr_caracteres_original.joblib --wav "C:\ruta\grabacion.wav"
```

Sólo carga Small de la caché existente con CPU/int8 y un trabajador. Reutiliza
`whisper_control._transcribir_wav` sin cambiar ninguno de sus parámetros. Si el modelo
no está disponible, falla sin descargar ni recurrir a un servicio externo. Se admiten
WAV de hasta 64 MiB sin recorte automático. No se han inspeccionado grabaciones privadas.
Las pruebas verifican reutilización del transcriptor y ausencia de escritura; una prueba
con habla real permanece pendiente porque no se proporcionó una grabación para esta etapa.

Para repetir entrenamiento (elige siempre un directorio nuevo):

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.optimizar --salida eva_inteligencia/experimentos/repeticion_v04
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Rendimiento y alcance

La medición conjunta utilizó el candidato nuevo, los widgets reales de `InterfazEVA`
ocultos y Whisper Small local, sin importar `main.py` ni conectar callbacks de acciones.
Se procesaron dos segundos de silencio sintético con los parámetros actuales. Resultado:
118,75 MiB de intérprete, 126,53 MiB con Tkinter y **446,12 MiB** con Small; pico del proceso
**719,81 MiB**. Carga de Small: 6,10 s; procesamiento del WAV silencioso: 0,846 s.
Datos completos en `memoria_conjunta.json`.

Es una medición conjunta real de esos componentes, pero en un único proceso de diagnóstico.
No reproduce la arquitectura de procesos completa de EVA, una sesión prolongada ni el
decodificado de voz: VAD puede descartar el silencio. El pico y el working set no miden
todo el consumo de Windows, otros programas ni toda la memoria virtual comprometida.
La carga observada es compatible con el presupuesto de 8 GB; falta medir habla real,
sesiones largas y el asistente completo en el equipo de distribución.

Las mediciones aisladas de todos los modelos se guardan en `mediciones.json` y archivos
`medicion_*.json`, con 500 repeticiones, 20 calentamientos, procesos nuevos, BLAS a un hilo
y la misma mezcla de cinco solicitudes de la etapa anterior. Se ejecutan secuencialmente
después de la regresión para no hacer competir entre sí los candidatos. Las latencias
incluyen guardas/validación, no Whisper. El resumen numérico se adjunta en
`experimentos/v04_01/RESULTADOS.md`.

## Cambios

- `entrenamiento.py`: `decidir` admite umbrales por intención manteniendo la interpretación
  de los artefactos anteriores. Sus métricas originales se comprueban en regresión.
- Nuevos `optimizar.py`, `diagnostico_whisper.py`, los dos CSV de esta etapa, este informe
  y los artefactos nuevos de `experimentos/v04_01/`.
- Pruebas y medición local en `tests/test_optimizacion_local.py` y
  `tests/medir_optimizacion_local.py`; la carpeta sigue ignorada por Git.

Personalización, confirmaciones, persistencia, voz, parámetros de Small, Tkinter, Spotify,
Gemini, alarmas, recordatorios y pyttsx3 no se modificaron. No se instalaron dependencias
ni se hicieron operaciones de publicación o cambios de rama. Todo sigue en
`inteligencia-local-eva`, sin activar ejecución.
