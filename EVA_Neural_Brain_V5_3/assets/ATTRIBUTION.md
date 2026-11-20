# Recursos 3D y condiciones de redistribución

**Obra original:** “Brain”, de **dgallichan (David Gallichan)**.

- Autor: https://sketchfab.com/dgallichan
- Fuente original: https://sketchfab.com/3d-models/brain-cadd2bde67404c43b2359a6a3281d84a
- Licencia declarada por el autor: **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
- Condiciones: https://creativecommons.org/licenses/by/4.0/
- Texto completo: [CC-BY-4.0.txt](CC-BY-4.0.txt), obtenido del repositorio público SPDX
  https://github.com/spdx/license-list-data/blob/main/text/CC-BY-4.0.txt

El autor indica que la malla fue generada con FreeSurfer desde una resonancia T1.
La publicación original identifica CC Attribution, y los metadatos `asset.extras`
del GLB identifican expresamente CC-BY-4.0, el autor y la misma URL original.

## Copia utilizada

NeuroPrint publica una versión simplificada/comprimida del mismo recurso y
conserva expresamente su atribución CC BY 4.0:

- Página: https://neuroprint.info/brain_3d.html
- Recurso: https://neuroprint.info/brain_model.glb
- Copia incluida: `source_brain.glb`, 663.972 bytes.
- SHA-256: `c73f599e76236ea99b79a5bef1ee8817f5e25835c251b109111909d74e6a63c8`.
- Verificación de procedencia y licencia: 17 de noviembre de 2026.

No se incorporaron el código, los textos educativos ni el diseño web de NeuroPrint.

## Adaptaciones para EVA V4

`brain_high.glb`, `brain_low.glb` y `surface_network.json` derivan de esa malla.
Se descomprimió Draco, se unificaron los fragmentos, se cambió el sistema de ejes
para una vista lateral, se centró y escaló a 260 unidades de ancho, se redujo
la geometría con agrupación espacial, se aplicó un suavizado Taubin moderado,
se recalcularon normales y se crearon trazas sobre aristas de la superficie.
Los materiales originales se sustituyen por shaders de EVA durante la ejecución.

Estos recursos derivados se distribuyen también bajo **CC BY 4.0**. Mantener
este archivo, el autor, la fuente, el enlace de licencia y la indicación de los
cambios al redistribuirlos. La licencia permite compartir y adaptar, incluido
uso comercial, cumpliendo las condiciones de atribución. No implica aprobación
de EVA por parte del autor o de NeuroPrint.

La malla es una referencia visual, no un modelo validado para uso médico. No
se alteró su proporción por separado para agrandar hemisferios, cerebelo o tallo.

Los archivos de video y las imágenes de referencia **no forman parte del paquete**.
La marca de agua del video no se ha usado ni recreado en los recursos de EVA.

## Reutilización en EVA V5

V5 conserva sin cambios los tres GLB y `surface_network.json` preparados para V4.
Sus materiales se sustituyen en ejecución por los shaders holográficos de V5.
El campo cósmico adicional se genera mediante coordenadas deterministas propias;
no procede del video de referencia. El video `previews/v5-demo.mp4` muestra
únicamente una ejecución de esta demostración, sin contenido de referencia.

## Reutilización en EVA V5.1

V5.1 conserva esos mismos GLB y la red superficial sin modificaciones. Los
refinamientos afectan a shaders, movimiento y composición generados por EVA.
Las capturas y grabaciones de `previews/` muestran la demo; no incorporan
fotogramas ni marcas de agua del video de referencia.

## Reutilización en EVA V5.2

V5.2 conserva los mismos recursos geométricos y sus licencias. Los cambios de
esta fase se limitan a circuitos, lluvia binaria y presentación generada por EVA.

## Reutilización en EVA V5.3

V5.3 conserva los mismos GLB y la red superficial, sin cambios de geometría ni
licencia. `binary_glyphs.svg` contiene trazos propios para los dígitos 0 y 1;
la lluvia Matrix se genera con el shader de EVA. No se incorporaron imágenes,
tipografías ni fotogramas de una referencia externa.
