# AGENTS.md — Cerebro de investigación de accidentes laborales

Este documento es el **esquema** del cerebro. Le dice al agente (Cursor, Claude
Code, Codex, etc.) cómo está organizado el conocimiento, qué convenciones seguir
y qué flujos de trabajo aplicar. El objetivo es que el agente actúe como un
**mantenedor disciplinado de una wiki**, no como un chatbot genérico.

Idioma de todo el contenido: **español**.

## 1. Propósito

Este proyecto es un cerebro especializado en **investigación de accidentes de
trabajo** y en la **determinación de medidas preventivas**. Se construye sobre el
corpus **BINVAC** del INSST ("Accidentes de Trabajo Investigados") y crece con
nuevos casos que aportan expertos.

Sirve para dos cosas:

1. **Referencia**: una wiki interconectada que acumula patrones (agentes
   materiales, formas de accidente, desviaciones, causas y un catálogo
   reutilizable de medidas preventivas).
2. **Asistente de investigación**: dado un accidente nuevo, ayuda a investigarlo
   de forma estructurada y a proponer las medidas preventivas más adecuadas,
   apoyándose en el conocimiento acumulado.

## 2. Arquitectura de tres capas

- **Fuentes crudas (`raw/`)**: PDFs BINVAC del INSST. **Inmutables**: el agente
  lee de aquí pero NUNCA las modifica. No se versionan en Git (ver `.gitignore`);
  se regeneran con `python download_binvac.py`.
- **La wiki (`wiki/`)**: archivos markdown generados y mantenidos por el agente.
  El agente es el **único** que escribe aquí. El humano lee.
- **El esquema (este `AGENTS.md`)**: las reglas. Se co-evoluciona con el usuario.

## 3. Estructura de la wiki

```
wiki/
  index.md               # catálogo de todas las páginas (se actualiza en cada ingesta)
  log.md                 # registro cronológico append-only
  overview.md            # qué es el cerebro y cómo se usa
  sources/               # una página por ficha BINVAC (auto-extraída con el script)
  agentes-materiales/    # entidad por agente material (grúas, escaleras, vehículos...)
  sectores/              # por actividad económica (CNAE)
  formas/                # por forma/modalidad de la lesión (atrapamiento, caída...)
  desviaciones/          # por tipo de desviación (vuelco, pérdida de control...)
  causas/                # taxonomía de causas recurrentes
  medidas-preventivas/   # CATÁLOGO reutilizable de medidas (núcleo del valor)
  patrones/              # síntesis: combinaciones recurrentes y lecciones transversales
  investigaciones/       # investigaciones de accidentes NUEVOS (salida del asistente)
  plantillas/            # plantillas de ficha, de medida y de investigación
```

## 4. Convenciones de las páginas

- **Frontmatter YAML** en toda página, para navegación y Dataview. Campos según
  el tipo (ver plantillas en `wiki/plantillas/`). Incluir siempre `tags`.
- **Enlaces internos** estilo wiki: `[[nombre-de-archivo-sin-extension]]` o con
  alias `[[archivo|texto visible]]`. Interconectar generosamente: cada página
  relevante debe enlazar a las entidades, causas y medidas que menciona.
- **Nomenclatura de archivos**: minúsculas, sin acentos, palabras separadas por
  guiones. Ej.: `gruas-y-equipos-de-elevacion.md`, `caida-de-altura.md`,
  `desplegar-estabilizadores.md`. Las fuentes conservan su código: `BINVAC_018.md`.
- Cada página termina con una sección `## Enlaces` o `## Fichas relacionadas` que
  lista sus conexiones cuando aporte valor.
- **Bloques automáticos**: el script `scripts/sync_links.py` mantiene secciones
  delimitadas por `<!-- AUTO:NOMBRE:START/END -->`. No editar esos bloques a mano.
- **Síntesis manual**: páginas curadas llevan `sintesis: manual` en el frontmatter;
  el sync no sobrescribe su cuerpo narrativo.
- **Registro canónico**: `data/canonical_registry.yaml` mapea códigos ESAW/CNAE a
  slugs de entidad. Actualizarlo al crear entidades nuevas en la síntesis.

## 5. Taxonomías del dominio

### 5.1 Codificación del accidente (tipo ESAW, en las fichas BINVAC)
Presente en el frontmatter de las páginas de `sources/` cuando la ficha lo trae:
`cnae` (actividad económica), `actividad_fisica`, `desviacion`, `forma`
(modalidad de la lesión), `agente_actividad`, `agente_desviacion`,
`agente_lesion`. Algunas fichas antiguas no traen esta tabla estructurada; en ese
caso su texto original queda en la sección "Datos del accidente" de la fuente y el
agente puede inferir la clasificación desde la descripción si es útil.

### 5.2 Categorías de causas (agrupación BINVAC habitual)
- Ausencia o deficiencias en los elementos de protección.
- Organización del trabajo y gestión de la prevención.
- Formación e información.
- Características del lugar / superficie de trabajo.
- Factores individuales / comportamiento.
- Deficiencias del equipo de trabajo (RD 1215/1997).

La taxonomía se refina a partir del corpus; usa `wiki/causas/` como fuente única.

### 5.3 Jerarquía de las medidas preventivas (art. 15 LPRL)
Al proponer o catalogar medidas, clasificar siempre por jerarquía y priorizar de
arriba abajo:
1. **Eliminación** del peligro.
2. **Sustitución** por algo menos peligroso.
3. **Medidas de ingeniería** / protección colectiva.
4. **Medidas organizativas / administrativas** (procedimientos, formación,
   coordinación de actividades empresariales, recurso preventivo).
5. **EPI** (protección individual) como último recurso.

## 6. Flujo: INGEST (incorporar una ficha o caso)

Cuando el usuario pida procesar una fuente (o lote):

1. **Extraer**: si es un PDF BINVAC nuevo en `raw/`, ejecutar
   `python scripts/extract_fichas.py raw/BINVAC_NNN.pdf` para generar
   `wiki/sources/BINVAC_NNN.md`. Revisar el resultado frente al PDF y corregir
   ruido (pies de foto, cortes) si es necesario.
2. **Recuperar ESAW** (fichas antiguas): `python scripts/recover_esaw.py` para
   rellenar campos de texto desde `datos_raw` cuando falten códigos.
3. **Sincronizar enlaces**: `python scripts/sync_links.py` genera enlaces
   bidireccionales fuente ↔ entidad en bloques AUTO.
4. **Comentar** con el usuario los puntos clave del caso.
5. **Actualizar la síntesis** (una sola pasada puede tocar 10-15 páginas):
   - Crear/actualizar la página de cada **agente material** implicado.
   - Crear/actualizar la página de la **forma** y la **desviación**.
   - Crear/actualizar la página del **sector** (CNAE).
   - Registrar cada **causa** en `wiki/causas/` (enlazando la ficha).
   - Añadir cada **medida preventiva** al catálogo `wiki/medidas-preventivas/`
     (si ya existe una equivalente, enlazar y reforzar, no duplicar).
   - Actualizar `wiki/patrones/` si aparece una combinación recurrente.
6. **Marcar contradicciones**: si el caso contradice algo ya escrito, anotarlo
   explícitamente en la página afectada.
7. **Índice, lint y registro**: `python scripts/build_index.py`,
   `python scripts/lint_wiki.py`, y añadir entrada a `wiki/log.md`.

## 7. Flujo: INVESTIGAR un accidente nuevo (protocolo)

Cuando el usuario describa un accidente a investigar:

1. **Recoger datos**: tarea que se realizaba, secuencia de los hechos, agentes
   materiales, lesión/consecuencias, contexto (sector, organización, empresas
   concurrentes). Preguntar lo que falte; no inventar.
2. **Codificar** (tipo ESAW): actividad física, desviación, forma y agentes
   materiales, para poder comparar con el corpus.
3. **Buscar similares**: localizar en `wiki/` fichas, patrones **e
   investigaciones anteriores** con el mismo agente material / forma /
   desviación. Empezar por `index.md` (fichas BINVAC) y revisar siempre
   también `wiki/investigaciones/README.md` (casos no-BINVAC investigados
   con este mismo protocolo), ya que `index.md` no los incluye
   automáticamente.
4. **Análisis de causas** hasta causa raíz (p. ej. árbol de causas / 5 porqués),
   clasificándolas según la taxonomía de `wiki/causas/`. Distinguir causas
   inmediatas, básicas y de gestión.
5. **Proponer medidas preventivas** priorizadas por la jerarquía del art. 15
   LPRL, reutilizando el catálogo `wiki/medidas-preventivas/` y adaptándolas al
   caso. Citar las fichas de las que provienen.
6. **Archivar**: guardar la investigación como página en `wiki/investigaciones/`
   con su frontmatter, enlazar a las entidades/causas/medidas usadas, actualizar
   `index.md` y `log.md`. Los buenos análisis se quedan en la wiki, no en el chat.

## 8. Flujo: QUERY (responder preguntas)

Leer primero `index.md`, luego las páginas relevantes, y sintetizar con **citas**
a las páginas de la wiki y a las fichas fuente. Si la respuesta es valiosa y
reutilizable, ofrecer archivarla como página nueva (patrón, comparativa, etc.).

## 9. Flujo: LINT (salud de la wiki)

Cuando se pida una revisión, buscar y proponer correcciones para:
- Contradicciones entre páginas y afirmaciones obsoletas.
- Páginas huérfanas (sin enlaces entrantes) y enlaces rotos (`scripts/lint_wiki.py`).
- Conceptos mencionados sin página propia.
- Medidas duplicadas en el catálogo (fusionar).
- Referencias cruzadas que faltan.
- Bloques AUTO desincronizados (`python scripts/sync_links.py --check`).
- Huecos de datos que podrían cubrirse con nuevas fuentes o búsqueda web.

## 10. Registro (`log.md`)

Append-only. Cada entrada empieza con un prefijo parseable:
`## [AAAA-MM-DD] tipo | Título` donde tipo ∈ {ingest, query, investigacion,
lint}. Así `grep "^## \[" wiki/log.md | tail -5` da lo más reciente.

## 11. Reglas de oro

- Nunca modificar `raw/`. Nunca inventar datos de un accidente: si falta, se
  pregunta o se marca como desconocido.
- No duplicar: antes de crear una página, comprobar si ya existe una equivalente.
- Toda afirmación relevante debe poder rastrearse hasta una ficha fuente.
- Mantener `index.md` y `log.md` al día en cada operación de escritura.
