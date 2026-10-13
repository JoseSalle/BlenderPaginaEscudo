# Vigilia — estudio de un escudo

Escudo medieval original y editable: siete tablones curvados de roble oscuro, marco y travesaños de acero, rosa geométrica de ocho puntas y remaches de bronce envejecido. El reverso incorpora dos soportes y una empuñadura de madera con collares de bronce.

El visor usa HTML, CSS y JavaScript sin framework ni compilación. Todos los recursos de ejecución, incluida la distribución oficial de **model-viewer 4.1.0**, se sirven desde el propio repositorio.

- Repositorio: https://github.com/JoseSalle/BlenderPaginaEscudo
- [Página publicada y verificada](https://josesalle.github.io/BlenderPaginaEscudo/).
- Rama: `main`. La inspección inicial no encontró commits ni referencias remotas. Se eligió `main` según la consigna; la API de GitHub también devolvió `main` como rama predeterminada. No había archivos o instrucciones que conservar ni una configuración de Pages existente.

## Archivos

```text
index.html                         Página principal
styles.css                         Diseño adaptable y estados de foco
app.js                             Carga y tres controles de materiales
assets/models/escudo_vigilia.glb     Modelo autocontenido para la web
assets/textures/                    Mapas PBR originales y ORM
assets/vendor/                     model-viewer 4.1.0 y licencias
source/escudo_vigilia.blend          Fuente editable con imágenes empaquetadas
scripts/generate_textures.py        Generación reproducible de mapas
scripts/build_shield.py             Modelado, UV, materiales y exportación
scripts/inspect_glb.py              Inspección de estructura y tamaños
scripts/verify_blender.py           Apertura de fuente y reimportación de GLB
scripts/test_browser.cjs            Pruebas funcionales en navegador
docs/                              Informes de verificación
```

## Abrir y ejecutar

Abre `source/escudo_vigilia.blend` en **Blender 5.2.0 LTS**. Las cuatro colecciones agrupan madera, estructura, ornamentos y agarre. Los 45 objetos y sus mallas tienen nombres descriptivos. Las imágenes iniciales están empaquetadas en el archivo; activa Vista de materiales para examinarlas. La escala es métrica: aproximadamente 1,15 m de alto, 0,89 m de ancho y 0,25 m de profundidad total con el agarre.

Desde la raíz del repositorio, con Python 3:

```sh
python -m http.server 8000
```

Abre http://localhost:8000/ . No abras `index.html` con `file://`: los módulos y las texturas requieren HTTP. No es necesario instalar npm para usar la página. Las rutas relativas funcionan en el subdirectorio de GitHub Pages.

## Los tres botones

1. **Madera limpia / desgastada:** cambia simultáneamente Base Color, ORM (rugosidad en verde, metalicidad en azul) y Normal. Las marcas, la decoloración localizada y la rugosidad proceden de mapas distintos; no de un cambio global de color.
2. **Cambiar tono del acero:** multiplica el color por un tono oscuro y restaura el factor original. Conserva el mapa y factor metálicos, rugosidad y normales.
3. **Relieve del bronce:** usa `normalTexture.setTexture(null)` y restaura la referencia original. El relieve de superficie es independiente de la silueta geométrica del emblema.

Los materiales se buscan por `Madera`, `Acero` y `Bronce` dentro del evento `load`, con `model.getMaterialByName`. Se guardan las referencias iniciales y se precargan los tres mapas alternativos una sola vez con `createTexture`. Cada botón modifica únicamente su material mediante la API pública. Los ocho estados pueden combinarse y restaurarse sin volver a cargar el GLB.

Los controles permanecen deshabilitados hasta completar la preparación, tienen `aria-pressed`, foco visible y respuesta a Enter/Espacio. El visor permite arrastrar, hacer zoom con rueda o pellizco y usar sus controles de teclado. Los mensajes de estado se anuncian con `aria-live`; los fallos de carga muestran una explicación.

## Modelado, UV y texturizado

- Silueta ancha arriba y apuntada abajo; curvatura frontal de unos 9,7 cm en el centro. Tablones de 3,8 cm de espesor. Marco hueco continuo, sin una segunda placa interior completa.
- Biseles de dos segmentos. Esferas de resolución moderada para remaches, y más segmentos solo para el umbo central. No se usan subdivisiones para simular vetas o rayas.
- Mallas cerradas con normales recalculadas, transformaciones de escala aplicadas y un modificador de triangulación para exportar tangentes estables. Se conservan polígonos editables en la fuente.
- Acero y bronce: Smart UV Project de las piezas de cada material, densidad normalizada con Average Islands Scale, empaquetado conjunto sin rotación y margen relativo de 0,016. Las discontinuidades reales de UV quedan marcadas como costuras para editar.
- Madera: proyección frontal proporcional a metros para mantener las vetas verticales y una densidad uniforme entre tablones. El reverso reutiliza **intencionalmente** el mismo espacio de textura. Los biseles, laterales y puño reutilizan también regiones de este material genérico con sus UV desplegadas; no hay AO ni pintura exclusiva de una pieza que pueda contaminar otra. El margen de la proyección principal es 0,04. En metales se prioriza densidad consistente dentro de cada atlas, no idéntica entre materiales.
- Los mapas son imágenes reales creadas por `generate_textures.py`, con semilla fija 1847. Se combinan ruido a distintas frecuencias, vetas direccionales, pátina y trazos de desgaste. No se usan recursos gráficos externos.
- **No se realizó bake de una malla de alta resolución.** La apariencia procedural se rasteriza directamente a PNG; el mapa normal tangente se calcula a partir de derivadas de altura. Este flujo no deja nodos procedurales exclusivos de Blender en el resultado.
- Base Color: **sRGB**. Roughness, Metallic y Normal: **Non-Color**. Normales tangentes **OpenGL / +Y**, compatibles con glTF. El signo del canal verde considera que las filas PNG aumentan hacia abajo y V aumenta hacia arriba.
- Materiales Principled BSDF con imágenes conectadas directamente. El exportador combina Roughness y Metallic; ambos originales permanecen por separado. ORM adicional: R=1 (sin AO horneado), G=roughness, B=metallic.
- Exportación seleccionada a GLB sin cámaras ni luces, con UV, normales, tangentes y orientación Y-up. Blender usa frente -Y y vertical +Z; el GLB queda con frente +Z y vertical +Y.

## Presupuesto real

| Dato | Resultado |
|---|---:|
| Triángulos exportados | 9.064 |
| Objetos / mallas | 45 |
| Materiales | 3 |
| Resolución de todos los mapas | 512 × 512 |
| PNG originales | 20: cuatro juegos × cinco mapas |
| Imágenes embebidas en GLB | 9 |
| GLB | 2.324.408 bytes / 2,324 MB |
| Fuente Blender | 1.452.703 bytes / 1,453 MB |
| PNG originales en conjunto | 1.960.788 bytes / 1,961 MB |
| Distribución model-viewer | 979.139 bytes |

Los cuatro juegos son madera limpia, madera desgastada, acero y bronce; cada uno contiene Base Color, Roughness, Metallic, Normal y ORM. No se aplica Draco, Meshopt ni KTX2. Se comparten tres materiales y nueve imágenes embebidas para evitar texturas duplicadas por objeto. Las cifras exactas se regeneran en `docs/asset-report.json`.

## Reproducir

Requisitos de generación: Blender 5.2.0 LTS, Python 3, NumPy y Pillow. El visor no necesita estas herramientas.

```sh
python -m pip install -r scripts/requirements-textures.txt
python scripts/generate_textures.py
blender --background --python-exit-code 1 --python scripts/build_shield.py
python scripts/inspect_glb.py
blender --background --python-exit-code 1 --python scripts/verify_blender.py
```

En Windows, si Blender no está en PATH, usa `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"` en PowerShell. La generación reemplaza los archivos generados: guarda aparte cualquier edición manual que quieras conservar antes de repetirla. El script crea una carpeta `work/temp` ignorada por Git para temporales del exportador.

Para exportar modificaciones manuales sin reconstruir: selecciona solo las mallas de las cuatro colecciones, Archivo → Exportar → glTF 2.0, formato GLB, Selected Objects, Apply Modifiers, UVs, Normals, Tangents, Materials y +Y Up. Guarda en `assets/models/escudo_vigilia.glb`. Conserva los nombres exactos de los tres materiales.

## Verificación

La fuente se abrió de nuevo en Blender y el GLB se reimportó en una escena vacía. Se verificaron 45 mallas y tres materiales, sin aristas no manifold, caras degeneradas, UV ausentes o escalas sin aplicar. El inspector GLB comprueba tangentes, UV, mapas PBR, tamaño y resolución de imágenes embebidas.

Pruebas en Chrome 155 mediante servidor HTTP: ocho combinaciones de materiales, tres recorridos completos (27 comprobaciones de estado), restauración de las referencias originales, teclado, cuatro anchos (390, 768, 1024 y 1440 px), sin desbordamiento horizontal, sin errores de consola ni recursos faltantes en la carga normal. Se simuló también una descarga GLB fallida para comprobar el mensaje y los botones desactivados. Revisión visual del frente, reverso, madera desgastada, acero oscuro y diseño móvil.

Para repetir la prueba funcional, instala Playwright como herramienta de desarrollo (no se publica):

```sh
npm install --no-save playwright
npx playwright install chromium
node scripts/test_browser.cjs http://localhost:8000/
```

Si ya existe Chrome, se puede indicar `CHROME_PATH` y evitar descargar Chromium. `PLAYWRIGHT_MODULE` permite resolver una instalación externa. Los informes JSON están en `docs/`; las capturas temporales se guardan en `work/qa`, excluida de Git.

Las mismas pruebas pasaron también en la URL pública de GitHub Pages el 13 de octubre de 2026. La página, GLB, fuente Blender y las tres texturas alternativas devolvieron HTTP 200 y coincidieron byte por byte con los archivos locales. Informes: `docs/browser-verification-local.json`, `docs/browser-verification.json` (público) y `docs/published-assets.json`.

Límite de las pruebas: se verificó el diseño móvil mediante tamaños de ventana de Chrome, no en dispositivos iOS/Android físicos. No se implementó AR, al no formar parte de la consigna. No quedan pendientes de implementación o publicación.

## Publicación

GitHub Pages quedó configurado desde la raíz `/` de `main`, con HTTPS. `.nojekyll` permite servir los archivos estáticos directamente. Los futuros pushes a `main` actualizan la publicación. No se modificó la visibilidad del repositorio ni se utilizó force push.

Para revisar o restablecer esta configuración: GitHub → Settings → Pages → Build and deployment → Deploy from a branch → `main` → `/ (root)` → Save. Espera a que termine el despliegue y abre el enlace que GitHub muestre. Los scripts y el `.blend` también se pueden descargar desde el sitio estático.

## Fuentes y atribuciones

- [model-viewer oficial](https://modelviewer.dev/), [documentación](https://modelviewer.dev/docs/) y [ejemplos de materiales](https://modelviewer.dev/examples/scenegraph/).
- [API pública fijada al tag v4.1.0](https://github.com/google/model-viewer/blob/v4.1.0/packages/model-viewer/src/features/scene-graph/api.ts): `getMaterialByName`, `setTexture`, `setBaseColorFactor` y las propiedades PBR.
- [Ejemplos del tag v4.1.0](https://github.com/google/model-viewer/blob/v4.1.0/packages/modelviewer.dev/examples/scenegraph/index.html): `createTexture` y conservación de referencias.
- [Manual de exportación glTF de Blender](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html).
- [API de GitHub Pages](https://docs.github.com/en/rest/pages/pages).

Modelo, emblema, texturas, icono e interfaz creados para este proyecto. No hay modelos, fotografías ni tipografías descargadas. Las fuentes tipográficas son del sistema.

model-viewer se distribuye bajo Apache-2.0. Su archivo oficial se conserva sin modificar, incluidos sus avisos internos. El paquete integra dependencias como Three.js (MIT), Lit (BSD-3-Clause) y gainmap-js (MIT). Las licencias y la procedencia con SHA-256 están en `assets/vendor/`. No se impone una nueva licencia a los archivos originales del titular del repositorio.
