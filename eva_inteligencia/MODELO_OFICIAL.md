# Modelo oficial de interpretación local

La ruta de ejecución es **`eva_inteligencia/modelos/intenciones_lr_v03.joblib`**.
`modelo_oficial.py` la resuelve respecto de su propio archivo, independientemente
del directorio de trabajo. Observación, diagnóstico de Whisper, consola de
diagnóstico, probador interactivo e `InterpreteLocal()` comparten esta ruta.

Es una copia binaria del artefacto seleccionado en v03, sin reentrenamiento,
reserialización, cambio de umbrales ni ajuste de parámetros. El SHA-256 es:

```text
3c99658cf506c81939b1a2fc7b71e629b1e1df3fcb57eaed12460bc402514242
```

El manifiesto `modelos/intenciones_lr_v03.json` documenta procedencia, tamaño,
formato, clases y dependencias. La procedencia histórica es informativa: no se
abre ningún archivo experimental al cargar el modelo oficial. El manifiesto
tampoco sustituye los umbrales del paquete; éstos se leen del mismo artefacto.

## Por qué no usar modelo_intenciones.joblib

Los dos modelos comparados **no son equivalentes**:

| Propiedad | Prototipo versionado `modelo_intenciones.joblib` | Seleccionado v03 / oficial |
|---|---|---|
| SHA-256 | `b2b000272cca991b8501f5b7a89f566441e1f82a2c603e99c0c5f5aa32018d20` | `3c99658cf506c81939b1a2fc7b71e629b1e1df3fcb57eaed12460bc402514242` |
| Tamaño | 442.282 bytes | 206.070 bytes |
| Algoritmo | Regresión logística, caracteres | Regresión logística, caracteres |
| Clases/etiquetas | Las mismas 12 | Las mismas 12 |
| Referencias de entrenamiento | 282 frases | Matriz de 168 referencias |
| Vocabulario / columnas de coeficientes | 3.786 | 2.941 |
| Umbrales | Probabilidad 0,25; similitud 0,34, aplicados por el motor antiguo | Score 0,4; similitud 0; margen 0, incluidos en el paquete |
| Contenido | `modelo`, `frases_entrenamiento`; metadatos en archivo separado | `modelo`, `referencias`, `umbrales`, `version_sklearn`, `formato=1` |

Ambos usan TF-IDF `char_wb`, n-gramas (2,5), `sublinear_tf=True`, y regresión
logística C=5, pesos balanceados, 1500 iteraciones máximas y semilla 42. Compartir
hiperparámetros no hace iguales sus vocabularios ni sus parámetros aprendidos.
El prototipo no tiene el formato requerido por `InterpreteLocal`.

La comparación sobre las mismas 237 entradas sintéticas existentes produjo:

| Conjunto | Entradas | Candidatas distintas | Decisiones por umbrales distintas |
|---|---:|---:|---:|
| Desafío independiente | 72 | 7 | 16 |
| Desafío v04 | 85 | 10 | 23 |
| Contexto natural | 40 | 4 | 15 |
| Contexto adversarial | 40 | 3 | 14 |

Todas las filas tuvieron probabilidades diferentes entre ambos modelos. Esta
comparación no constituye una nueva selección ni una evaluación de mejora: sólo
comprueba que cambiar al prototipo versionado alteraría el comportamiento.

El modelo v03 fue elegido por el objetivo de validación, que penalizaba falsas
aceptaciones. En la reserva histórica tuvo 54 % de cobertura, 100 % de precisión
en propuestas aceptadas y 100 % de rechazo de desconocidas. Las alternativas v04
no mejoraron consistentemente cobertura y rechazo, por lo que se conservó v03.
Son resultados históricos sobre conjuntos pequeños, no garantías generales.

## Separación de ejecución y desarrollo

- `observacion.py`, `diagnostico_whisper.py`, `diagnostico.py`, `probar.py` y el
  constructor por defecto de `integracion.py` usan el modelo oficial.
- El argumento explícito `--modelo` y `InterpreteLocal(ruta)` siguen disponibles
  para comparar artefactos locales de confianza. No hay selección automática de
  alternativas ni fallback si falta el modelo oficial.
- `motor.py` / `MotorIntenciones` se conservan como API del prototipo histórico,
  con `modelo_intenciones.joblib` y `modelo_info.json`. Se usan para comparaciones
  de desarrollo; no son el motor del observador ni del diagnóstico actual.
- `entrenar.py` sigue siendo el entrenador histórico; `entrenamiento.py`,
  `optimizar.py`, `evaluar_contexto.py`, `evaluar_voz.py`, `evaluar_integracion.py`
  y `medir.py` son herramientas de desarrollo/evaluación. Las rutas de experimentos
  que conservan son intencionales. No se utilizó entrenamiento para generar o
  seleccionar el modelo oficial; la incidencia de la prueba histórica se explica abajo.
- Las funciones de puntuación importadas de `entrenamiento.py` no leen informes,
  particiones ni modelos experimentales. Su importación no inicia entrenamiento.
- Los modelos e informes existentes dentro de `experimentos/` permanecen intactos.

## Repositorio e instalador Windows

Para el próximo commit deben incluirse los cambios de código y los archivos
nuevos `modelo_oficial.py`, `modelos/intenciones_lr_v03.joblib` y su manifiesto.
Esta tarea no ejecuta `git add`, commit, push ni merge: esos archivos nuevos no
quedan versionados automáticamente. `experimentos/` y `tests/` no son necesarios
para cargar el modelo de ejecución y están ignorados por Git. El directorio
`modelos/` no está ignorado.

Al preparar el instalador:

1. Incluir el paquete `eva_inteligencia`, sus módulos importados y el directorio
   `modelos/` como recursos, conservando su posición relativa a `modelo_oficial.py`.
   No usar rutas al árbol de experimentos del equipo de desarrollo.
2. Mantener el artefacto de sólo lectura junto a la aplicación; no mezclarlo con
   preferencias o asociaciones personales de `%LOCALAPPDATA%\EVA`.
3. Incluir scikit-learn **1.9.1**, la versión declarada por el paquete y exigida
   por el adaptador, con sus dependencias compatibles. El entorno validado usa
   Python 3.13.15. El rango amplio de `requirements-inteligencia.txt` por sí solo
   no garantiza la misma versión al crear un entorno nuevo.
4. Verificar SHA-256 y carga en el entorno final, desde otro directorio y sin
   `experimentos/`. Los archivos joblib sólo deben proceder del proyecto y de
   fuentes de confianza.
5. Conservar la distribución/caché de Whisper Small y sus parámetros actuales;
   el artefacto aquí descrito es el clasificador de texto, no el modelo de voz.

No se ha construido un instalador en esta etapa. La prueba de copia limpia usa
los archivos del repositorio con estos cambios y los nuevos recursos propuestos,
sin experimentos, configuración privada ni acceso a servicios. Usa el entorno
virtual existente; no equivale a probar todas las dependencias en otro Windows.

## Verificaciones

Resultado final: **276 pruebas aprobadas y 1 omitida**, de 277 descubiertas,
en 48,832 segundos. La omisión corresponde únicamente al reentrenamiento histórico.
Se añadieron 13 pruebas de distribución y paridad. `git diff --check` terminó
sin errores. Los registros están en `tests/resultado_regresion_sin_entrenar.txt`
y `tests/comparacion_artefactos_modelo.json`.

La copia oficial conserva exactamente los bytes y los resultados del seleccionado:
probabilidades completas, candidatas, márgenes, similitudes, decisiones por umbral
y diagnósticos contextuales/paramétricos coinciden en las 237 entradas. Un reloj
fijo hace comparable la extracción de fechas relativas. No se ajustó ninguna regla.

Se comprobó la carga y el observador desde una copia sin `experimentos/`, también
desde un directorio de trabajo diferente. Se probó el diagnóstico de Whisper por
texto y por la ruta de micrófono con transcripción simulada, sin capturar audio;
las funciones y los parámetros de Whisper no cambiaron. El observador no ejecuta
acciones, no carga sklearn cuando está desactivado y se desactiva si falta el
modelo, sin elegir el prototipo antiguo.

Las pruebas locales también verifican los hashes del índice de Git, los archivos
experimentales y los módulos protegidos, incluyendo `main.py` y Whisper. Las
comprobaciones históricas de fuentes usan las copias previas de los módulos cuyas
rutas cambiaron, sin reescribir los informes históricos.

Incidencia de verificación: la primera ejecución completa incluyó inadvertidamente
`test_reentrenamiento_reproducible_y_sin_sobrescritura`, una prueba histórica que
entrena cuatro clasificadores en un directorio temporal. No reemplazó ningún
modelo distribuido ni alteró los experimentos originales, pero no correspondía
ejecutarla bajo la restricción de esta etapa. La verificación final usa
`tests/ejecutar_regresion_sin_entrenar.py`: omite esa prueba y bloquea los métodos
de entrenamiento para detectar cualquier otra llamada accidental.
