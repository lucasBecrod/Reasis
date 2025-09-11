# Proyecto Reasis

## Acerca de este proyecto

"Reasis" es una plataforma de recolección y análisis de datos para la red de escuelas "Fe y Alegría". El proyecto tiene como objetivo proporcionar una herramienta para que los directores de escuela suban datos sobre sus instituciones, que luego serán utilizados por el equipo de "Fe y Alegría" para análisis estadístico y para planificar mejor sus intervenciones.

Este proyecto se encuentra en sus primeras etapas de desarrollo.

## Estructura actual del repositorio (2025-08-11)

- Código por dominios bajo `scripts/`:
  - `scripts/siagie/`: carga y procesamiento SIAGIE
  - `scripts/docentes/`: integración y análisis de docentes
  - `scripts/pobreza/`: vinculación/analítica de pobreza
  - `scripts/indices/`: cálculo de variables metodológicas (ILA, TD, X11, X13, Y3, etc.)
  - `scripts/calidad/`: limpieza/correcciones/imputaciones
  - `scripts/analisis/`: exploraciones, correlaciones, reportes
  - `scripts/instituciones/`: utilidades de instituciones
  - `scripts/misc/`: utilidades varias

- Datos y reportes:
  - `data/reports/`: salidas (CSV/figuras) de análisis y reportes
  - `assets/Consultoria/`: fuentes originales y reportes Word finales
  - `db/sql/`: scripts SQL reorganizados desde el raíz

- Documentación:
  - `docs/`: toda la documentación `.md` (metodologías, estados, reportes técnicos)
  - `ARQUITECTURA_CARPETAS.md`: guía de estructura y migraciones

## Stack Tecnológico

*   **Frontend:** FlutterFlow
*   **Backend:** Supabase (PostgreSQL)

## Estructura de la Base de Datos

La base de datos está diseñada para separar los datos crudos (indicadores base) de los datos calculados (variables compuestas).

*   **Indicadores Base:** Estos son los puntos de datos primarios recolectados a través de los formularios de la aplicación. Se almacenan en cuatro tablas principales:
    *   `instituciones_educativas`: Información básica sobre las escuelas.
    *   `indicadores_academicos_base`: Indicadores de rendimiento académico.
    *   `indicadores_docentes_base`: Indicadores relacionados con los docentes.
    *   `indicadores_infraestructura_base`: Indicadores de infraestructura y recursos.

*   **Variables Compuestas:** Estas se calculan automáticamente a partir de los indicadores base usando vistas SQL. Esto asegura que los datos siempre sean consistentes y estén actualizados. Las vistas son:
    *   `variables_dependientes`
    *   `variables_independientes_contexto`
    *   `variables_independientes_docentes`
    *   `variables_independientes_recursos`

El esquema completo de la base de datos se puede encontrar en el directorio `supabase/migrations`.
