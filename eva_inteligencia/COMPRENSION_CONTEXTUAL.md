# Comprensión contextual local: entrega y verificación

Se mantiene el modelo `experimentos/v03_01/lr_caracteres_original.joblib` con sus mismos
umbrales. No se entrenó ni sustituyó ningún modelo. El adaptador sigue devolviendo datos
de diagnóstico con `ejecutable=False`, sin conectar funciones reales ni modificar `main.py`.

## Trabajo recuperado y completado

Al reanudar ya existían `contexto.py`, su conexión en `integracion.py`, los campos
contextuales de `diagnostico_whisper.py` y una copia del adaptador anterior. No había
desafíos contextuales nuevos, evaluación antes/después ni pruebas específicas de contexto.
Se conservaron esas implementaciones y se completó su verificación.

La revisión corrigió detalles pendientes: los fragmentos compuestos ahora conservan
`:` y separadores de fecha para el extractor existente; no se descartan silenciosamente
segundas solicitudes ajenas a las capacidades locales; se reconocen objetos coordinados
como «abre Chrome y Paint», peticiones negadas dentro de una secuencia y formas como
«mientras detienes la alarma». La cortesía no cuenta como otra orden. Se distingue el
reloj de «mi equipo» de una fecha personal, y se permite preguntar por las funciones de EVA.

La primera ejecución de desarrollo encontró un fallo al segmentar «mientras detienes»;
se corrigió antes de congelar las reglas y evaluar los desafíos nuevos.

## Comportamiento contextual

1. Los comandos locales atendidos mantienen prioridad y evitan el análisis adicional.
2. Se identifican solicitudes múltiples, alternativas, negaciones, condiciones, referencias
   sin resolver y algunas preguntas informativas. Una petición cortés como «¿Puedes abrir
   la calculadora?» no se trata automáticamente como pregunta externa.
3. Las solicitudes compuestas devuelven `estado=aclaracion`, `intenciones_posibles`,
   `solicitudes` y `por_resolver`. Cada fragmento conserva su texto, posibilidades y datos
   pendientes; no se devuelve una propuesta global ni se acepta una parte silenciosamente.
   Las posibilidades son hipótesis léxicas, no autorizaciones ni planes de ejecución.
4. Se mantienen las guardas anteriores y la personalización confirmada. Las asociaciones
   personales no se leen en el diagnóstico de Whisper ni se alteran durante las pruebas.
5. Si el modelo supera sus umbrales, se verifica que el contexto sea compatible con la
   intención: objeto de aplicación, petición musical, alarma explícita, ayuda sobre EVA,
   reloj/calendario actual en lugar de una agenda personal, entre otros contratos.
6. La extracción final sigue a cargo de `extraer_parametros` y sus validadores existentes.
   Los fragmentos usan ese mismo extractor; no se duplicaron analizadores temporales ni se
   modificaron fechas, alarmas o recordatorios del asistente.

Las tres propuestas desconocidas documentadas en la etapa anterior se corrigen:

| Texto usado en desarrollo | Antes | Después |
|---|---|---|
| Cuál es la fecha de mi examen de ingreso | consultar_fecha | desconocido: fecha personal |
| Necesito ayuda para hacer una monografía | ayuda | desconocido: tema ajeno a las capacidades de EVA |
| Ya sabes qué tienes que hacer | ayuda | aclaracion: referencia sin resolver |

También «Pon una canción cualquiera» pasa de una propuesta musical a pedir una canción
concreta. Estos cuatro casos son **desarrollo conocido**, no evidencia independiente.

## Método de evaluación

`evaluar_contexto.py` carga la copia anterior del adaptador y el nuevo usando exactamente
el mismo artefacto y umbrales. No modifica ni vuelve a evaluar las 58 frases de prueba
conservada para ajustar reglas. Su archivo de particiones se comprueba por hash.

Se redactaron y congelaron dos desafíos sintéticos nuevos antes de observar sus predicciones:

- `contexto_natural.csv`: 22 comandos completos, 12 desconocidas y 6 incompletas/ambiguas.
- `contexto_adversarial.csv`: 8 comandos completos, 24 desconocidas y 8 incompletas/ambiguas.

Son 80 frases nuevas, sin duplicados normalizados entre ellas ni coincidencias exactas con
el desafío v04 usado como desarrollo. No son grabaciones ni datos de usuarios. Independencia
significa que no se usaron sus resultados para ajustar esta versión; la autoría sintética
compartida y las similitudes semánticas impiden considerarlas una prueba representativa
de hablantes reales. No se afirma haber eliminado toda paráfrasis cercana a desarrollo.

`congelacion.json` registra hashes del modelo, reglas, extractores, desafíos y componentes
protegidos antes de evaluar. Se comprobaron al terminar y en las pruebas. No hubo ajustes
de reglas ni umbrales después de consultar los resultados nuevos. Las frases ahora
inspeccionadas necesitarían una reserva distinta para una futura evaluación ciega.

## Resultados antes y después

La cobertura cuenta propuestas para comandos completos conocidos. La precisión cuenta
propuestas con la intención correcta. Rechazo de desconocidas significa que no hay una
propuesta: puede devolver `desconocido` o pedir aclaración. Las solicitudes incompletas se
evalúan aparte y no se mezclan con comandos completos para inflar cobertura.

| Conjunto | Cobertura antes → después | Precisión antes → después | Rechazo desconocidas antes → después | Propuestas desconocidas antes → después |
|---|---:|---:|---:|---:|
| Desarrollo conocido v04 (33 completas / 42 desconocidas) | 57,6 % → 45,5 % | 86,4 % → 100 % | 92,9 % → 100 % | 3 → 0 |
| Nuevo natural (22 completas / 12 desconocidas) | 63,6 % → 63,6 % | 77,8 % → 100 % | 66,7 % → 100 % | 4 → 0 |
| Nuevo adversarial (8 completas / 24 desconocidas) | 75,0 % → 75,0 % | 66,7 % → 100 % | 87,5 % → 100 % | 3 → 0 |
| Nuevos combinados (30 completas / 36 desconocidas) | 66,7 % → 66,7 % | 74,1 % → 100 % | 80,6 % → 100 % | 7 → 0 |

Solicitudes incompletas/ambiguas propuestas indebidamente:

| Conjunto | Antes | Después |
|---|---:|---:|
| Desarrollo v04, 10 casos | 1 | 0 |
| Nuevo natural, 6 casos | 0 | 0 |
| Nuevo adversarial, 8 casos | 3 | 1 |

Los nuevos conjuntos mantienen 20 de 30 comandos completos aceptados. Se corrigen siete
propuestas desconocidas y dos ambiguas, sin nuevas pérdidas de comandos completos en esos
80 ejemplos. Esto no demuestra una mejora general del español: las muestras son pequeñas.

Ejemplos nuevos evaluados una sola vez:

| Frase | Antes | Después |
|---|---|---|
| Qué fecha vence mi pasaporte | consultar_fecha | desconocido |
| Qué hora es en Buenos Aires actualmente | consultar_hora | desconocido |
| Explícame cómo se abre el explorador de archivos | abrir_aplicacion | desconocido |
| Por qué Spotify pausa mis canciones | spotify_pausar | desconocido |

`experimentos/contexto_v01/informe.json` contiene todas las salidas, los motivos, métricas
por intención, matrices de confusión, desgloses por categoría, mejoras y regresiones.
`integracion_anterior.py` es una copia para comparación offline, no un segundo enrutador
activo. El evaluador evita sobrescribir una corrida existente.

## Regresiones y limitaciones comprobadas

En el desafío v04 se pierden cuatro aceptaciones válidas; se conservan visibles en el informe:

- «EVA informa la hora que tienes en pantalla»: el contrato del reloj es demasiado estricto.
- «Me lees lo que tengo pendiente de recordar»: faltan variantes léxicas del objeto consultado.
- «Eba para la al arma»: el contrato no reconstruye la palabra fragmentada por transcripción.
- «Sierra la calculadora»: no se corrige automáticamente ese homófono a «cierra».

Sigue pendiente **«Pon música igual que ayer»**, que se propone como búsqueda de una canción
con consulta literal «música igual que ayer». No se ejecutó. Es una referencia ambigua que
las reglas actuales no detectan. Se informa sin ajustar este desafío después de evaluarlo.

Las reglas son conservadoras y finitas, no un analizador semántico completo: pueden rechazar
títulos musicales o asuntos con negaciones/conectores, y no garantizan reconocer toda orden
compuesta, anáfora o pregunta externa. No se conserva historial conversacional para resolver
referencias. Tampoco puede reconstruirse con certeza una negación perdida por el transcriptor.
El 100 % de rechazo observado en 36 desconocidas nuevas no garantiza cero falsos positivos futuros.

La recomendación es conservar el mismo modelo de caracteres y mantener todo en diagnóstico.
Hay evidencia de reducción de propuestas incorrectas en estos ejemplos, junto con una
pérdida real de cobertura en desarrollo. No se justifica habilitar ejecución de acciones.

## Whisper y privacidad

`diagnostico_whisper.py` muestra el motivo contextual con prioridad sobre el score estadístico,
las posibles intenciones y lo pendiente por resolver. Sigue aceptando transcripciones por
entrada estándar o un WAV elegido explícitamente, sin guardar audio/texto por defecto.

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --modelo eva_inteligencia/experimentos/v03_01/lr_caracteres_original.joblib
```

No se proporcionaron transcripciones reales para esta etapa; por tanto **no se afirma haber
validado habla real**. Las pruebas usan texto sintético y dobles del transcriptor. No se
inspeccionaron grabaciones personales ni se capturó el micrófono. No se cambiaron Small,
sus parámetros, voz, pyttsx3 ni los servicios del asistente. No se usaron servicios externos.

## Archivos y pruebas

Trabajo contextual conservado y completado: `contexto.py`, `integracion.py` y
`diagnostico_whisper.py`. Creados para verificar: `evaluar_contexto.py`, los dos CSV nuevos,
`tests/test_contexto_local.py`, este documento y los artefactos en `experimentos/contexto_v01/`.

Se añadieron 20 pruebas: tres errores históricos, compatibilidad intención/objeto,
incompletitud, negación, preguntas, compuestas y elipsis, fragmentos temporales intactos,
cortesía, prioridad local, personalización confirmada, privacidad del diagnóstico, reutilización
del extractor y conservación de hashes. La regresión completa terminó con **196 pruebas
aprobadas: 176 anteriores y 20 nuevas**, en 76,61 segundos, código de salida 0. El registro
final queda en `tests/resultado_contexto_regresion_final.txt`.

`tests/` permanece ignorado. No se modificó `main.py`, ningún dato personal, configuración
privada ni archivo `.cache`. No se realizaron git add, commit, push o merge. La rama
comprobada fue `inteligencia-local-eva`. La etapa termina tras las pruebas y la entrega;
cualquier siguiente ajuste debe usar nuevos datos de evaluación y autorización del usuario.
