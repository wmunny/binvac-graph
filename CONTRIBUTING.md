# Cómo contribuir

Este cerebro crece con nuevos casos de investigación de accidentes. Gracias por
aportar. El flujo está pensado para que el trabajo pesado (resumir, clasificar,
interconectar) lo haga el agente siguiendo [`AGENTS.md`](AGENTS.md); tú aportas el
caso y revisas.

> **Nota sobre el alcance actual**: el flujo de abajo está pensado y probado
> para ampliar el corpus con fichas BINVAC (ya anonimizadas por el INSST) y
> para que cada quien haga crecer **su propia copia** del cerebro con sus
> casos. Compartir casos propios de una empresa en este repositorio, para que
> alimenten un conocimiento común entre organizaciones, es todavía una idea
> abierta (ver "¿Un conocimiento compartido entre empresas?" en el
> [README](README.md)). Si quieres proponer un caso propio para el
> conocimiento común, abre primero un issue/discusión para comentarlo antes
> del PR: aún no hay un filtro de anonimización ni una revisión definidos
> para ese escenario, y preferimos definirlos con casos reales de por medio.

## Flujo para aportar un caso

1. **Añade la fuente**
   - Si es una ficha BINVAC en PDF, colócala en `raw/`. (Recuerda: `raw/` no se
     versiona; se regenera con `download_binvac.py`. Para casos propios que deban
     conservarse, su síntesis vive en `wiki/sources/`, que sí se versiona.)
   - Si no tienes PDF, redacta el caso con la plantilla
     [`wiki/plantillas/aportacion-caso.md`](wiki/plantillas/aportacion-caso.md).

2. **Procesa con el agente (flujo Ingest de `AGENTS.md`)**
   - Para un PDF BINVAC: `python scripts/extract_fichas.py raw/BINVAC_NNN.pdf` y
     luego pide al agente que ingiera la ficha.
   - El agente creará/actualizará la página de fuente y la síntesis (agentes,
     formas, desviaciones, causas, catálogo de medidas, patrones) y actualizará
     `wiki/index.md` y `wiki/log.md`.
   - Alternativamente: `python scripts/build_index.py` regenera el índice.

3. **Revisa y abre un Pull Request**
   - Comprueba que la síntesis es coherente y no duplica páginas existentes.
   - Un revisor validará el caso antes de fusionar.

## Convenciones

- Idioma: **español**.
- No edites a mano `wiki/index.md` (se genera con `scripts/build_index.py`).
- Ten en cuenta que `scripts/extract_fichas.py` **regenera** las páginas de
  `wiki/sources/`; no hagas ediciones manuales que no quieras perder ahí. La
  síntesis y los matices van en las páginas de categoría, no en las fuentes.
- Sigue las convenciones de nomenclatura y frontmatter descritas en `AGENTS.md`
  (sección 4) y usa las plantillas de `wiki/plantillas/`.
- No incluyas datos personales de las personas accidentadas.

## Estructura del repositorio

Ver [`README.md`](README.md) y [`AGENTS.md`](AGENTS.md).
