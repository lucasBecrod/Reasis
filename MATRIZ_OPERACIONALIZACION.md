# MATRIZ DE OPERACIONALIZACIÓN ESTUDIO EXPLORATORIO

**Para:** Gloria Tuse  
**De:** Lucas Becrod, Alex Aburto y Josue Ramos  
**Fecha:** 14 Julio 2025  
**Asunto:** Viabilidad de estudio con variables disponibles para caracterización de IIEE

## OBJETIVO DEL ESTUDIO
Clasificar las IIEE de Fe y Alegría en grupos homogéneos basados en desempeño estudiantil, docente y factores contextuales, para diseñar intervenciones pedagógicas diferenciadas y priorizadas.

## MATRIZ DE OPERACIONALIZACIÓN DE VARIABLES
**Estudio Piloto de Caracterización de IIEE - Fe y Alegría del Perú**

### VARIABLES DEPENDIENTES

| Variable | Definición | Indicador | Fuente | Responsable |
|----------|------------|-----------|--------|-------------|
| **Y1: Índice de Logro Académico (ILA)** | Nivel de desempeño académico alcanzado por los estudiantes de la IIEE en las áreas fundamentales de aprendizaje | ILA = (Promedio_Notas_Matemática + Promedio_Notas_Comunicación) / 2. Escala 0-20, donde valores ≥14 indican logro satisfactorio | RER - Datos de 3 años | Lucas |
| **Y2: Tendencia de Desempeño (TD)** | Dirección del cambio en el desempeño académico de la IIEE durante el período analizado | TD = (ILA_2024 - ILA_2022) / ILA_2022. Valores >0.05 indican mejora, <-0.05 deterioro, intermedio estancamiento | RER - Cálculo derivado | Lucas |
| **Y3: Perfil de Resiliencia (PR)** | Capacidad de la IIEE para obtener resultados superiores a los esperados dado su contexto socioeconómico | PR = Residuo estandarizado del modelo ILA ~ Contexto. Valores >1 indican alta resiliencia, <-1 vulnerabilidad | Cálculo estadístico | Lucas |

### VARIABLES INDEPENDIENTES - CONTEXTO

| Variable | Definición | Indicador | Fuente | Responsable |
|----------|------------|-----------|--------|-------------|
| **X1: Nivel de Vulnerabilidad Contextual (NVC)** | Grado de desventaja socioeconómica y geográfica del entorno donde opera la IIEE | NVC = (NBI_distrito × 0.4) + (Ruralidad × 0.3) + (1-Servicios_básicos × 0.3). Escala 0-1 | INEI, ESCALE, Censo Infraestructura | Lucas |
| **X2: Tipo de Ruralidad (TR)** | Clasificación del grado de dispersión poblacional y acceso a servicios del centro poblado | Variable categórica ordinal: 1=Urbano, 2=Rural accesible, 3=Rural disperso | ESCALE | Gloria |
| **X3: Accesibilidad Educativa (AE)** | Facilidad de acceso físico de los estudiantes a la IIEE | AE = (Tiempo_traslado_máximo + Tiempo_traslado_mínimo) / 2. Medido en minutos | Red rural | **No se trabajará** |

### VARIABLES INDEPENDIENTES - DOCENTE

| Variable | Definición | Indicador | Fuente | Responsable |
|----------|------------|-----------|--------|-------------|
| **X4: Índice de Desempeño Docente (IDD)** | Nivel de competencia pedagógica y profesional del equipo docente de la IIEE | IDD = Promedio_PAAD_IIEE. Escala 1-4, donde ≥3 indica desempeño satisfactorio | Listado de formación | Gloria |
| **X5: Estabilidad Docente (ED)** | Continuidad del personal docente en la IIEE | ED = (Docentes_nombrados / Total_docentes) × 0.5 + (Promedio_años_servicio_red / 10) × 0.5. Escala 0-1 | Info de la red, Censo educativo | Gloria |
| **X6: Competencia Digital Docente (CDD)** | Nivel de uso efectivo de recursos tecnológicos para la enseñanza | CDD = Promedio_puntaje_evaluación_competencias_digitales. Escala 1-4 | Eval. competencias digitales PAAD 2024 | Gloria, con información de Escuela Digital |

### VARIABLES INDEPENDIENTES - RECURSOS

| Variable | Definición | Indicador | Fuente | Responsable |
|----------|------------|-----------|--------|-------------|
| **X10: Infraestructura Educativa (IE)** | Calidad y disponibilidad de espacios y equipamiento para el aprendizaje | IE = (Servicios_básicos × 0.4) + (Estado_mobiliario × 0.3) + (Tiene_biblioteca × 0.3). Escala 0-1 | Censo infraestructura educativa | Gloria |
| **X11: Ratio Estudiante-Docente (RED)** | Carga de trabajo docente medida por número de estudiantes atendidos | RED = Total_estudiantes / Total_docentes. Variable continua | ESCALE | Lucas |
| **X12: Tipo de Organización Escolar (TOE)** | Modelo organizativo de la IIEE según distribución de docentes y grados | Variable categórica: 1=Polidocente completo, 2=Multigrado, 3=Unidocente | ESCALE, Censo | Gloria |

### VARIABLES INDEPENDIENTES - ESTUDIANTES/FAMILIAS

| Variable | Definición | Indicador | Fuente | Responsable |
|----------|------------|-----------|--------|-------------|
| **X13: Capital Cultural Familiar (CCF)** | Nivel educativo y prácticas educativas del entorno familiar | CCF = Promedio_nivel_educativo_tutores. Escala ordinal: 1=Sin estudios a 5=Superior completa | Ficha de matrícula | **No se trabajará** |
| **X14: Antecedentes Educativos (AE)** | Trayectoria educativa previa de los estudiantes | AE = Porcentaje_estudiantes_2do_con_inicial. Variable continua 0-100% | Ficha de matrícula | **No se trabajará** |
| **X15: Modalidad EIB (MEIB)** | Implementación de educación intercultural bilingüe | Variable categórica: 0=No EIB, 1=EIB de fortalecimiento, 2=EIB de revitalización | ESCALE | Gloria |

## RECURSOS EXTERNOS

- **Dirección Drive**: https://drive.google.com/drive/folders/1eYaZDWBrRW7Dwg2PoA_rh-dbnETxagiY?usp=drive_link
- **Información actualizada**: Carpeta "Información actualizada"
- **ESCALE MINEDU**: https://escale.minedu.gob.pe/

## NOTAS METODOLÓGICAS

1. **Variables Compuestas**: Varias variables (NVC, IDD, IE) son índices construidos a partir de múltiples indicadores para capturar dimensiones complejas.

2. **Estandarización**: Todas las variables continuas serán estandarizadas (z-score) antes del análisis de clustering para evitar sesgos por escala.

3. **Tratamiento de Datos Faltantes**: Se aplicará imputación por media/moda según tipo de variable, documentando el porcentaje de imputación.

4. **Validación**: El piloto incluirá análisis de consistencia interna (Alpha de Cronbach) para índices compuestos.

## ESTADO ACTUAL DE VARIABLES (2025-08-07)

- **Disponibles (7/12)**: ILA components, TD, PR, TR, IDD, CDD, RED
- **Parciales (2/12)**: NVC (falta NBI), ED (falta estabilidad)
- **Faltantes (3/12)**: IE, TOE, MEIB
- **No se trabajarán (3/12)**: X3, X13, X14