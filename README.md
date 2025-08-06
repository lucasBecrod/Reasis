# Reasis Project

## About this project

"Reasis" is a data collection and analysis platform for the "Fe y Alegría" network of schools. The project aims to provide a tool for school principals to upload data about their schools, which will then be used by the "Fe y Alegría" team for statistical analysis and to better plan their interventions.

This project is in its early stages of development.

## Technology Stack

*   **Frontend:** FlutterFlow
*   **Backend:** Supabase (PostgreSQL)

## Database Structure

The database is designed to separate raw data (base indicators) from calculated data (composite variables).

*   **Base Indicators:** These are the primary data points collected through the app's forms. They are stored in four main tables:
    *   `instituciones_educativas`: Basic information about the schools.
    *   `indicadores_academicos_base`: Academic performance indicators.
    *   `indicadores_docentes_base`: Teacher-related indicators.
    *   `indicadores_infraestructura_base`: Infrastructure and resource indicators.

*   **Composite Variables:** These are calculated automatically from the base indicators using SQL views. This ensures that the data is always consistent and up-to-date. The views are:
    *   `variables_dependientes`
    *   `variables_independientes_contexto`
    *   `variables_independientes_docentes`
    *   `variables_independientes_recursos`

The complete database schema can be found in the `supabase/migrations` directory.
