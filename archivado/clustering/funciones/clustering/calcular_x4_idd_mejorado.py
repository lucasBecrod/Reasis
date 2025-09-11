"""
Script para calcular X4_IDD - Índice Desempeño Docente MEJORADO
Metodología robusta con limpieza de códigos + regresión para imputación

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import re

def limpiar_codigo_modular(codigo):
    """Limpia y normaliza códigos modulares"""
    if pd.isna(codigo):
        return None
    
    # Convertir a string y limpiar
    codigo_str = str(codigo).strip()
    
    # Remover espacios internos y caracteres no numéricos del inicio
    codigo_str = re.sub(r'^\s*[^\d]*', '', codigo_str)
    codigo_str = re.sub(r'\s+', '', codigo_str)
    
    # Intentar extraer número
    numeros = re.findall(r'\d+', codigo_str)
    if numeros:
        codigo_num = numeros[0]
        # Formatear con zfill(7)
        return codigo_num.zfill(7)
    
    return None

def calcular_x4_idd_mejorado():
    """
    Calcula X4_IDD con metodología mejorada:
    
    METODOLOGÍA INTEGRADA:
    1. LIMPIEZA DE CÓDIGOS: Normalización robusta de códigos modulares
    2. DATOS PADD: Promedio por institución con evaluaciones completas
    3. REGRESIÓN CONTEXTUAL: Modelo basado en competencia digital + características institucionales
    4. IMPUTACIÓN INTELIGENTE: Predicción por similaridad contextual
    """
    
    print("=== CALCULANDO X4_IDD MEJORADO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target con características contextuales
    df_target = pd.read_sql_query("""
        SELECT 
            CODIGO_MODULAR, 
            NOMBRE_INSTITUCION, 
            NUMERO_FYA,
            X2_TR,
            X1_NVC,
            LATITUD,
            LONGITUD
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. Procesar datos PADD con limpieza de códigos
    print(f"\n2. PROCESANDO DATOS PADD (con limpieza de códigos):")
    
    df_padd_raw = pd.read_sql_query("""
        SELECT 
            codigo_modular_actual,
            dni,
            nombre_completo,
            nota_matematica,
            nota_comunicacion, 
            nota_digital,
            nota_genero,
            rer
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL
          AND nota_matematica IS NOT NULL 
          AND nota_comunicacion IS NOT NULL
          AND nota_digital IS NOT NULL
          AND nota_genero IS NOT NULL
    """, conn)
    
    print(f"   Docentes PADD brutos: {len(df_padd_raw)}")
    
    # Limpiar códigos
    df_padd_raw['codigo_ie_limpio'] = df_padd_raw['codigo_modular_actual'].apply(limpiar_codigo_modular)
    df_padd_clean = df_padd_raw[df_padd_raw['codigo_ie_limpio'].notna()].copy()
    
    print(f"   Docentes PADD después limpieza: {len(df_padd_clean)}")
    
    # Calcular IDD individual
    df_padd_clean['IDD_individual'] = (
        df_padd_clean['nota_matematica'].astype(float) +
        df_padd_clean['nota_comunicacion'].astype(float) + 
        df_padd_clean['nota_digital'].astype(float) +
        df_padd_clean['nota_genero'].astype(float)
    ) / 4
    
    # Agregar por institución
    idd_padd_ie = df_padd_clean.groupby('codigo_ie_limpio').agg({
        'IDD_individual': ['mean', 'count'],
        'rer': 'first'
    }).reset_index()
    
    idd_padd_ie.columns = ['codigo_target', 'X4_IDD', 'num_docentes', 'red']
    idd_padd_ie['fuente'] = 'PADD'
    idd_padd_ie['metodo'] = 'promedio_docentes_evaluados'
    
    print(f"   Instituciones únicas con IDD PADD: {len(idd_padd_ie)}")
    print(f"   Rango IDD: {idd_padd_ie['X4_IDD'].min():.1f} - {idd_padd_ie['X4_IDD'].max():.1f}")
    
    # Verificar compatibilidad con target
    codigos_target_set = set(df_target['CODIGO_MODULAR'])
    idd_padd_compatible = idd_padd_ie[idd_padd_ie['codigo_target'].isin(codigos_target_set)]
    print(f"   Instituciones PADD compatibles con target: {len(idd_padd_compatible)}")
    
    # 3. Procesar competencia digital para modelo de regresión
    print(f"\n3. PROCESANDO COMPETENCIA DIGITAL (para regresión):")
    
    df_digital = pd.read_sql_query("""
        SELECT 
            nombre_rer,
            codigo_red,
            puntuacion_texto,
            nota_global_relativa_num,
            ambito,
            edad,
            sexo
        FROM competencia_digital_docentes
        WHERE puntuacion_texto IS NOT NULL
    """, conn)
    
    print(f"   Evaluaciones digitales: {len(df_digital)}")
    
    # Preparar datos para regresión: usar competencia digital para predecir desempeño
    # Normalizar puntuación digital a escala PADD (0-20)
    puntuacion_min = df_digital['puntuacion_texto'].min()
    puntuacion_max = df_digital['puntuacion_texto'].max()
    df_digital['IDD_digital_normalizado'] = (
        (df_digital['puntuacion_texto'] - puntuacion_min) / 
        (puntuacion_max - puntuacion_min)
    ) * 20
    
    # Agrupar por red para características contextuales
    digital_por_red = df_digital.groupby('codigo_red').agg({
        'IDD_digital_normalizado': ['mean', 'std', 'count'],
        'edad': 'mean',
        'nota_global_relativa_num': 'mean'
    }).reset_index()
    
    digital_por_red.columns = [
        'red_digital', 'idd_digital_mean', 'idd_digital_std', 'num_evaluaciones',
        'edad_promedio', 'nivel_competencia_promedio'
    ]
    
    print(f"   Redes con datos digitales: {len(digital_por_red)}")
    
    # 4. Crear modelo de regresión para imputación
    print(f"\n4. MODELO DE REGRESION PARA IMPUTACION:")
    
    # Combinar datos PADD compatibles con características institucionales
    df_training = df_target.merge(idd_padd_compatible, 
                                  left_on='CODIGO_MODULAR', 
                                  right_on='codigo_target', 
                                  how='inner')
    
    print(f"   Instituciones para entrenamiento: {len(df_training)}")
    
    if len(df_training) >= 10:  # Mínimo para regresión confiable
        # Preparar features para regresión
        features = []
        target_values = []
        
        for _, row in df_training.iterrows():
            # Features: ruralidad, vulnerabilidad, ubicación
            feature_vector = [
                row['X2_TR'] if pd.notna(row['X2_TR']) else 1.5,  # Ruralidad
                row['X1_NVC'] if pd.notna(row['X1_NVC']) else 3.5,  # Vulnerabilidad
                row['LATITUD'] if pd.notna(row['LATITUD']) else -12.0,  # Coordenadas
                row['LONGITUD'] if pd.notna(row['LONGITUD']) else -75.0,
                float(row['NUMERO_FYA']) if pd.notna(row['NUMERO_FYA']) else 50  # Red
            ]
            features.append(feature_vector)
            target_values.append(row['X4_IDD'])
        
        # Entrenar modelo
        X = np.array(features)
        y = np.array(target_values)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        r2_score = model.score(X_scaled, y)
        print(f"   R² del modelo: {r2_score:.3f}")
        print(f"   Coeficientes: Ruralidad={model.coef_[0]:.2f}, Vulnerabilidad={model.coef_[1]:.2f}")
        
        # Aplicar modelo a instituciones sin datos
        instituciones_sin_datos = df_target[~df_target['CODIGO_MODULAR'].isin(idd_padd_compatible['codigo_target'])]
        
        predicciones = []
        for _, row in instituciones_sin_datos.iterrows():
            feature_vector = [
                row['X2_TR'] if pd.notna(row['X2_TR']) else 1.5,
                row['X1_NVC'] if pd.notna(row['X1_NVC']) else 3.5,
                row['LATITUD'] if pd.notna(row['LATITUD']) else -12.0,
                row['LONGITUD'] if pd.notna(row['LONGITUD']) else -75.0,
                float(row['NUMERO_FYA']) if pd.notna(row['NUMERO_FYA']) else 50
            ]
            
            X_pred = scaler.transform([feature_vector])
            y_pred = model.predict(X_pred)[0]
            
            # Asegurar rango realista [0, 20]
            y_pred = max(0, min(20, y_pred))
            
            predicciones.append({
                'codigo_target': row['CODIGO_MODULAR'],
                'X4_IDD': y_pred,
                'fuente': 'Regresion_Contextual',
                'metodo': f'regresion_lineal_r2_{r2_score:.3f}'
            })
        
        df_predicciones = pd.DataFrame(predicciones)
        print(f"   Predicciones generadas: {len(df_predicciones)}")
        print(f"   Rango predicciones: {df_predicciones['X4_IDD'].min():.1f} - {df_predicciones['X4_IDD'].max():.1f}")
        
    else:
        print(f"   Datos insuficientes para regresión. Usando imputación simple.")
        # Fallback: imputación simple
        promedio_padd = idd_padd_compatible['X4_IDD'].mean()
        instituciones_sin_datos = df_target[~df_target['CODIGO_MODULAR'].isin(idd_padd_compatible['codigo_target'])]
        
        predicciones = []
        for _, row in instituciones_sin_datos.iterrows():
            predicciones.append({
                'codigo_target': row['CODIGO_MODULAR'],
                'X4_IDD': promedio_padd,
                'fuente': 'Imputacion_Simple',
                'metodo': 'promedio_padd_disponible'
            })
        
        df_predicciones = pd.DataFrame(predicciones)
    
    # 5. Consolidar resultados finales
    print(f"\n5. CONSOLIDACION FINAL:")
    
    # Prioridad: PADD real > Predicciones modelo
    resultados_finales = []
    
    # PADD compatible (prioridad 1)
    for _, row in idd_padd_compatible.iterrows():
        resultados_finales.append({
            'codigo_target': row['codigo_target'],
            'X4_IDD': row['X4_IDD'],
            'fuente': row['fuente'],
            'metodo': row['metodo'],
            'num_docentes': row['num_docentes']
        })
    
    # Predicciones (prioridad 2)
    for _, row in df_predicciones.iterrows():
        resultados_finales.append({
            'codigo_target': row['codigo_target'],
            'X4_IDD': row['X4_IDD'],
            'fuente': row['fuente'],
            'metodo': row['metodo'],
            'num_docentes': 0
        })
    
    df_resultado = pd.DataFrame(resultados_finales)
    
    print(f"   Total instituciones: {len(df_resultado)}")
    print(f"   Cobertura: {len(df_resultado)}/{len(df_target)} ({len(df_resultado)/len(df_target)*100:.1f}%)")
    
    # Distribución por fuente
    print(f"\n   Distribución por fuente:")
    for fuente, grupo in df_resultado.groupby('fuente'):
        count = len(grupo)
        promedio = grupo['X4_IDD'].mean()
        print(f"     {fuente}: {count} instituciones (IDD prom: {promedio:.1f})")
    
    # Estadísticas finales
    print(f"\n   Estadísticas X4_IDD:")
    print(f"     Rango: {df_resultado['X4_IDD'].min():.1f} - {df_resultado['X4_IDD'].max():.1f}")
    print(f"     Promedio: {df_resultado['X4_IDD'].mean():.1f}")
    print(f"     Desviación estándar: {df_resultado['X4_IDD'].std():.1f}")
    
    # 6. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x4_idd_mejorado_{timestamp}.csv"
    
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n6. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(df_resultado), df_resultado['X4_IDD'].mean()

if __name__ == "__main__":
    csv_file, total, promedio_idd = calcular_x4_idd_mejorado()
    
    print(f"\n=== RESULTADO X4_IDD MEJORADO ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"Promedio IDD: {promedio_idd:.1f}")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X4_IDD calculado para todas las instituciones")
        print(f"[METODOLOGIA] PADD real + Regresión contextual + Limpieza códigos")
    else:
        print(f"\n[PARCIAL] X4_IDD calculado - verificar cobertura")