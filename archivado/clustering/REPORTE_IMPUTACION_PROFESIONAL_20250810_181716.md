# REPORTE IMPUTACION PROFESIONAL - VARIABLES CONTEXTUALES

**Fecha**: 2025-08-10 18:17:16
**Proyecto**: Reasis - Optimización Variables Contextuales

## Metodología Aplicada
- **Técnica principal**: Random Forest (Clasificación/Regresión)
- **Validación**: Cross-validation 5-fold
- **Manejo predictores**: KNN Imputer para NULLs en features
- **Balance clases**: class_weight='balanced' para clasificación

## Variables Procesadas

### X17_GESTION
- **Método**: RandomForest
- **Casos entrenamiento**: 177
- **Casos imputados**: 7
- **Predictores más importantes**:
  - X24_GPMD: 0.236
  - NUMERO_FYA: 0.233
  - X25_POBLACION_DISTRITO: 0.195
  - Y1_ILA: 0.096
  - ALTITUD_MSNM: 0.078

### X19_ORGANIZACION_PEDAGOGICA
- **Método**: RandomForest
- **Casos entrenamiento**: 175
- **Casos imputados**: 9
- **Predictores más importantes**:
  - X14_NIVEL_EDUCATIVO: 0.360
  - X11_RED: 0.262
  - Y1_ILA: 0.095
  - ALTITUD_MSNM: 0.094
  - X25_POBLACION_DISTRITO: 0.073

### X20_DIRECTIVOS_TOTAL
- **Método**: RandomForest
- **Casos entrenamiento**: 177
- **Casos imputados**: 7
- **Predictores más importantes**:
  - Y1_ILA: 0.227
  - X14_NIVEL_EDUCATIVO: 0.190
  - X2_TR: 0.120
  - ALTITUD_MSNM: 0.102
  - X25_POBLACION_DISTRITO: 0.092

### X21_MULTIPLICIDAD1
- **Método**: RandomForest
- **Casos entrenamiento**: 175
- **Casos imputados**: 9
- **Predictores más importantes**:
  - X11_RED: 0.237
  - Y1_ILA: 0.172
  - ALTITUD_MSNM: 0.144
  - X14_NIVEL_EDUCATIVO: 0.135
  - X25_POBLACION_DISTRITO: 0.101

### X22_MULTIPLICIDAD2
- **Método**: RandomForest
- **Casos entrenamiento**: 175
- **Casos imputados**: 9
- **Predictores más importantes**:
  - X11_RED: 0.256
  - ALTITUD_MSNM: 0.146
  - X14_NIVEL_EDUCATIVO: 0.139
  - X18_TURNO: 0.122
  - Y1_ILA: 0.114

