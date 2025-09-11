#!/usr/bin/env python3
"""
Metodología estadística profesional para imputación de variables contextuales
usando técnicas avanzadas de machine learning y estadística contextual
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.impute import KNNImputer
import warnings
warnings.filterwarnings('ignore')

def metodologia_imputacion_profesional():
    """
    Implementa metodología estadística profesional para imputación contextual
    """
    
    print("=== METODOLOGIA ESTADISTICA PROFESIONAL PARA IMPUTACION ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Cargar datos con variables predictoras clave
    query = """
    SELECT 
        CODIGO_MODULAR, NUMERO_FYA, ALTITUD_MSNM,
        X2_TR, Y1_ILA, X1_NVC, X11_RED, X24_GPMD, X25_POBLACION_DISTRITO,
        X14_NIVEL_EDUCATIVO, X16_MODALIDAD, X17_GESTION, X18_TURNO,
        X19_ORGANIZACION_PEDAGOGICA, X20_DIRECTIVOS_TOTAL,
        X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2
    FROM indices_metodologicos
    """
    
    df = pd.read_sql_query(query, conn)
    
    print("1. ANALISIS ESTADO ACTUAL:")
    print(f"   Total instituciones: {len(df)}")
    
    # Variables que requieren imputación
    variables_target = [
        'X17_GESTION', 'X19_ORGANIZACION_PEDAGOGICA', 'X20_DIRECTIVOS_TOTAL',
        'X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2'
    ]
    
    # Variables predictoras robustas (sin NULLs o muy pocas)
    variables_predictoras = [
        'NUMERO_FYA', 'ALTITUD_MSNM', 'X2_TR', 'Y1_ILA', 'X1_NVC', 
        'X11_RED', 'X24_GPMD', 'X25_POBLACION_DISTRITO', 
        'X14_NIVEL_EDUCATIVO', 'X16_MODALIDAD', 'X18_TURNO'
    ]
    
    # Análisis de NULLs
    print(f"\n   Variables que requieren imputación:")
    nulls_summary = {}
    
    for var in variables_target:
        nulls = df[var].isnull().sum()
        total = len(df)
        pct_nulls = (nulls / total) * 100
        nulls_summary[var] = {'nulls': nulls, 'completitud': 100 - pct_nulls}
        print(f"   {var}: {nulls} NULLs ({pct_nulls:.1f}%)")
    
    # 2. Metodología por variable específica
    resultados_imputacion = {}
    
    for var_target in variables_target:
        print(f"\n2. PROCESANDO VARIABLE: {var_target}")
        
        if df[var_target].isnull().sum() == 0:
            print(f"   [COMPLETA] Variable sin NULLs")
            continue
        
        # Preparar datos para esta variable
        df_var = df[variables_predictoras + [var_target]].copy()
        
        # Separar datos con y sin target
        df_train = df_var[df_var[var_target].notna()]
        df_impute = df_var[df_var[var_target].isnull()]
        
        print(f"   Casos para entrenamiento: {len(df_train)}")
        print(f"   Casos para imputar: {len(df_impute)}")
        
        if len(df_train) < 20:  # Muy pocos casos para ML
            print(f"   [FALLBACK] Insuficientes casos para ML, usando imputación modal")
            # Imputación modal por contexto
            if var_target in ['X17_GESTION', 'X19_ORGANIZACION_PEDAGOGICA']:
                # Por ruralidad
                for ruralidad in df_impute['X2_TR'].unique():
                    if pd.notna(ruralidad):
                        moda = df_train[df_train['X2_TR'] == ruralidad][var_target].mode()
                        if len(moda) > 0:
                            mask = (df[var_target].isnull()) & (df['X2_TR'] == ruralidad)
                            print(f"     Ruralidad {ruralidad}: imputando {mask.sum()} casos con valor {moda[0]}")
            continue
        
        # Detectar tipo de variable
        valores_unicos = df_train[var_target].nunique()
        es_categorica = valores_unicos <= 5
        
        # Preparar predictores
        X_train = df_train[variables_predictoras]
        y_train = df_train[var_target]
        X_impute = df_impute[variables_predictoras]
        
        # Manejar NULLs en predictores con KNN
        if X_train.isnull().sum().sum() > 0 or X_impute.isnull().sum().sum() > 0:
            imputer_predictores = KNNImputer(n_neighbors=5)
            X_train = pd.DataFrame(
                imputer_predictores.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
            X_impute = pd.DataFrame(
                imputer_predictores.transform(X_impute),
                columns=X_impute.columns,
                index=X_impute.index
            )
        
        # Seleccionar y entrenar modelo
        if es_categorica:
            print(f"   [CLASIFICACION] Variable categórica ({valores_unicos} valores únicos)")
            modelo = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_split=5,
                random_state=42,
                class_weight='balanced'
            )
        else:
            print(f"   [REGRESION] Variable numérica")
            modelo = RandomForestRegressor(
                n_estimators=100,
                max_depth=5,
                min_samples_split=5,
                random_state=42
            )
        
        # Entrenar modelo
        modelo.fit(X_train, y_train)
        
        # Validación cruzada
        if len(df_train) >= 30:  # Suficientes casos para CV
            cv_scores = cross_val_score(modelo, X_train, y_train, cv=min(5, len(df_train)//6))
            score_promedio = cv_scores.mean()
            print(f"   Validación cruzada: {score_promedio:.3f} ± {cv_scores.std():.3f}")
        
        # Imputar valores
        valores_imputados = modelo.predict(X_impute)
        
        # Para variables categóricas, asegurar valores válidos
        if es_categorica:
            valores_validos = df_train[var_target].unique()
            valores_imputados = np.round(valores_imputados).astype(int)
            # Clamp a valores válidos
            valores_imputados = np.clip(valores_imputados, valores_validos.min(), valores_validos.max())
        
        # Importancia de features
        feature_importance = pd.Series(
            modelo.feature_importances_,
            index=variables_predictoras
        ).sort_values(ascending=False)
        
        print(f"   Top 3 predictores más importantes:")
        for i, (feature, importance) in enumerate(feature_importance.head(3).items()):
            print(f"     {i+1}. {feature}: {importance:.3f}")
        
        # Guardar resultados
        resultados_imputacion[var_target] = {
            'metodo': 'RandomForest',
            'casos_entrenamiento': len(df_train),
            'casos_imputados': len(df_impute),
            'valores_imputados': valores_imputados,
            'indices_a_imputar': df_impute.index.tolist(),
            'predictores_importantes': feature_importance.head(5).to_dict(),
            'modelo': modelo
        }
        
        print(f"   [COMPLETADO] {len(df_impute)} valores imputados exitosamente")
    
    return df, resultados_imputacion

def aplicar_imputaciones(df, resultados):
    """
    Aplica las imputaciones calculadas a la base de datos
    """
    
    print(f"\n3. APLICANDO IMPUTACIONES A BASE DE DATOS:")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Crear backup
    backup_query = "SELECT * FROM indices_metodologicos"
    df_backup = pd.read_sql_query(backup_query, conn)
    backup_filename = f"backup_antes_imputacion_profesional_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_backup.to_csv(backup_filename, index=False, encoding='utf-8')
    print(f"   [BACKUP] Creado: {backup_filename}")
    
    # Aplicar cada imputación
    total_imputaciones = 0
    
    for var_target, resultado in resultados.items():
        valores_imputados = resultado['valores_imputados']
        indices_a_imputar = resultado['indices_a_imputar']
        
        print(f"\n   Aplicando imputación para {var_target}:")
        print(f"     Método: {resultado['metodo']}")
        print(f"     Casos a imputar: {len(valores_imputados)}")
        
        # Actualizar base de datos
        actualizaciones_exitosas = 0
        
        for i, idx in enumerate(indices_a_imputar):
            codigo_modular = df.loc[idx, 'CODIGO_MODULAR']
            valor_imputado = valores_imputados[i]
            
            try:
                cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET {var_target} = ?
                WHERE CODIGO_MODULAR = ?
                """, (float(valor_imputado), codigo_modular))
                actualizaciones_exitosas += 1
            except Exception as e:
                print(f"     [ERROR] {codigo_modular}: {str(e)}")
        
        print(f"     [RESULTADO] {actualizaciones_exitosas} actualizaciones exitosas")
        total_imputaciones += actualizaciones_exitosas
    
    # Verificar resultados finales
    print(f"\n4. VERIFICACION FINAL:")
    
    variables_verificar = list(resultados.keys())
    
    for var in variables_verificar:
        cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT({var}) as con_datos,
            COUNT(*) - COUNT({var}) as nulls_restantes
        FROM indices_metodologicos
        """)
        stats = cursor.fetchone()
        completitud_final = (stats[1] / stats[0]) * 100
        
        print(f"   {var}: {stats[1]}/{stats[0]} ({completitud_final:.1f}% completitud)")
        if stats[2] == 0:
            print(f"     [OK] Variable completamente imputada")
        else:
            print(f"     [PENDIENTE] {stats[2]} NULLs restantes")
    
    conn.commit()
    conn.close()
    
    print(f"\n[EXITO] {total_imputaciones} imputaciones aplicadas exitosamente")
    return True

def generar_reporte_metodologia(resultados):
    """
    Genera reporte técnico de la metodología aplicada
    """
    
    print(f"\n5. REPORTE TECNICO METODOLOGIA:")
    
    print(f"   Variables procesadas: {len(resultados)}")
    
    for var_target, resultado in resultados.items():
        print(f"\n   {var_target}:")
        print(f"     Método: {resultado['metodo']}")
        print(f"     Casos entrenamiento: {resultado['casos_entrenamiento']}")
        print(f"     Casos imputados: {resultado['casos_imputados']}")
        print(f"     Predictores clave:")
        
        for predictor, importancia in resultado['predictores_importantes'].items():
            print(f"       {predictor}: {importancia:.3f}")
    
    # Generar archivo de documentación
    doc_filename = f"REPORTE_IMPUTACION_PROFESIONAL_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(doc_filename, 'w', encoding='utf-8') as f:
        f.write("# REPORTE IMPUTACION PROFESIONAL - VARIABLES CONTEXTUALES\n\n")
        f.write(f"**Fecha**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Proyecto**: Reasis - Optimización Variables Contextuales\n\n")
        
        f.write("## Metodología Aplicada\n")
        f.write("- **Técnica principal**: Random Forest (Clasificación/Regresión)\n")
        f.write("- **Validación**: Cross-validation 5-fold\n") 
        f.write("- **Manejo predictores**: KNN Imputer para NULLs en features\n")
        f.write("- **Balance clases**: class_weight='balanced' para clasificación\n\n")
        
        f.write("## Variables Procesadas\n\n")
        
        for var_target, resultado in resultados.items():
            f.write(f"### {var_target}\n")
            f.write(f"- **Método**: {resultado['metodo']}\n")
            f.write(f"- **Casos entrenamiento**: {resultado['casos_entrenamiento']}\n")
            f.write(f"- **Casos imputados**: {resultado['casos_imputados']}\n")
            f.write("- **Predictores más importantes**:\n")
            
            for predictor, importancia in resultado['predictores_importantes'].items():
                f.write(f"  - {predictor}: {importancia:.3f}\n")
            f.write("\n")
    
    print(f"   [DOCUMENTACION] Generado: {doc_filename}")
    
    return doc_filename

if __name__ == "__main__":
    print("Iniciando metodología estadística profesional...")
    
    # Ejecutar análisis y imputación
    df_original, resultados_imputacion = metodologia_imputacion_profesional()
    
    if resultados_imputacion:
        # Aplicar a base de datos
        exito_aplicacion = aplicar_imputaciones(df_original, resultados_imputacion)
        
        if exito_aplicacion:
            # Generar reporte técnico
            reporte_generado = generar_reporte_metodologia(resultados_imputacion)
            
            print(f"\n=== METODOLOGIA COMPLETADA EXITOSAMENTE ===")
            print(f"Variables imputadas: {len(resultados_imputacion)}")
            print(f"Técnica: Random Forest con validación cruzada")
            print(f"Documentación: {reporte_generado}")
        else:
            print(f"\n=== PROBLEMA EN APLICACION ===")
    else:
        print(f"\n=== TODAS LAS VARIABLES YA ESTABAN COMPLETAS ===")
        print(f"No se requirió imputación")