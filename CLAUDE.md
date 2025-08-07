# CLAUDE.md - Memoria de Trabajo del Proyecto Reasis

## Contexto del Proyecto
**Proyecto**: Reasis - Plataforma de recolección y análisis de datos para Fe y Alegría
**Objetivo INICIAL**: Consolidar datos desestructurados de Excel/PDF/Word en base de datos SQLite para completar informe de tipologías de IIEE
**Objetivo FUTURO**: Crear aplicación FlutterFlow para recolección de datos

## ACTUALIZACIÓN IMPORTANTE (2025-08-07)
**ESTAMOS EN FASE INICIAL**: Solo consolidación de datos Excel → SQLite
**NO estamos construyendo la app aún** - eso es objetivo futuro
**OBJETIVO INMEDIATO**: Terminar informe "01 Informe Tipologías de IIIEE 2025.pdf"

## Estado Actual REAL

### 🚧 FASE 1 - EN PROGRESO: Consolidación de Datos
- ✅ **COMPLETADO**: Tabla instituciones_educativas_v2_mejorada (381 IIEE)
- 🔄 **EN REVISIÓN**: Tabla indicadores_academicos_base (requiere mejoras)
- 🔄 **EN REVISIÓN**: Tabla datos_competencia_digital (requiere mejoras)
- ❓ **NUEVA**: Tabla redes educativas rurales (RER) - necesita verificación

### 📊 Base de Datos Actual
- **Archivo**: `reasis_database.db` (SQLite)
- **Total registros**: 54,327 consolidados
- **Tablas principales**:
  - `instituciones_educativas_v2_mejorada`: 381 IIEE (100% consistente)
  - `resultados_academicos`: 15,054 registros académicos
  - `datos_competencia_digital`: 39,086 registros docentes

### 🎯 Variables para Metodología de Clustering
**Disponibles (7/12)**: ILA components, TD, PR, TR, IDD, CDD, RED
**Parciales (2/12)**: NVC (falta NBI), ED (falta estabilidad)
**Faltantes (3/12)**: IE, TOE, MEIB

### 🎉 HITO CRÍTICO ALCANZADO (2025-08-07)
**PROBLEMA CRÍTICO RESUELTO**: Vinculación exitosa datos académicos ↔ instituciones educativas

#### ✅ Logros Completados:
1. **ILA (Índice de Logro Académico)**: 49 instituciones con cálculo funcional
2. **Base de datos consolidada**: 57.1% vinculación exitosa (3,249/5,688 registros)
3. **Arquitectura modular**: Proyecto reorganizado profesionalmente
4. **Tabla de equivalencias**: Códigos Fe y Alegría ↔ Códigos MINEDU funcional

#### 🔧 Próximos Pasos Desbloqueados:
1. **Mejorar vinculación**: Del 57.1% al 80%+ usando búsqueda fuzzy
2. **Implementar TD**: Tendencia de Desempeño con datos multi-año 2022-2024  
3. **Implementar PR**: Perfil de Resiliencia usando modelo estadístico
4. **Completar informe tipologías**: Ahora completamente viable

## Stack Tecnológico
- **Análisis**: Python, Pandas, SQLite
- **Objetivo final**: FlutterFlow + Supabase (PostgreSQL)

## Comandos Importantes
```bash
# Análisis de datos
python analizador_datos_academicos.py
python normalizador_codigos_ie.py

# Verificación de calidad
python revisor_instituciones.py
python verificador_datos.py
```

## Archivos Clave
- `reasis_database.db`: Base de datos principal
- `AGENTS.md`: Documentación detallada del trabajo realizado
- `assets/Consultoria/`: Fuentes de datos originales
- `supabase/migrations/`: Esquemas para producción

## Metodología de Trabajo Actual
1. **Explorar archivos Excel**: Ver campos y obtener 10-15 filas de muestra
2. **Comprender contenido**: Analizar estructura y datos
3. **Procesar a SQLite**: Migrar datos estructurados a base de datos
4. **Objetivo**: Preparar datos para completar informe tipologías

## Archivos Fuente
- **Ruta datos**: `C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\`
- **Informe objetivo**: `01 Informe en elaboración\01 Informe Tipologías de IIIEE 2025.pdf`
- **Matriz operacionalización**: Ver MATRIZ_OPERACIONALIZACION.md

## Última Sesión de Trabajo
CORRECCIÓN: La Fase 1 AÚN NO está completa. Necesitamos revisar y mejorar las tablas existentes antes de continuar con las siguientes fases.