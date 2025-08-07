# Archivos para Replicación - Metodología de Vinculación Masiva

## 📁 Archivos de Documentación

### 📋 Documentación Principal
- **`METODOLOGIA_VINCULACION_REPLICABLE.md`** - Guía completa paso a paso para replicar toda la metodología
- **`AGENTS.md`** - Documentación detallada del proceso histórico con todas las decisiones tomadas  
- **`CLAUDE.md`** - Memoria actualizada del proyecto con estado final
- **`ARCHIVOS_REPLICACION.md`** - Este archivo (índice de todos los recursos)

## 🛠️ Scripts de Implementación

### Scripts Principales (Orden de Ejecución)
1. **`temp_load_equivalencias.py`** - Carga tabla base de equivalencias desde Excel
2. **`temp_vincular.py`** - Aplicador de vinculación y generador de métricas
3. **`temp_buscar_criticos.py`** - Búsqueda de 15 códigos más críticos
4. **`temp_buscar_restantes.py`** - Búsqueda de 20 códigos restantes críticos  
5. **`temp_buscar_masivo.py`** - Búsqueda masiva automatizada de 50+ códigos
6. **`vinculacion_ultimo_recurso.py`** - ⭐ **METODOLOGÍA INNOVADORA CLAVE**

### Scripts de Apoyo Desarrollados
- **`temp_load_equivalencias.py`** - Procesamiento de archivo Excel de equivalencias
- Scripts temporales para diagnóstico y validación (pueden eliminarse después)

## 📊 Archivos de Datos

### Archivos Excel Fuente (Requeridos)
- **`assets/Consultoria/DatosLucas/Matematica y Comunicación/BD1- Matemática 2024.xlsx`**
- **`assets/Consultoria/DatosLucas/Matematica y Comunicación/BD2- Comunicación 2024.xlsx`**  
- **`assets/Consultoria/DatosLucas/Matematica y Comunicación/BD3 - Producción de textos 2024.xlsx`**
- **`assets/Consultoria/Información actualizada/1. Ruralidad, EIB y TOE.xlsx`**

### Base de Datos
- **`reasis_database.db`** - Base de datos SQLite final con todas las vinculaciones

## 🔧 Dependencias Técnicas

### Librerías Python Requeridas
```python
import pandas as pd
import sqlite3
import re
from pathlib import Path
```

### Estructura de Tablas Clave
```sql
-- Tabla principal de datos académicos
resultados_academicos (
    codigo_local,
    codigo_modular,  -- Campo vinculado
    nombre_ie_original,
    nivel_logro_numerico,
    materia,
    año,
    -- ... otros campos
)

-- Tabla de instituciones educativas  
instituciones_educativas (
    codigo_modular,
    codigo_local,
    nombre_institucion,
    -- ... otros campos
)

-- Tabla de equivalencias (generada por proceso)
mapeo_codigos_ie (
    codigo_local,
    codigo_modular,
    nombre_ie_encontrado,
    metodo_encontrado
)
```

## 📈 Métricas de Validación

### Métricas Clave para Seguimiento
```python
# Vinculación exitosa
porcentaje_vinculacion = (vinculados / total) * 100  # Objetivo: >95.8%

# Instituciones funcionales  
instituciones_ila = COUNT(DISTINCT codigo_modular WHERE codigo_modular IS NOT NULL)  # Objetivo: >63

# Registros sin vincular
sin_vincular = total - vinculados  # Objetivo: <5%
```

### Puntos de Control por Fase
- **Post tabla base**: ~38% vinculación
- **Post códigos críticos**: ~65% vinculación  
- **Post búsqueda masiva**: ~80% vinculación
- **Post último recurso**: ~97% vinculación ✅

## 🎯 Pasos de Replicación Rápida

### Para Replicar Completamente
1. **Verificar archivos**: Asegurar que existen todos los archivos Excel fuente
2. **Preparar base de datos**: SQLite con estructura de tablas correcta
3. **Ejecutar scripts en orden**: Seguir secuencia 1-6 documentada
4. **Validar métricas**: Verificar logro de objetivos en cada paso
5. **Documentar hallazgos**: Anotar diferencias o adaptaciones necesarias

### Para Adaptar a Otros Proyectos
1. **Analizar estructura**: Identificar campos equivalentes en tus datos
2. **Adaptar búsquedas**: Modificar criterios LIKE según tus códigos/nombres
3. **Ajustar métricas**: Definir objetivos apropiados para tu contexto
4. **Personalizar scripts**: Cambiar rutas, nombres de columnas, etc.
5. **Probar incrementalmente**: Validar cada fase antes de continuar

## 💡 Consejos para Uso Exitoso

### Antes de Empezar
- ✅ Crear backup de base de datos existente
- ✅ Verificar completitud de archivos fuente
- ✅ Definir métricas objetivo claras  
- ✅ Preparar entorno Python con librerías

### Durante la Ejecución  
- ✅ Ejecutar scripts uno por vez y validar
- ✅ Documentar problemas o adaptaciones
- ✅ Monitorear métricas en tiempo real
- ✅ Mantener logs de cambios importantes

### Después del Proceso
- ✅ Validar resultados contra objetivos
- ✅ Documentar lecciones aprendidas específicas
- ✅ Crear backup de resultado final
- ✅ Preparar documentación para equipo

## 🚨 Problemas Comunes y Soluciones

### Error: Archivos Excel no encontrados
**Solución**: Verificar rutas en scripts, ajustar `Path()` según estructura

### Error: Tablas SQLite no existen  
**Solución**: Ejecutar scripts de creación de estructura de BD primero

### Error: Baja vinculación (<50%)
**Solución**: Verificar calidad de tabla de equivalencias base, revisar técnicas de búsqueda

### Error: Encoding de caracteres
**Solución**: Remover emojis de prints, usar encoding UTF-8 consistente

## 📞 Información de Contacto

**Metodología desarrollada por**: Claude AI (Anthropic)  
**Fecha de validación**: 2025-08-07  
**Versión**: 1.0 (Metodología Final Validada)  

**Para replicación exitosa**: Seguir exactamente la secuencia documentada en `METODOLOGIA_VINCULACION_REPLICABLE.md`