# Arquitectura de Carpetas - Proyecto Reasis

## Objetivo
Organizar el proyecto en módulos por dominio para:
- Mantener el directorio raíz limpio con outputs principales (BD, documentación)
- Agrupar funciones por dominio lógico
- Facilitar mantenimiento y escalabilidad
- Separar código fuente de datos y documentación

## Estructura Propuesta

```
Reasis/
│
├── 📄 README.md                    # Documentación principal
├── 📄 CLAUDE.md                    # Memoria de trabajo Claude
├── 📄 AGENTS.md                    # Historial de trabajo detallado  
├── 📄 MATRIZ_OPERACIONALIZACION.md # Variables del estudio
├── 📄 requirements.txt             # Dependencias Python
├── 🗄️ reasis_database.db           # BASE DE DATOS PRINCIPAL (OUTPUT)
├── 🗄️ reasis_database_backup_*.db  # Backups de BD
│
├── 📁 src/                         # CÓDIGO FUENTE ORGANIZADO POR DOMINIOS
│   │
│   ├── 📁 instituciones/           # Dominio: Instituciones Educativas
│   │   ├── revisor_instituciones.py
│   │   ├── migrador_v2_mejorado.py
│   │   ├── analizador_v2_mejorada.py
│   │   ├── exportador_instituciones.py
│   │   ├── corrector_ruralidad_auto.py
│   │   └── __init__.py
│   │
│   ├── 📁 academicos/              # Dominio: Resultados Académicos
│   │   ├── explorador_datos_academicos.py
│   │   ├── migrador_datos_academicos.py
│   │   ├── analizador_datos_academicos.py
│   │   ├── normalizador_codigos_ie.py
│   │   ├── resumen_estructura_academica.py
│   │   └── __init__.py
│   │
│   ├── 📁 consolidacion/           # Dominio: Consolidación de Datos
│   │   ├── consolidador_final_v2.py
│   │   ├── explorador_datos.py
│   │   ├── explorador_estructura.py
│   │   ├── explorador_datos_globales_detallado.py
│   │   └── __init__.py
│   │
│   ├── 📁 indices/                 # Dominio: Cálculo de Índices (ILA, TD, PR)
│   │   ├── calculador_ila.py       # A crear
│   │   ├── calculador_tendencias.py # A crear
│   │   ├── calculador_resiliencia.py # A crear
│   │   ├── mapeo_variables_simple.py
│   │   └── __init__.py
│   │
│   ├── 📁 calidad/                 # Dominio: Control de Calidad
│   │   ├── verificador_datos.py
│   │   ├── auditoria_calidad_datos.py
│   │   ├── limpiador_datos.py
│   │   └── __init__.py
│   │
│   ├── 📁 competencias_digitales/  # Dominio: Competencias Digitales Docentes
│   │   ├── analizador_competencias.py # A crear desde datos existentes
│   │   └── __init__.py
│   │
│   └── 📁 utils/                   # Utilidades Comunes
│       ├── database_connection.py  # A crear
│       ├── config.py              # A crear
│       ├── helpers.py             # A crear
│       └── __init__.py
│
├── 📁 data/                        # DATOS PROCESADOS Y TEMPORALES
│   ├── exports/                    # Exportaciones CSV/Excel
│   │   └── instituciones_educativas_*.csv
│   ├── temp/                       # Archivos temporales
│   └── reports/                    # Reportes generados
│
├── 📁 assets/                      # FUENTES DE DATOS ORIGINALES (SIN CAMBIOS)
│   └── Consultoria/                # Mantener estructura actual
│
├── 📁 docs/                        # DOCUMENTACIÓN ADICIONAL
│   ├── metodologia.md              # Metodología del estudio
│   ├── diccionario_datos.md        # Diccionario de datos
│   └── manual_usuario.md           # Manual de uso
│
├── 📁 scripts/                     # SCRIPTS DE ADMINISTRACIÓN
│   ├── setup_database.py          # Configuración inicial BD
│   ├── backup_database.py         # Script de backup
│   └── migrate_structure.py       # Script para esta migración
│
└── 📁 tests/                       # PRUEBAS (FUTURO)
    ├── test_instituciones.py
    ├── test_academicos.py
    └── test_indices.py
```

## Ventajas de esta Estructura

### ✅ **Directorio Raíz Limpio**
- Solo outputs principales: BD, documentación, configuración
- Fácil identificación de productos del proyecto

### ✅ **Módulos por Dominio**
- **instituciones/**: Todo relacionado con IIEE
- **academicos/**: Procesamiento de notas estudiantiles  
- **indices/**: Cálculo de ILA, TD, PR, etc.
- **consolidacion/**: Migración desde Excel
- **calidad/**: Validación y limpieza

### ✅ **Escalabilidad**
- Fácil agregar nuevos dominios
- Separación clara de responsabilidades
- Reutilización de código entre módulos

### ✅ **Mantenimiento**
- Código organizado y fácil de encontrar
- Imports claros entre módulos
- Tests organizados por dominio

## Plan de Migración

1. **Crear estructura de carpetas**
2. **Mover archivos existentes** a sus módulos correspondientes
3. **Actualizar imports** en todos los scripts
4. **Crear archivos de configuración** común
5. **Documentar cambios** en AGENTS.md

## Archivos a Mover

### 📁 src/instituciones/
- `revisor_instituciones.py`
- `migrador_v2_mejorado.py` 
- `analizador_v2_mejorada.py`
- `exportador_instituciones.py`
- `corrector_ruralidad_auto.py`

### 📁 src/academicos/
- `explorador_datos_academicos.py`
- `migrador_datos_academicos.py`
- `analizador_datos_academicos.py`
- `normalizador_codigos_ie.py`
- `resumen_estructura_academica.py`

### 📁 src/consolidacion/
- `consolidador_final_v2.py`
- `explorador_datos.py`
- `explorador_estructura.py`
- `explorador_datos_globales_detallado.py`

### 📁 src/calidad/
- `verificador_datos.py`
- `auditoria_calidad_datos.py`
- `limpiador_datos.py`

### 📁 data/exports/
- `data consolidada/` → `data/exports/`

## ✅ ESTRUCTURA IMPLEMENTADA (2025-08-07)

### 📁 Estructura Final Creada
```
Reasis/
├── 📄 README.md                    # Documentación principal  
├── 📄 CLAUDE.md                    # Memoria de trabajo Claude
├── 📄 AGENTS.md                    # Historial detallado
├── 📄 ARQUITECTURA_CARPETAS.md     # Este archivo
├── 📄 MATRIZ_OPERACIONALIZACION.md # Variables del estudio
├── 📄 requirements.txt             # Dependencias Python
├── 🗄️ reasis_database.db           # BASE DE DATOS PRINCIPAL
├── 🗄️ reasis_database_backup_*.db  # Backups automáticos
│
├── 📁 src/                         # CÓDIGO FUENTE MODULAR
│   ├── 📁 instituciones/           # 6 archivos - Gestión IIEE
│   ├── 📁 academicos/             # 6 archivos - Resultados estudiantes  
│   ├── 📁 consolidacion/          # 11 archivos - Migración Excel→SQLite
│   ├── 📁 indices/                # 2 archivos - Cálculo ILA, TD, PR
│   ├── 📁 calidad/                # 3 archivos - Validación datos
│   ├── 📁 competencias_digitales/ # Futuro - Análisis docentes
│   └── 📁 utils/                  # 4 archivos - Utilidades comunes
│
├── 📁 data/                       # DATOS PROCESADOS
│   ├── exports/                   # 3 archivos CSV instituciones
│   ├── temp/                      # Archivos temporales
│   └── reports/                   # Reportes futuros
│
├── 📁 assets/                     # DATOS ORIGINALES (intacto)
├── 📁 docs/                       # Documentación adicional
├── 📁 scripts/                    # Scripts administración
└── 📁 tests/                      # Pruebas futuras
```

### 📊 Archivos Migrados por Módulo

#### 🏢 **src/instituciones/** (6 archivos)
- `revisor_instituciones.py` - Análisis calidad datos IIEE
- `migrador_v2_mejorado.py` - Migración estructura V2.0
- `analizador_v2_mejorada.py` - Análisis versión mejorada
- `exportador_instituciones.py` - Export datos institucionales
- `corrector_ruralidad_auto.py` - Corrección clasificación rural/urbano
- `analizador_v2_instituciones.py` - Análisis versión V2

#### 🎓 **src/academicos/** (6 archivos)  
- `explorador_datos_academicos.py` - Exploración archivos Excel notas
- `migrador_datos_academicos.py` - Migración notas estudiantes
- `analizador_datos_academicos.py` - Análisis calidad datos académicos
- `normalizador_codigos_ie.py` - Normalización códigos instituciones
- `resumen_estructura_academica.py` - Resumen estructura académica
- `normalizador_columnas_academicas.py` - Normalización columnas

#### 📥 **src/consolidacion/** (11 archivos)
- `consolidador_final_v2.py` - Consolidador principal
- `explorador_datos.py` - Exploración inicial archivos
- `explorador_estructura.py` - Análisis estructuras Excel
- `explorador_datos_globales_detallado.py` - Exploración detallada
- `consolidador_*.py` - Múltiples versiones consolidadores
- `migrador_final_normalizado.py` - Migración normalizada

#### 📊 **src/indices/** (2 archivos)
- `mapeo_variables_simple.py` - Mapeo variables metodología
- `analisis_variables_metodologia.py` - Análisis viabilidad variables

#### ✅ **src/calidad/** (3 archivos)
- `verificador_datos.py` - Verificación general datos
- `auditoria_calidad_datos.py` - Auditoría completa calidad
- `limpiador_datos.py` - Limpieza datos

#### 🔧 **src/utils/** (4 archivos)
- `analizador_fuente_primaria.py` - Análisis fuentes primarias
- `arbol_base_datos.py` - Visualización estructura BD
- `muestra_datos.py` - Herramienta muestreo
- `muestra_estadistica.py` - Estadísticas muestreo

### 📁 **data/exports/** (3 archivos CSV)
- `instituciones_educativas_resumido.csv`
- `instituciones_educativas_v2_completa.csv` 
- `instituciones_unicas_consolidadas.csv`

## 🎯 Beneficios Logrados

### ✅ **Directorio Raíz Limpio**
- Solo archivos principales: BD, documentación, configuración
- Fácil identificación de outputs del proyecto
- Estructura profesional y organizada

### ✅ **Modularización Completa**
- **28 archivos Python** organizados en 6 módulos
- Separación clara de responsabilidades por dominio
- Código reutilizable y mantenible

### ✅ **Escalabilidad**
- Estructura preparada para crecimiento
- Fácil agregar nuevos módulos
- Separación datos originales vs procesados

## 📝 Próximos Pasos Post-Migración

1. **Actualizar imports** en scripts que referencian otros módulos
2. **Crear archivos de configuración** común (database_connection.py)
3. **Documentar APIs** de cada módulo
4. **Implementar scripts de administración** en /scripts/
5. **Resolver problema crítico** vinculación datos académicos↔instituciones