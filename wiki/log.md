---
tipo: log
tags:
  - log
---

# Registro (log)

Registro cronológico append-only. Cada entrada:
`## [AAAA-MM-DD] tipo | Título` (tipo ∈ ingest, query, investigacion, lint).

## [2026-07-13] ingest | Corpus BINVAC inicial (103 fichas)
Descargadas 103 fichas BINVAC del INSST a `raw/` y extraídas a `wiki/sources/`
con `scripts/extract_fichas.py`. 72 con codificación ESAW completa; 31 de
maquetación antigua conservan sus datos en texto. Generado `index.md`.

## [2026-07-13] ingest | Síntesis de ejemplo: BINVAC_018 (grúa autocargante)
Desarrollada la síntesis completa del caso 018 (atrapamiento por vuelco de grúa
autocargante): entidad del agente material, forma, desviación, sector, causas y
varias medidas en el catálogo, más un patrón transversal.

## [2026-07-13] lint | Interrelaciones semánticas del corpus BINVAC
Implementada infraestructura de enlaces bidireccionales: registro canónico ESAW
(`data/canonical_registry.yaml`), `scripts/sync_links.py`, `scripts/recover_esaw.py`,
`scripts/lint_wiki.py` y refactor de `scripts/build_index.py` (agrupación por código).
103 fuentes con bloques AUTO de clasificación y enlaces. Cinco lotes temáticos
sintetizados (vuelco, caídas en obra, carretillas, electricidad, cintas). Catálogo
ampliado a 10 causas y 10 medidas. 5 patrones transversales.

## [2026-07-13] investigacion | Vuelco de carretilla con big bag en sector alimentario
Investigado un accidente nuevo (no BINVAC) aportado por un usuario: carretilla
elevadora con big bag colgado de las horquillas, vuelco, conductor atrapado bajo
la máquina, sector alimentario. Caso prácticamente gemelo de [[BINVAC_002]];
también relacionado con [[BINVAC_056]] y [[BINVAC_098]]. Archivado en
`wiki/investigaciones/vuelco-carretilla-big-bag-sector-alimentario.md`, con
árbol de causas (5 porqués) y medidas priorizadas según el art. 15 LPRL.
Creada nueva medida de catálogo
[[medidas-preventivas/uso-permanente-cinturon-seguridad-carretillas]] y
reforzado el patrón [[patrones/perdida-de-control-carretillas]]. Datos
desconocidos (fecha, empresa, tarea exacta) marcados explícitamente como tales,
sin inventar.

## [2026-07-13] investigacion | Atrapamiento de mano en prensa plegadora (taller metalúrgico)
Investigado un accidente nuevo (no BINVAC) aportado por un usuario: operario de
prensa plegadora introduce la mano izquierda entre el punzón y la matriz para
corregir la alineación de una chapa de 2 mm; su pie derecho acciona el pedal por
accidente y sufre atrapamiento y aplastamiento de los dedos. Relacionado con
[[BINVAC_019]] (resguardos insuficientes en perfiladora), [[BINVAC_014]]
(exceso de confianza, enclavamiento anulado) y [[BINVAC_047]] (pedal sin mando
bimanual). Archivado en
`wiki/investigaciones/atrapamiento-mano-prensa-plegadora-taller-metalurgico.md`,
con árbol de causas (5 porqués) y medidas priorizadas según el art. 15 LPRL.
Ampliado el catálogo con tres causas nuevas
([[causas/ausencia-o-anulacion-de-resguardos-en-punto-de-operacion]],
[[causas/accionamiento-por-pedal-sin-mando-bimanual]],
[[causas/introduccion-de-manos-por-exceso-de-confianza]]) y tres medidas nuevas
([[medidas-preventivas/resguardos-optoelectronicos-y-enclavados-en-punto-de-operacion]],
[[medidas-preventivas/sustitucion-de-pedal-por-mando-bimanual]],
[[medidas-preventivas/procedimiento-de-parada-y-utillaje-para-reposicionar-piezas]]).
Creado el patrón transversal
[[patrones/atrapamiento-en-punto-de-operacion-de-maquinas]]. Datos desconocidos
(empresa, CNAE exacto, estado real de los resguardos de la prensa) marcados
explícitamente como tales, sin inventar.

## [2026-07-13] investigacion | Atrapamiento por guante en torno convencional (taller de mecanizado)
Investigado un accidente nuevo (no BINVAC) aportado por un usuario: tornero
verifica el acabado de un eje acercando la mano al torno sin detener el giro;
el guante se engancha en la pieza y arrastra mano y antebrazo. Caso gemelo de
[[BINVAC_026]] (torno en taller de mecanizado, intervención manual con pieza en
rotación); factor guante relacionado con [[BINVAC_055]] y [[BINVAC_039]].
Archivado en
`wiki/investigaciones/atrapamiento-guante-torno-convencional-mecanizado.md`.
Creadas causa [[causas/uso-de-guantes-ante-piezas-en-rotacion]], medidas
[[medidas-preventivas/parada-obligatoria-para-inspeccion-en-tornos]] y
[[medidas-preventivas/prohibicion-de-guantes-ante-maquinas-rotativas]], entidad
[[agentes-materiales/tornos-convencionales]] y patrón
[[patrones/atrapamiento-contacto-con-pieza-en-rotacion]].
