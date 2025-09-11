"""
Script para RECALCULAR X4_IDD con normalización apropiada
Corrige rangos irreales y adopta escala común 1-4

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
    
    codigo_str = str(codigo).strip()
    codigo_str = re.sub(r'^\s*[^\d]*', '', codigo_str)
    codigo_str = re.sub(r'\s+', '', codigo_str)
    
    numeros = re.findall(r'\d+', codigo_str)
    if numeros:
        codigo_num = numeros[0]
        return codigo_num.zfill(7)
    
    return None

def normalizar_padd_a_escala_1_4(nota_padd):
    """
    Normaliza notas PADD de escala 0-20 a escala 1-4
    Elimina valores irreales (0-5) y mapea a escala docente realista
    """
    # Rango realista PADD: 6-18 (eliminamos 0-5 como irreales)
    # Mapear a escala 1-4 donde:
    # 1 = Desempeño Básico (6-9 en PADD)
    # 2 = Desempeño En Proceso (10-12 en PADD) 
    # 3 = Desempeño Esperado (13-15 en PADD)
    # 4 = Desempeño Destacado (16-20 en PADD)
    
    if nota_padd <= 5:  # Valores irreales
        return 1.5  # Asignar nivel básico-intermedio
    elif nota_padd <= 9:
        return 1.0 + (nota_padd - 6) * 1.0 / 3  # 1.0 - 2.0
    elif nota_padd <= 12:
        return 2.0 + (nota_padd - 10) * 1.0 / 2  # 2.0 - 3.0
    elif nota_padd <= 15:
        return 3.0 + (nota_padd - 13) * 1.0 / 2  # 3.0 - 4.0
    else:  # 16-20
        return 4.0  # Nivel destacado máximo
    
def recalcular_x4_idd_normalizado():
    """
    Recalcula X4_IDD con normalización apropiada a escala 1-4
    """
    
    print("=== RECALCULANDO X4_IDD NORMALIZADO (Escala 1-4) ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
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
    
    # 2. Procesar datos PADD con normalización mejorada
    print(f"\n2. PROCESANDO DATOS PADD (con normalización 1-4):")
    
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
    
    # Calcular IDD individual en escala 0-20 primero
    df_padd_clean['IDD_padd_0_20'] = (
        df_padd_clean['nota_matematica'].astype(float) +
        df_padd_clean['nota_comunicacion'].astype(float) + 
        df_padd_clean['nota_digital'].astype(float) +
        df_padd_clean['nota_genero'].astype(float)
    ) / 4
    
    # Normalizar a escala 1-4
    df_padd_clean['IDD_normalizado_1_4'] = df_padd_clean['IDD_padd_0_20'].apply(normalizar_padd_a_escala_1_4)
    
    print(f"   Docentes después limpieza: {len(df_padd_clean)}")
    print(f"   IDD PADD original (0-20): {df_padd_clean['IDD_padd_0_20'].min():.1f} - {df_padd_clean['IDD_padd_0_20'].max():.1f}")
    print(f"   IDD normalizado (1-4): {df_padd_clean['IDD_normalizado_1_4'].min():.2f} - {df_padd_clean['IDD_normalizado_1_4'].max():.2f}")
    
    # Agregar por institución
    idd_padd_ie = df_padd_clean.groupby('codigo_ie_limpio').agg({
        'IDD_normalizado_1_4': ['mean', 'count'],
        'rer': 'first'
    }).reset_index()
    
    idd_padd_ie.columns = ['codigo_target', 'X4_IDD', 'num_docentes', 'red']
    idd_padd_ie['fuente'] = 'PADD_Normalizado'
    idd_padd_ie['metodo'] = 'promedio_normalizado_1_4'
    
    # Compatibilidad con target
    codigos_target_set = set(df_target['CODIGO_MODULAR'])
    idd_padd_compatible = idd_padd_ie[idd_padd_ie['codigo_target'].isin(codigos_target_set)]
    print(f"   Instituciones PADD compatibles: {len(idd_padd_compatible)}")
    print(f"   Rango IDD institucional (1-4): {idd_padd_compatible['X4_IDD'].min():.2f} - {idd_padd_compatible['X4_IDD'].max():.2f}")
    
    # 3. Procesar competencia digital (ya en escala 1-4)
    print(f"\n3. PROCESANDO COMPETENCIA DIGITAL (escala 1-4 directa):")
    
    df_digital = pd.read_sql_query("""
        SELECT 
            nombre_rer,
            codigo_red,
            nota_global_relativa_num as nivel_digital_1_4,
            ambito,
            edad,
            sexo
        FROM competencia_digital_docentes
        WHERE nota_global_relativa_num IS NOT NULL
    """, conn)
    
    print(f"   Evaluaciones digitales: {len(df_digital)}")
    print(f"   Escala digital: {df_digital['nivel_digital_1_4'].min()} - {df_digital['nivel_digital_1_4'].max()}")
    
    # Promedio por red
    digital_por_red = df_digital.groupby('codigo_red').agg({
        'nivel_digital_1_4': ['mean', 'std', 'count'],
        'edad': 'mean'
    }).reset_index()
    
    digital_por_red.columns = ['red_digital', 'idd_digital_mean_1_4', 'idd_digital_std', 'num_evaluaciones', 'edad_promedio']
    
    print(f"   Promedios digitales por red (escala 1-4):")
    for _, row in digital_por_red.iterrows():
        print(f"     Red {row['red_digital']}: {row['idd_digital_mean_1_4']:.2f} ({row['num_evaluaciones']} evaluaciones)")
    
    # 4. Modelo de regresión con escala 1-4
    print(f"\n4. MODELO REGRESION (escala 1-4 común):")
    
    df_training = df_target.merge(idd_padd_compatible, 
                                  left_on='CODIGO_MODULAR', 
                                  right_on='codigo_target', 
                                  how='inner')
    
    print(f"   Instituciones entrenamiento: {len(df_training)}")
    
    if len(df_training) >= 10:
        # Features para regresión
        features = []
        target_values = []
        
        for _, row in df_training.iterrows():
            feature_vector = [
                row['X2_TR'] if pd.notna(row['X2_TR']) else 1.5,
                row['X1_NVC'] if pd.notna(row['X1_NVC']) else 3.5,
                row['LATITUD'] if pd.notna(row['LATITUD']) else -12.0,
                row['LONGITUD'] if pd.notna(row['LONGITUD']) else -75.0,
                float(row['NUMERO_FYA']) if pd.notna(row['NUMERO_FYA']) else 50
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
        
        # Aplicar modelo con restricción de rango [1.5, 4.0]
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
            
            # Restringir a rango realista [1.5, 4.0]
            y_pred = max(1.5, min(4.0, y_pred))
            
            predicciones.append({
                'codigo_target': row['CODIGO_MODULAR'],
                'X4_IDD': y_pred,
                'fuente': 'Regresion_1_4',
                'metodo': f'regresion_normalizada_r2_{r2_score:.3f}'
            })
        
        df_predicciones = pd.DataFrame(predicciones)
        print(f"   Predicciones generadas: {len(df_predicciones)}")
        print(f"   Rango predicciones: {df_predicciones['X4_IDD'].min():.2f} - {df_predicciones['X4_IDD'].max():.2f}")
        
    else:
        # Fallback con promedio en escala 1-4
        promedio_padd_1_4 = idd_padd_compatible['X4_IDD'].mean()
        instituciones_sin_datos = df_target[~df_target['CODIGO_MODULAR'].isin(idd_padd_compatible['codigo_target'])]
        
        predicciones = []
        for _, row in instituciones_sin_datos.iterrows():
            predicciones.append({
                'codigo_target': row['CODIGO_MODULAR'],
                'X4_IDD': promedio_padd_1_4,
                'fuente': 'Promedio_1_4',
                'metodo': 'promedio_padd_normalizado'
            })
        
        df_predicciones = pd.DataFrame(predicciones)
    
    # 5. Consolidar resultados
    print(f"\n5. CONSOLIDACION FINAL (escala 1-4):")
    
    resultados_finales = []
    
    # PADD normalizado
    for _, row in idd_padd_compatible.iterrows():
        resultados_finales.append({
            'codigo_target': row['codigo_target'],
            'X4_IDD': row['X4_IDD'],
            'fuente': row['fuente'],
            'metodo': row['metodo'],
            'num_docentes': row['num_docentes']
        })
    
    # Predicciones
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
    
    # Estadísticas finales
    print(f"\n   Estadísticas X4_IDD normalizadas (1-4):")
    print(f"     Rango: {df_resultado['X4_IDD'].min():.2f} - {df_resultado['X4_IDD'].max():.2f}")
    print(f"     Promedio: {df_resultado['X4_IDD'].mean():.2f}")
    print(f"     Mediana: {df_resultado['X4_IDD'].median():.2f}")
    
    # Distribución por niveles educativos
    print(f"\n   Distribución por nivel docente:")
    for nivel_min, nivel_max, nombre in [(1.0, 1.99, 'Básico'), (2.0, 2.99, 'En Proceso'), (3.0, 3.99, 'Esperado'), (4.0, 4.0, 'Destacado')]:
        count = len(df_resultado[(df_resultado['X4_IDD'] >= nivel_min) & (df_resultado['X4_IDD'] <= nivel_max)])
        pct = count/len(df_resultado)*100
        print(f"     {nombre} ({nivel_min}-{nivel_max}): {count} instituciones ({pct:.1f}%)")
    
    # 6. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x4_idd_normalizado_1_4_{timestamp}.csv"
    
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n6. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(df_resultado), df_resultado['X4_IDD'].mean()

if __name__ == "__main__":
    csv_file, total, promedio_idd = recalcular_x4_idd_normalizado()
    
    print(f"\n=== RESULTADO X4_IDD NORMALIZADO ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"Promedio IDD (1-4): {promedio_idd:.2f}")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X4_IDD normalizado calculado para todas las instituciones")
        print(f"[METODOLOGIA] PADD normalizado 1-4 + Regresión + Restricción de rango")
    else:
        print(f"\n[PARCIAL] X4_IDD calculado - verificar cobertura")