# AUDITORÍA METODOLÓGICA DE TABLAS - REASIS

## 📊 CLASIFICACIÓN DE TABLAS PARA ESTUDIO METODOLÓGICO

### 🟢 **TABLAS ESENCIALES (MANTENER)**

#### **TABLA MAESTRA**
- **`instituciones_educativas`**: 381 registros, 47 columnas
  - **Uso**: Tabla central con códigos modulares y datos básicos
  - **Variables**: Código modular, nombre, ubicación, nivel educativo

#### **DATOS ACADÉMICOS (VARIABLES Y1, Y2, Y3)**
- **`resultados_academicos`**: 15,054 registros, 20 columnas  
  - **Uso**: ILA, TD, PR - Variables dependientes centrales
  - **Variables**: Notas matemática/comunicación por estudiante, años 2022-2024

#### **DATOS DOCENTES (VARIABLES X4, X5, X6)**
- **`docentes_data`**: 421 registros, 22 columnas
  - **Uso**: X4 (IDD), X5 (ED) - Desempeño y estabilidad docente
  - **Variables**: Evaluaciones PADD, continuidad, nombramientos

- **`competencia_digital_docentes`**: 776 registros, 15 columnas
  - **Uso**: X6 (CDD) - Competencia digital docente
  - **Variables**: Puntuaciones competencias digitales por red

#### **DATOS CONTEXTUALES (VARIABLES X1, X2, X10, X15)**
- **`datos_eib_minedu`**: 84 registros, 11 columnas
  - **Uso**: X1 (NVC), X15 (MEIB), X10 (IE) - Variables contextuales críticas
  - **Variables**: Quintil pobreza, modalidad EIB, servicios básicos
  - **MEJORADO**: Aplicada técnica múltiples códigos identificadores (320% incremento)

- **`ruralidad_cesar`**: 67 registros, 8 columnas  
  - **Uso**: X2 (TR) - Tipo ruralidad específico
  - **Variables**: Rural 1/2/3 granular

- **`x5_ed_estabilidad_docente`**: 83 registros, 12 columnas
  - **Uso**: X5 (ED) - Estabilidad docente calculada
  - **Variables**: % nombrados vs contratados, estabilidad calculada

- **`variables_eib_mejoradas_final`**: 83 registros, 12 columnas
  - **Uso**: Variables EIB mejoradas con técnica múltiples códigos
  - **Variables**: X1_NVC, X15_MEIB, X10_IE mejoradas

#### **DATOS RECURSOS (VARIABLES X11, X12)**  
- **`datos_toe_servicios_2024`**: 167 registros, 14 columnas
  - **Uso**: X12 (TOE), X11 (RED) - Organización escolar y recursos
  - **Variables**: Tipo organización, estudiantes, docentes

#### **COMPETENCIAS DIGITALES ESTUDIANTES**
- **`competencia_digital_estudiantes`**: 1,380 registros, 28 columnas
  - **Uso**: Variable complementaria competencias estudiantes
  - **Variables**: Evaluaciones digitales por red

#### **CONECTIVIDAD Y EQUIPAMIENTO**
- **`conectividad_equipamiento`**: 121 registros, 68 columnas
  - **Uso**: Variables infraestructura TIC adicionales
  - **Variables**: Conectividad, equipamiento tecnológico

#### **AUXILIARES ESENCIALES**
- **`mapeo_codigos_ie`**: 205 registros, 5 columnas
  - **Uso**: Vinculación códigos locales → modulares
  - **Variables**: Tabla de equivalencias para integración

- **`redes_fe_y_alegria`**: 80 registros, 8 columnas
  - **Uso**: Información de redes y regiones
  - **Variables**: Códigos red, ubicaciones, contexto territorial

### 🟡 **TABLAS HISTORICAS/COMPLEMENTARIAS (EVALUAR)**

- **`datos_iiee_2023`**: 170 registros, 18 columnas
  - **Uso**: Datos históricos 2023, útil para validación temporal
  - **Decisión**: MANTENER para análisis de tendencias

### 🔴 **TABLAS A ELIMINAR (BACKUP/OBSOLETAS)**

#### **BACKUPS INNECESARIOS**
- **`instituciones_educativas_backup`**: 381 registros, 61 columnas
  - **Razón**: Backup de versión anterior, ya optimizada
  
- **`instituciones_educativas_backup_eib`**: 381 registros, 59 columnas  
  - **Razón**: Backup específico EIB, datos ya integrados

#### **TABLAS VACÍAS/REDUNDANTES**
- **`variables_eib_multiples_codigos`**: 0 registros
  - **Razón**: Tabla vacía, sin utilidad
  
- **`conectividad_progreso`**: 116 registros, 9 columnas
  - **Razón**: Tabla de control de proceso, no datos finales

#### **DATOS ANTIGUOS CONSOLIDADOS**
- **`indicadores_academicos_base`**: 1,300 registros, 7 columnas
  - **Razón**: Reemplazado por `resultados_academicos` (15,054 registros)
  
- **`datos_competencia_digital`**: 39,086 registros, 8 columnas
  - **Razón**: Datos en formato raw, consolidados en tablas específicas

## 🎯 **RESUMEN DE ACCIÓN**

### MANTENER (11 TABLAS ESENCIALES):
1. `instituciones_educativas` (maestra)
2. `resultados_academicos` (Y1,Y2,Y3)
3. `docentes_data` (X4,X5)  
4. `competencia_digital_docentes` (X6)
5. `datos_eib_minedu` (X1,X10,X15)
6. `ruralidad_cesar` (X2)
7. `x5_ed_estabilidad_docente` (X5)
8. `variables_eib_mejoradas_final` (EIB mejoradas)
9. `datos_toe_servicios_2024` (X11,X12)
10. `conectividad_equipamiento` (infraestructura TIC)
11. `competencia_digital_estudiantes` (complementaria)

### AUXILIARES (3 TABLAS):
12. `mapeo_codigos_ie` (vinculación)
13. `redes_fe_y_alegria` (contexto)  
14. `datos_iiee_2023` (históricos)

### ELIMINAR (7 TABLAS):
- `instituciones_educativas_backup`
- `instituciones_educativas_backup_eib` 
- `variables_eib_multiples_codigos`
- `conectividad_progreso`
- `indicadores_academicos_base`
- `datos_competencia_digital`
- `sqlite_sequence`

**TOTAL FINAL**: 14 tablas esenciales + auxiliares (vs 21 actuales)
**LIMPIEZA**: 33% reducción de tablas obsoletas/redundantes