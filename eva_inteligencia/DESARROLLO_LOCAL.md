# Inteligencia local: entrenamiento y diagnóstico

Entrega experimental del 4 de noviembre de 2026. No está conectada a `main.py` y no
ejecuta funciones de EVA. El modelo original y su corpus se conservan. No se recomienda
sustituir todavía el intérprete existente: aumenta el rechazo seguro, pero cae la cobertura.

## Auditoría del prototipo

El corpus original contiene 282 frases, 11 intenciones conocidas y `fuera_de_alcance`.
Hay 20 ejemplos por clase salvo crear recordatorio (35), crear alarma (23) y fuera de
alcance (44). No hay duplicados exactos después de normalizar. La agrupación léxica
detecta 244 familias; 15 contienen etiquetas distintas, por ejemplo preguntas similares
sobre hora/fecha y órdenes de abrir/cerrar. Eso no significa automáticamente que las
etiquetas sean incorrectas: los pares de contraste son necesarios y se mantienen juntos.

`texto.py` elimina tildes, puntuación y el vocativo inicial de EVA. Es útil para clasificar,
pero elimina `:` y separadores de fechas. El nuevo extractor recibe el texto original.
El prototipo usa TF-IDF de caracteres (2–5) y regresión logística, probabilidad mínima
0,25 y similitud coseno mínima 0,34. Rechaza algunas órdenes de eliminación y avisos
sin descripción, pero no toda negación ni aplicaciones ajenas a la lista autorizada.

La reserva antigua obtuvo 84,51 % de exactitud según `modelo_info.json`, pero la
serialización posterior entrenó con todo el corpus. Esa cifra no es una evaluación
independiente del archivo distribuido ni es comparable directamente con los nuevos
resultados agrupados. No había validación separada para ajustar umbrales.

Se comprobaron propuestas incorrectas para «no abras la calculadora», «abre PowerShell»,
«cierra todos los programas», «no pauses la música» y «dime la hora en Tokio».
El corpus también contiene aplicaciones no autorizadas por EVA (como Word), recordatorios
sin todos sus parámetros y peticiones de listas musicales que el adaptador no puede resolver.
Por eso reconocer una intención y validar una acción son operaciones diferentes.

## Procedimiento reproducible

1. Leer un CSV UTF-8 con columnas `frase,intencion` o `texto,intencion`.
2. Agrupar por normalización, plantillas de cortesía/números y similitud de caracteres
   `SequenceMatcher >= 0.80`. Se unen transitivamente las familias, incluso entre etiquetas.
3. Dividir con `StratifiedGroupKFold`, semillas 42 y 43: 168 ejemplos de entrenamiento,
   56 de validación y 58 de prueba. Todas las clases aparecen en los tres conjuntos.
4. Ajustar vocabularios, IDF y clasificadores exclusivamente con entrenamiento.
5. Ajustar umbrales de score, margen entre las primeras dos clases y similitud únicamente
   con validación. Los scores de SVM son márgenes; no se presentan como probabilidades.
6. Seleccionar por `F1 macro − 0.5 × tasa de aceptación de desconocidas − 0.5 × tasa
   de propuestas erróneas sobre el total`. El criterio y la grilla se fijaron antes de
   evaluar la prueba; no se optimizaron usando sus errores.
7. Evaluar los cuatro candidatos en prueba y en un desafío adicional de 72 frases
   sintéticas (44 conocidas y 28 desconocidas). El modelo original sólo se compara en
   este desafío porque ya vio todo el corpus original.
8. Guardar todos los candidatos, particiones, hashes de los dos CSV, versiones, umbrales,
   matrices de confusión y errores. Nunca sobrescribir un directorio de experimento.

El desafío se escribió antes del experimento, no participa en ajuste y no repite frases
normalizadas del corpus. Contiene casos adversariales deliberadamente parecidos a órdenes
conocidas. No es una muestra de usuarios independientes ni permite afirmar generalización
al habla real. La agrupación impide el cruce de las familias detectadas; es una heurística
léxica y no garantiza identificar todas las paráfrasis semánticas. Antes de ampliar el
corpus se deben revisar manualmente las familias. Los errores ya inspeccionados pasan a
ser material de desarrollo; futuras afirmaciones de mejora necesitan una nueva prueba ciega.

La separación por grupos sigue la [documentación de scikit-learn sobre validación cruzada](https://scikit-learn.org/stable/modules/cross_validation.html).
No se ha usado ningún servicio externo para entrenar ni se han recopilado conversaciones.

Desde la raíz del proyecto, usando el entorno existente:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.entrenamiento --salida eva_inteligencia/experimentos/nueva_evaluacion
.venv\Scripts\python.exe -m eva_inteligencia.evaluar_integracion --modelo eva_inteligencia/experimentos/nueva_evaluacion/lr_caracteres_original.joblib --salida eva_inteligencia/experimentos/nueva_evaluacion/integracion.json
.venv\Scripts\python.exe -m eva_inteligencia.medir --modelo eva_inteligencia/experimentos/nueva_evaluacion/lr_caracteres_original.joblib --salida eva_inteligencia/experimentos/nueva_evaluacion/medicion.json
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En las dos órdenes posteriores usa el nombre indicado por `seleccion_validacion` del
nuevo informe; no presupongas que siempre ganará el mismo candidato. El archivo
`entrenar.py` se conserva como procedimiento histórico del prototipo, no es el nuevo
procedimiento reproducible y puede reemplazar el modelo original si se ejecuta.

Entorno medido: Python 3.13.15, scikit-learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1,
joblib 1.6.0, Windows AMD64. No se instalaron dependencias. El informe registra las
versiones para repetirlo; un cambio de scikit-learn requiere reentrenar y reevaluar.
Las pruebas repitieron el entrenamiento y obtuvieron las mismas particiones, umbrales
y métricas de los cuatro candidatos.

## Resultados reales

`experimentos/v03_01/informe.json` contiene las métricas completas, soporte por clase,
matrices (filas reales, columnas predichas; orden en `etiquetas_matriz`) y todas las frases
mal clasificadas. `particiones.json` permite revisar cada asignación.

| Modelo entrenado sólo con entrenamiento | F1 macro validación | F1 macro prueba | Precisión propuestas prueba | Rechazo desconocidas prueba |
|---|---:|---:|---:|---:|
| Regresión logística, caracteres | 0,686 | 0,610 | 100,0 % | 100,0 % |
| Regresión logística, palabras + caracteres | 0,719 | 0,676 | 94,3 % | 100,0 % |
| SVM lineal | 0,782 | 0,756 | 81,3 % | 62,5 % |
| Complement Naive Bayes | 0,678 | 0,570 | 78,1 % | 100,0 % |

La selección por el criterio penalizado de validación es la regresión logística de
caracteres: score mínimo 0,4, sin restricción adicional de margen/similitud (ambos 0).
La mayor F1 de prueba corresponde al SVM, pero acepta 3 de las 8 instrucciones desconocidas.
Se conservan ambos y los otros candidatos; no se elige de nuevo usando la prueba.
La selección no es una promoción a producción.

Con los umbrales antiguos y el mismo entrenamiento agrupado, el algoritmo base alcanza
F1 0,713, precisión de propuestas 85,4 %, cobertura de conocidas 80,0 % y rechazo de
desconocidas 87,5 %. La calibración conservadora sube precisión y rechazo al 100 %, pero
baja cobertura al 54 % (27/50). No hay evidencia de una mejora global de comprensión.

Precisión y recall por intención del candidato seleccionado en **prueba agrupada**:

| Intención | Precisión | Recall | Ejemplos |
|---|---:|---:|---:|
| abrir_aplicacion | — | 0,0 % | 4 |
| cerrar_aplicacion | 100,0 % | 25,0 % | 4 |
| ayuda | 100,0 % | 25,0 % | 4 |
| consultar_fecha | 100,0 % | 50,0 % | 4 |
| consultar_hora | 100,0 % | 100,0 % | 4 |
| consultar_recordatorios | 100,0 % | 50,0 % | 4 |
| crear_alarma | 100,0 % | 71,4 % | 7 |
| crear_recordatorio | 100,0 % | 71,4 % | 7 |
| detener_alarma | 100,0 % | 25,0 % | 4 |
| spotify_pausar | 100,0 % | 75,0 % | 4 |
| spotify_reproducir | 100,0 % | 75,0 % | 4 |
| fuera_de_alcance | 25,8 % | 100,0 % | 8 |

«—» significa que no hubo propuestas de esa clase; JSON usa `zero_division=0`.
La precisión baja de fuera de alcance refleja comandos válidos rechazados. Las muestras
son pequeñas: 100 % observado no garantiza cero errores futuros.

Comparación en el desafío adicional, antes y después de la validación de parámetros:

| Sistema | F1 macro | Precisión propuestas | Cobertura conocidas | Rechazo desconocidas |
|---|---:|---:|---:|---:|
| Prototipo original distribuido | 0,917 | 83,0 % | 100,0 % | 67,9 % (19/28) |
| Candidato seleccionado, sólo clasificador | 0,748 | Ver JSON | Ver JSON | 71,4 % (20/28) |
| Candidato + adaptador y validaciones | 0,784 | 100,0 % | 68,2 % (30/44) | 100,0 % (28/28) |

Las correcciones de negaciones, PowerShell, cierre de todos los programas y hora en Tokio
se deben a reglas y validaciones explícitas, no a una supuesta mejora aprendida del modelo.
`integracion.json` conserva resultados antes/después por frase. El rechazo adicional también
afecta expresiones válidas: debe mejorarse el corpus con familias nuevas autorizadas y
medirse otra vez con una prueba nueva, sin activar acciones en esta etapa.

## Parámetros y asociaciones personales

`parametros.py` usa los conversores de `tiempo_eva.py`, preserva el texto del asunto y
devuelve una propuesta de datos o una pregunta de aclaración, siempre `ejecutable=False`.
Acepta fechas ISO, día/mes/año, día de mes de año, hoy/mañana/pasado mañana, próximos
días de semana, horas HH:MM o números en español con periodo explícito, minutos/horas/días,
media hora y una hora y media. El mismo día de semana pide fecha exacta. «Próximo viernes»
significa la próxima ocurrencia; para otra semana se debe indicar fecha completa.

Sin fecha o descripción no inventa valores. Rechaza horarios pasados, imposibles,
ambiguos por cambio de horario, recurrencias, condiciones, rangos, varias fechas u horas,
mezclas de fecha y duración y formatos parciales. No pretende cubrir todo el español:
segundos, semanas, «menos cuarto» y expresiones vagas requieren reformulación. Como EVA
persiste minutos, las duraciones se redondean al minuto siguiente si existen segundos,
para no entregar antes de lo pedido (hasta 59 segundos de diferencia).

Aplicaciones: calculadora, bloc de notas/Notepad, Paint, explorador de archivos, Chrome
y Spotify. Música: canción concreta, continuar, pausar, siguiente y anterior; listas y
álbumes piden aclaración. Volumen no se añade en esta etapa. La defensa por palabras es
conservadora y puede rechazar títulos o asuntos legítimos; nunca evalúa código ni recibe
nombres de funciones arbitrarios.

`personalizacion.py` admite «Cuando diga modo estudio, abre la calculadora». La acción
destino se reconoce mediante patrones explícitos y se valida; no se confía en ML para
elegir lo que se enseña. Devuelve la asociación exacta y una pregunta; sólo una confirmación
positiva con token de esa propuesta permite persistir. Los tokens duran cinco minutos,
no sobreviven al reinicio y se consumen después de escribir correctamente. El rechazo no
guarda nada. Consulta y eliminación están disponibles; eliminar también requiere confirmación.

Se guarda en `%LOCALAPPDATA%\EVA\inteligencia_local\comandos_personales.json`. Reutiliza
`bloquear`, `AlmacenJSON` y escritura atómica de `persistencia.py`: bloqueo desde lectura
hasta guardado, conflictos explícitos, copias de JSON dañado y temporales limpiados ante
errores. No sobrescribe asociaciones diferentes. Las fechas relativas se interpretan al
invocar la expresión; una fecha absoluta que ya venció pide aclaración. No se guarda
historial de conversaciones ni se modifica el modelo general.

`alias_personales.py` conserva el formato anterior de alias de intención, ahora exige
`confirmado=True` para registrar y usa la persistencia común. Los alias antiguos no se
eliminan ni se convierten automáticamente en órdenes completas: faltan parámetros y una
confirmación del destino. Permanecen disponibles para el prototipo histórico.

Consola separada, sin iniciar la interfaz ni ejecutar acciones:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico ensenar "Cuando diga modo estudio, abre la calculadora"
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico listar
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico eliminar "modo estudio"
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico interpretar "abre la calculadora" --modelo eva_inteligencia/experimentos/v03_01/lr_caracteres_original.joblib
```

Estas órdenes de enseñanza/eliminación solicitan confirmación antes de escribir datos
personales. No se ejecutaron contra el perfil real durante el desarrollo: las pruebas
usaron únicamente directorios temporales. Joblib sólo debe cargar artefactos locales de
confianza, nunca modelos descargados o elegidos por un comando de voz.

## Integración y límites pendientes

`InterpreteLocal.proponer` exige `comando_local_atendido` explícito. Si el enrutador local
atendió la orden o su resultado no es exactamente `False`, devuelve `prioridad_local` sin
clasificar. Después consulta asociaciones confirmadas, modelo y validador. Un fallo de
persistencia personal se comunica y no deriva a otra acción. No importa `main`, Tkinter,
Whisper, Spotify ni pyttsx3. Tampoco llama a Gemini.

Tras futura autorización, el punto de conexión sería: Whisper Small → enrutador local
existente → adaptador → validación final → función permitida → respuesta de EVA. La carga
del modelo debe hacerse en trabajador y los resultados llegar a Tkinter mediante su cola;
este cambio no instala hilos ni callbacks en la interfaz. Antes de conectar, verificar
la semántica de fechas de alarmas y el cierre de aplicaciones (posibles documentos sin
guardar). Esta entrega no añade permiso para cerrar programas ni otras acciones por ML.
Gemini sigue como componente opcional de preguntas generales en el código existente.

No se ha hecho un instalador ni probado una instalación limpia sin entorno de desarrollo.
La distribución debe incluir sólo el artefacto aprobado y bibliotecas compatibles; el
entrenador, corpus de desarrollo y experimentos no son necesarios para inferencia. Falta
una evaluación con voz real, diversidad de acentos, nuevos usuarios y RAM conjunta de EVA.

## Pruebas y recursos medidos

161 pruebas automatizadas satisfactorias: 127 anteriores y 34 nuevas; ejecución final
46,27 s, salida 0. Incluyen ciclo de entrega/eliminación/recuperación de recordatorios,
persistencia y preferencias, regresiones de voz/UI/Gemini con dobles de prueba, extracción
temporal, negaciones/destructivos, prioridad local, importación sin iniciar EVA, asociaciones
confirmadas, 32 escrituras concurrentes, JSON truncado/estructuras incorrectas, fallo de
`os.replace`, conservación del original, reintento, conflictos y cambio de directorio.
También se repite el entrenamiento verificando igualdad de particiones, umbrales y métricas,
y que calibración recibe sólo etiquetas de validación. `tests/` sigue ignorado por Git.

La primera ejecución de las pruebas nuevas detectó cuatro casos fallidos por no normalizar
la ñ de «mañana»; se corrigieron antes de la regresión final. No se cambiaron los modelos
ni sus umbrales después de consultar prueba.

| Medición en proceso aislado Windows | Resultado |
|---|---:|
| Artefacto seleccionado comprimido | 206.070 bytes |
| RAM inicial de inferencia | 18,07 MiB |
| RAM/pico tras cargar e inferir | 113,86 MiB |
| Importación y carga | 2,05 s |
| Inferencia mediana / p95 | 1,11 / 2,37 ms |
| Pico de entrenamiento de cuatro candidatos | 119,29 MiB |
| Entrenamiento, calibración, evaluación y serialización | 12,92 s |

Inferencia: 500 repeticiones, 20 calentamientos, BLAS a un hilo, mezcla de cuatro entradas
al modelo y una rechazada por reglas. Los tiempos incluyen propuesta/validación; no son
latencia de reconocimiento de voz. El entrenamiento se midió mientras corría la regresión,
por lo que su duración no representa rendimiento sin competencia por CPU. Archivos de
medición completos: `medicion.json` y `medicion_entrenamiento.json` del experimento.
La memoria medida es working set del proceso (pico del SO), no RAM del sistema ni memoria
virtual reservada. Sugiere que este componente ligero cabe holgadamente en 8 GB; el consumo
completo con Whisper, navegador y escritorio requiere prueba manual en el equipo objetivo.

## Archivos de esta entrega

Modificado: `alias_personales.py`. Creados: `entrenamiento.py`, `seguridad.py`,
`parametros.py`, `personalizacion.py`, `integracion.py`, `diagnostico.py`, `medir.py`,
`evaluar_integracion.py`, este documento, `datos/desafio_independiente.csv`, los artefactos
y reportes de `experimentos/v03_01/`, y pruebas/medición locales bajo `tests/`.

No se modificaron `main.py`, interfaz, voz, parámetros de Whisper, persistencia,
preferencias, alarmas, recordatorios, Spotify, Gemini, el corpus/modelo original ni
`requirements-inteligencia.txt`. No se instalaron dependencias ni se hicieron operaciones
de publicación o cambios de rama. La rama comprobada fue `inteligencia-local-eva`.
