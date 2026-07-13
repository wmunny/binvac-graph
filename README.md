# Cerebro de investigación de accidentes laborales (BINVAC)

Proyecto de investigación colaborativo: un **cerebro** (wiki de markdown mantenida
por IA) especializado en **investigación de accidentes de trabajo** y en la
**determinación de medidas preventivas**. Se construye sobre el corpus **BINVAC**
del INSST y crece con casos que aportan expertos.

La idea sigue el patrón "LLM Wiki": en lugar de solo recuperar fragmentos de los
PDFs en cada pregunta (RAG), un agente lee las fuentes y **construye y mantiene**
una wiki estructurada e interconectada. El conocimiento se compila una vez y se
mantiene al día. Ver [`AGENTS.md`](AGENTS.md) para el esquema y los flujos.

## Estructura

```
raw/                     # PDFs BINVAC (fuente inmutable; NO se versiona, ver .gitignore)
download_binvac.py       # descarga el catálogo BINVAC a raw/
scripts/
  extract_fichas.py      # PDF -> wiki/sources/BINVAC_NNN.md (normalizado)
  build_index.py         # regenera wiki/index.md desde el frontmatter de las fuentes
AGENTS.md                # esquema del cerebro: convenciones y flujos de trabajo
wiki/                    # la wiki (la escribe el agente; tú la lees)
  index.md  log.md  overview.md
  sources/ agentes-materiales/ sectores/ formas/ desviaciones/
  causas/ medidas-preventivas/ patrones/ investigaciones/ plantillas/
```

## Puesta en marcha

Requiere Python 3.10+.

```bash
pip install -r requirements.txt
python download_binvac.py        # descarga las fichas BINVAC a raw/
python scripts/extract_fichas.py # genera las páginas de fuente en wiki/sources/
python scripts/build_index.py    # genera wiki/index.md
```

## Cómo usar el cerebro

1. Abre el proyecto con un agente (Cursor / Claude Code / Codex). El agente lee
   `AGENTS.md` y sabe cómo mantener e interrogar la wiki.
2. Abre `wiki/` en **Obsidian** para navegar (enlaces, vista de grafo, Dataview).
   El agente escribe; tú lees.

Ejemplos de peticiones al agente:
- "Investiga este accidente: <descripción>" → sigue el protocolo de `AGENTS.md`
  y archiva el resultado en `wiki/investigaciones/`.
- "¿Qué medidas son típicas para vuelcos de maquinaria de elevación?"
- "Ingiere la ficha `raw/BINVAC_045.pdf`."

## Usarlo como plantilla en tu propia empresa

Este repositorio está pensado para poder clonarse y reutilizarse tal cual,
como punto de partida para el cerebro de investigación de accidentes de
**otra empresa o técnico**. Al clonarlo obtienes de entrada el método
(`AGENTS.md`, `scripts/`, `wiki/plantillas/`) y el conocimiento ya sintetizado
del corpus BINVAC (agentes materiales, causas, medidas, patrones), sobre el
que empiezas a construir tus propios casos.

1. **Clónalo o usa "Use this template" en GitHub** (si el repo está publicado
   allí como plantilla) para obtener tu propia copia independiente.
2. **Instala dependencias** y regenera `raw/` si quieres las fichas BINVAC en
   PDF (no se versionan): ver "Puesta en marcha" más arriba.
3. **Empieza a investigar tus propios accidentes** pidiéndoselo al agente
   ("Investiga este accidente: ...") o aportando fichas propias con
   [`wiki/plantillas/aportacion-caso.md`](wiki/plantillas/aportacion-caso.md).

Este uso es **totalmente privado**: tu copia y tus casos se quedan en tu
repositorio; nada se comparte salvo que tú decidas abrir un PR al repositorio
original (ver siguiente sección).

## ¿Un conocimiento compartido entre empresas?

Cada empresa que use esta plantilla acumulará, con el tiempo, sus propios
patrones, causas y medidas. Sería valioso poder compartir esa síntesis (no
necesariamente los casos en crudo) entre organizaciones para que el catálogo
de medidas preventivas crezca más rápido que lo que cada una podría acumular
por sí sola.

De momento esto es **una idea abierta, no un proceso ya construido**. Antes de
definir cómo debería funcionar (qué se anonimiza, qué nivel de revisión hace
falta, si tiene sentido un catálogo separado de los casos privados, etc.),
preferimos comprobar si hay interés real. Si te interesaría contribuir a un
catálogo común o beneficiarte de uno, abre un *issue* o una *discusión* en
este repositorio contándolo — según el interés que haya,
diseñaremos el mecanismo de contribución compartida (probablemente una
versión ampliada de [`CONTRIBUTING.md`](CONTRIBUTING.md) con un filtro de
anonimización y revisión).

## Contribuir

Este proyecto está pensado para crecer con nuevos casos. Consulta
[`CONTRIBUTING.md`](CONTRIBUTING.md) para el flujo de aportación (hoy pensado
sobre todo para hacer crecer tu propia copia; la contribución compartida
entre empresas está en fase de validar interés, ver sección anterior).

## Fuente y licencia

El código y el método (`AGENTS.md`, `scripts/`, plantillas, estructura de la
wiki) se publican bajo licencia [MIT](LICENSE): puedes clonarlos, adaptarlos y
reutilizarlos libremente, también con fines comerciales. Ver [`NOTICE.md`](NOTICE.md)
para la atribución de las fichas BINVAC (INSST) y de los casos aportados por
terceros, que no se rigen por la MIT.

Este cerebro es una herramienta de apoyo; la aplicación de sus contenidos a
situaciones concretas debe ser evaluada por profesionales competentes en
Prevención de Riesgos Laborales.
