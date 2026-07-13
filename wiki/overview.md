---
tipo: overview
tags:
  - overview
---

# Cerebro de investigación de accidentes laborales

Este es un cerebro (wiki mantenida por IA) especializado en **investigación de
accidentes de trabajo** y **determinación de medidas preventivas**, construido
sobre el corpus **BINVAC** del INSST y ampliable con casos aportados por expertos.

## Qué puedes hacer con él

- **Investigar un accidente nuevo**: descríbeselo al agente y seguirá el
  protocolo de `AGENTS.md` (recoger datos → codificar → buscar similares →
  análisis de causas → medidas preventivas priorizadas) y archivará el resultado
  en [[investigaciones]].
- **Consultar patrones**: qué causas y medidas son típicas para un agente
  material, una forma de accidente o un sector.
- **Ampliar el conocimiento**: incorporar nuevas fichas o casos (flujo Ingest).

## Cómo está organizado

- [[index]] — catálogo de todas las fichas y vistas agrupadas por forma,
  desviación, agente material y sector.
- `sources/` — una página por ficha BINVAC (fuente).
- `agentes-materiales/`, `formas/`, `desviaciones/`, `sectores/` — entidades.
- `causas/` — taxonomía de causas recurrentes.
- `medidas-preventivas/` — catálogo reutilizable de medidas (el núcleo del valor).
- `patrones/` — combinaciones recurrentes y lecciones transversales.
- [[log]] — registro cronológico de la evolución del cerebro.

## Cómo usarlo (flujo recomendado)

1. Abre este proyecto con un agente (Cursor / Claude Code / Codex). El agente lee
   `AGENTS.md` y sabe cómo mantener e interrogar la wiki.
2. Ten Obsidian abierto sobre la carpeta `wiki/` para navegar (enlaces, vista de
   grafo, Dataview). El agente escribe; tú lees.

## Estado actual

- 103 fichas BINVAC ingeridas como fuentes, con **enlaces automáticos** a entidades
  canónicas (`scripts/sync_links.py`).
- **5 patrones transversales** y síntesis por lotes: vuelco, caídas en obra,
  carretillas, contacto eléctrico y cintas transportadoras.
- Catálogo ampliado: 10 causas y 10 medidas reutilizables.
- El accidente [[BINVAC_018]] sigue siendo el ejemplo de síntesis completa manual.
