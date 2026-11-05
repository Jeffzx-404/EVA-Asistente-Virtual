# Inteligencia local en modo observación

El modo está desactivado por defecto. No cambia el clasificador, sus umbrales,
el análisis contextual ni el enrutamiento tradicional. No entrena, no registra
conversaciones y no incorpora asociaciones personales al diagnóstico.

## Activar y probar manualmente

En PowerShell, desde la carpeta del proyecto:

```powershell
$env:EVA_DIAGNOSTICO_INTELIGENCIA = "1"
.venv\Scripts\python.exe main.py
```

Escribe «Dime la hora» en EVA. Después pulsa Hablar y di esa misma frase cuando
EVA esté escuchando. Comprueba que cada entrada obtiene su respuesta tradicional
una sola vez y una línea `[EVA observación]` en la consola, con origen `texto` o
`voz`. La primera línea puede tardar más por la carga del clasificador.

La línea incluye texto, intención candidata, estado (`propuesta`, `aclaracion`
o `desconocido`), parámetros, motivo, milisegundos de interpretación, espera
en cola (incluye la primera carga), tiempo de carga y contadores de omisiones.
`ejecutable: false` y `acciones_ejecutadas: false` describen exclusivamente el
diagnóstico. **Los comandos tradicionales sí se ejecutan**: un rechazo del
observador no los cancela ni los corrige. No usar órdenes con efectos no deseados
para probar negaciones o frases compuestas en la aplicación real.

La consola de Windows puede mostrar acentos como escapes JSON `\u00f3`; el texto
no se transforma antes de analizarlo. Se escapan para admitir consolas con
codificaciones diferentes. No aparece una segunda respuesta de voz.

Cierra EVA y vuelve a abrirla con la opción desactivada para comparar:

```powershell
$env:EVA_DIAGNOSTICO_INTELIGENCIA = "0"
.venv\Scripts\python.exe main.py
```

La opción se lee al arrancar; sólo el valor exacto `1` la activa. No modifica
preferencias ni variables permanentes de Windows. No redirijas la consola a un
archivo si no deseas conservar textos. El observador sólo imprime; no guarda
audio ni transcripciones y no envía sus diagnósticos a servicios externos.
Los servicios opcionales del enrutador tradicional conservan su configuración.

## Funcionamiento y aislamiento

- `main.py` entrega una copia del texto original en los dos puntos de entrada,
  antes de llamar al procesador tradicional. Ignora el resultado de la entrega.
  El cuerpo de `procesar_comando`, la captura de voz y los ejecutores no cambian.
- `observacion.py` importa sólo biblioteca estándar al iniciar EVA. Desactivado,
  no crea un hilo ni importa sklearn/joblib. Activado, crea un solo trabajador
  daemon y carga el modelo al recibir el primer texto, fuera de Tkinter.
- El trabajador reutiliza `InterpreteLocal` y `diagnostico_whisper.diagnosticar`.
  No recibe referencias a Tkinter, funciones ejecutoras ni síntesis de voz.
  La evaluación independiente usa el adaptador en diagnóstico; no altera la
  prioridad de los comandos locales de EVA.
- Hay ocho lugares pendientes y como máximo un texto en análisis. Al llenarse,
  se descarta el diagnóstico nuevo y se incrementa `diagnosticos_omitidos`, visible
  en los siguientes resultados. Las entradas vacías, no textuales o de más de
  1000 caracteres también se omiten, sin truncarlas. EVA conserva su procesamiento.
- Si falta el modelo o falla su carga, se emite un aviso genérico y se desactiva
  ese trabajador hasta reiniciar EVA, sin repetir cargas por cada comando. Una
  excepción al analizar un texto produce `desconocido`; el siguiente puede
  analizarse normalmente. No se imprimen detalles internos de las excepciones.
- Una salida de consola ausente o fallida no lanza excepciones hacia EVA. Una
  consola lenta puede retrasar los diagnósticos y llenar su cola.
- Al cerrar se descartan textos pendientes sin esperar al trabajador. Una
  inferencia nativa ya iniciada no se puede cancelar desde Python: al terminar
  desecha su resultado y sale. El hilo daemon no impide terminar el proceso.
  El modelo cargado ocupa memoria durante la sesión; no existe recarga continua.

## Modelo y distribución

Se utiliza `modelos/intenciones_lr_v03.joblib`, copia binaria exacta del modelo
seleccionado en v03. El observador y el diagnóstico comparten la ruta de
`modelo_oficial.py`. Su ruta se resuelve respecto del
módulo, no del directorio de ejecución. No se busca un modelo alternativo ni se
descarga nada si falta.

La ejecución no necesita `experimentos/`. El modelo oficial y su manifiesto deben
incluirse en el repositorio y el instalador; véase [MODELO_OFICIAL.md](MODELO_OFICIAL.md).
La comprobación se realizó en una copia aislada sin experimentos. No se ha
construido ni comprobado todavía un instalador `.exe`.

## Verificaciones de esta etapa

La base disponible contiene 214 pruebas (incluye la etapa contextual y las
pruebas posteriores de diagnóstico con micrófono). Las pruebas del observador
usan texto sintético, captura/transcripción simuladas y el clasificador real.
No se grabó voz personal ni se abrió el micrófono durante estas verificaciones.

Las pruebas comparan las llamadas tradicionales de texto y voz con el procesador
anterior para instrucciones conocidas, desconocidas, incompletas, negativas y
compuestas. Cubren una carga y un hilo, productores concurrentes, saturación,
excepciones, cierre, ausencia de salida de voz adicional y Tkinter real oculto
respondiendo mientras el observador está ocupado.

Los tests históricos que congelaban `main.py` ahora comprueban su copia exacta
anterior en `tests/fixtures/observacion/main_anterior.py`. Una nueva prueba compara
el AST de las funciones conservadas con el `main.py` actual. Los hashes de los
modelos y demás módulos protegidos se siguen verificando sin cambios.

`tests/` continúa ignorado. Los resultados locales se encuentran en
`tests/resultado_observacion_regresion.txt`; la medición reproducible se realiza
con `tests/medir_observacion.py`, sin ejecutar `main.py` ni acciones.

Resultado: **235 pruebas aprobadas**, las 214 anteriores y 21 nuevas. Se comprobó
también `git diff --check`. No se instalaron dependencias ni se reentrenó el modelo.

### Medición local (5 de noviembre de 2026)

Procesos limpios separados, 20 calentamientos y 200 textos sintéticos alternando
origen escrito/voz; la etiqueta no ejecuta reconocimiento. Se mide working set
del proceso en Windows. La salida se recoge en memoria para excluir la velocidad
de la terminal. No se cambiaron parámetros de BLAS ni de Whisper.

| Métrica | Desactivado | Activado |
|---|---:|---:|
| RAM antes de recibir textos | 18,10 MiB | 18,05 MiB |
| RAM al terminar | 18,11 MiB | 115,68 MiB |
| Pico de RAM del proceso | 18,11 MiB | 115,75 MiB |
| Envío a la cola, mediana | 0,0001 ms | 0,0089 ms |
| Envío a la cola, p95 | 0,0002 ms | 0,0176 ms |
| Interpretación, mediana / p95 | No se realiza | 2,11 / 3,69 ms |
| Envío hasta resultado, mediana / p95 | No se realiza | 2,19 / 3,77 ms |
| Primera carga de modelo y dependencias | No se realiza | 2,27 s |

El primer resultado activado llegó en 2,30 s; la carga no se repite por comando.
El incremento aislado de memoria es de aproximadamente 98 MiB. No equivale a la
memoria total ni a la latencia de EVA con Whisper, pyttsx3 y servicios activos;
los procesos pueden compartir dependencias ya importadas y competir por CPU.
No se ha medido todavía esa competencia en uso real. Los valores inferiores
al microsegundo del modo desactivado son indicativos, no garantías temporales.

Pendiente de revisión manual: texto y micrófono en la aplicación completa con
esta conexión, respuesta de voz única, cierre durante carga y sensación de
fluidez con Whisper Small, Tkinter y pyttsx3 funcionando simultáneamente. Las dos
pruebas de micrófono de la etapa anterior validan el diagnóstico independiente,
pero no sustituyen esta comprobación de la integración.
