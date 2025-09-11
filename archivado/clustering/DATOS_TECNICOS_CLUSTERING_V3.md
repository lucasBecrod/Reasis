# DATOS TÉCNICOS - CLUSTERING V3
## Análisis Detallado de Centroides y Métricas

**Fecha:** 12 de agosto, 2025  
**Base de datos:** reasis_database_v3.db  
**Instituciones analizadas:** 184  
**Variables metodológicas:** 10 principales + 6 adicionales  

---

## 📊 CENTROIDES COMPLETOS POR CLUSTER

### **Variables Metodológicas Principales (Z-Scores)**

| Cluster | Y1_ILA | Y2_TD | Y3_PR | X1_NVC | X2_TR | X4_IDD | X6_CDD | X10_IE | X11_RED | X12_TOE |
|---------|--------|-------|-------|--------|-------|--------|--------|--------|---------|---------|
| **0** | 0.164 | 0.137 | -0.312 | 0.083 | 0.359 | 0.400 | **0.699** | -0.139 | -0.323 | **-0.897** |
| **1** | -0.074 | **-0.964** | **0.551** | **-1.059** | 0.009 | 0.026 | **-0.726** | -0.265 | -0.302 | 0.243 |
| **2** | 0.260 | **0.654** | -0.049 | 0.493 | 0.159 | **0.581** | **0.993** | 0.209 | -0.029 | 0.074 |
| **3** | -0.378 | -0.081 | -0.238 | 0.083 | 0.193 | 0.355 | 0.233 | 0.048 | 0.035 | 0.116 |
| **4** | -0.205 | -0.135 | -0.168 | 0.083 | 0.297 | **-0.572** | **-0.915** | -0.356 | -0.282 | -0.369 |
| **5** | 0.294 | 0.129 | -0.217 | 0.083 | **-2.786** | **-1.520** | 0.278 | **1.293** | **2.518** | 0.619 |

**Nota:** Valores en negrita indican z-scores > |0.5| (características distintivas)

---

### **Variables Adicionales (Z-Scores)**

| Cluster | X13_TMATRC | X14_NIVEL_EDU | X16_MODALIDAD | X17_GESTION | X24_GPMD | X25_POBLACION |
|---------|------------|---------------|---------------|-------------|----------|---------------|
| **0** | -0.103 | **-1.906** | **-6.708** | -0.775 | -0.888 | -0.240 |
| **1** | -0.172 | 0.131 | 0.149 | -0.775 | 0.281 | -0.756 |
| **2** | -0.262 | -0.120 | 0.149 | **1.061** | -0.777 | -0.230 |
| **3** | 0.143 | -0.072 | 0.149 | -0.231 | -0.304 | -0.204 |
| **4** | 0.102 | -0.198 | 0.149 | -0.734 | **0.868** | **0.793** |
| **5** | **1.380** | **1.988** | 0.149 | 0.540 | 0.356 | 0.557 |

---

## 🎯 INTERPRETACIÓN DE VARIABLES

### **Variables Metodológicas Principales:**

- **Y1_ILA (Índice Logro Académico):** Rendimiento académico compuesto
- **Y2_TD (Tendencia Desempeño):** Evolución temporal del rendimiento
- **Y3_PR (Progreso Relativo):** Rendimiento ajustado por contexto
- **X1_NVC (Vulnerabilidad Contextual):** Factores socioeconómicos adversos
- **X2_TR (Tipo Ruralidad):** Grado de ruralidad del contexto
- **X4_IDD (Desempeño Docente):** Evaluación competencias docentes
- **X6_CDD (Competencia Digital Docente):** Habilidades tecnológicas docentes
- **X10_IE (Infraestructura Educativa):** Condiciones físicas y servicios
- **X11_RED (Ratio Estudiante-Docente):** Densidad estudiantil por docente
- **X12_TOE (Tipo Organización Escolar):** Modalidad organizacional

### **Variables Adicionales:**

- **X13_TMATRC:** Total matrícula
- **X14_NIVEL_EDUCATIVO:** Nivel educativo predominante
- **X16_MODALIDAD:** Modalidad educativa
- **X17_GESTION:** Tipo de gestión
- **X24_GPMD:** Grado promedio
- **X25_POBLACION:** Población del distrito

---

## 📈 RANKING DE PODER DISCRIMINANTE

### **Variables Ordenadas por Desviación Estándar Entre Centroides:**

1. **X2_TR (Tipo Ruralidad):** 1.226 → Factor más discriminante
2. **X11_RED (Ratio Estudiante-Docente):** 1.112 → Densidad institucional
3. **X4_IDD (Desempeño Docente):** 0.797 → Calidad docente
4. **X6_CDD (Competencia Digital):** 0.764 → Capacidad tecnológica
5. **X10_IE (Infraestructura):** 0.605 → Condiciones físicas
6. **Y2_TD (Tendencia Desempeño):** 0.530 → Evolución académica
7. **X12_TOE (Organización Escolar):** 0.528 → Modalidad organizacional
8. **X1_NVC (Vulnerabilidad Contextual):** 0.526 → Contexto socioeconómico
9. **Y3_PR (Progreso Relativo):** 0.317 → Rendimiento contextualizado
10. **Y1_ILA (Logro Académico):** 0.272 → Rendimiento absoluto

---

## 🏫 DISTRIBUCIÓN TERRITORIAL DETALLADA

### **Matriz Cluster × Red:**

```
                Red 44  Red 47  Red 48  Red 54  Red 72  Red 79  TOTAL
Cluster 0           0       1       2       1       0       0      4
Cluster 1           0       2       0       4      10      20     36
Cluster 2          25       1      31       6       0       0     63
Cluster 3           3       6       2       7       1       0     19
Cluster 4           0      37       0       0      12       2     51
Cluster 5           1       2       5       0       1       2     11
TOTAL              29      49      40      18      24      24    184
```

### **Concentración por Red (% del cluster que representa cada red):**

| Red | Cluster Principal | % en ese Cluster | Segundo Cluster | % Segundo |
|-----|-------------------|------------------|-----------------|-----------|
| **44** | Cluster 2 | 86.2% | Cluster 3 | 10.3% |
| **47** | Cluster 4 | 75.5% | Cluster 3 | 12.2% |
| **48** | Cluster 2 | 77.5% | Cluster 5 | 12.5% |
| **54** | Cluster 3 | 38.9% | Cluster 1 | 22.2% |
| **72** | Cluster 4 | 50.0% | Cluster 1 | 41.7% |
| **79** | Cluster 1 | 83.3% | Cluster 5 | 8.3% |

---

## 🔍 ANÁLISIS DE COHESIÓN INTERNA

### **Dispersión Promedio Intra-Cluster (por variable):**

| Variable | Dispersión | Interpretación |
|----------|------------|----------------|
| **X1_NVC** | 0.503 | **Alta cohesión** - grupos homogéneos en vulnerabilidad |
| **X2_TR** | 0.490 | **Alta cohesión** - grupos homogéneos en ruralidad |
| **Y3_PR** | 0.600 | Cohesión media - progreso relativo consistente |
| **Y2_TD** | 0.716 | Cohesión media-baja - variabilidad en tendencias |
| **X10_IE** | 0.706 | Cohesión media-baja - infraestructura variable |
| **X6_CDD** | 0.712 | Cohesión media-baja - competencia digital variable |
| **X4_IDD** | 0.743 | Baja cohesión - desempeño docente heterogéneo |
| **X11_RED** | 0.767 | Baja cohesión - ratios variables |
| **Y1_ILA** | 0.906 | **Baja cohesión** - logros académicos muy variables |
| **X12_TOE** | 0.964 | **Baja cohesión** - organización escolar muy variable |

---

## 📊 EJEMPLOS REPRESENTATIVOS POR CLUSTER

### **Cluster 0 (Especializadas):**
- **3916573** - VIRGEN DE LAS MERCEDES (Red 48)
- **838455** - HUARAC HUARAN (Red 54)
- **3891735** - MARIA AUXILIADORA (Red 48)

### **Cluster 1 (Resilientes Rurales):**
- **1315084** - 86548 JOSE MARIA VELAZ (Red 54)
- **1633189** - 86769 ABRAHAM VALDELOMAR (Red 54)
- **520221** - 86809 (Red 54)

### **Cluster 2 (Alto Rendimiento):**
- **415059** - 86731 (Red 54)
- **415141** - 86783 (Red 54)
- **818682** - 87009-01 (Red 54)

### **Cluster 3 (Equilibradas):**
- **414987** - 86548 JOSE MARIA VELAZ (Red 54)
- **1376268** - 86548 JOSE MARIA VELAZ (Red 54)
- **415117** - 86769 ABRAHAM VALDELOMAR (Red 54)

### **Cluster 4 (En Desarrollo):**
- **1306182** - 852 (Red 47)
- **687194** - 36465 MICAELA BASTIDAS PUYUCAHUA (Red 79)
- **1320001** - 601614 (Red 47)

### **Cluster 5 (Urbanas Complejas):**
- **350447** - 14144 SANTA ROSA (Red 48)
- **1785484** - FE Y ALEGRIA 48 (Red 48)
- **1785476** - FE Y ALEGRIA 48 (Red 48)

---

## ⚡ MÉTRICAS DE CALIDAD ESTADÍSTICA

- **Silhouette Score Global:** 0.1936
- **Número óptimo de clusters:** 6 (determinado por análisis previo)
- **Cobertura de la muestra:** 184/384 instituciones (47.9%)
- **Variables con datos completos:** 16 de 16 analizadas
- **Balanceamiento de clusters:** Razonable (min: 2.2%, max: 34.2%)

---

**Metodología:** Clustering K-Means con estandarización z-score  
**Software:** Python, pandas, scikit-learn, sqlite3  
**Validación:** Silhouette analysis, distribución territorial, coherencia temática