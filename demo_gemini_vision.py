#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO GEMINI VISION - Casos de uso específicos para proyecto Reasis
Ejemplos prácticos de optimización de datos usando IA
"""
from gemini_optimizer import GeminiOptimizer
import sqlite3
import pandas as pd
import json

def demo_analisis_calidad_datos():
    """Demo: Análisis de calidad de datos usando IA"""
    print("=== DEMO: ANÁLISIS CALIDAD DE DATOS CON IA ===\n")
    
    optimizer = GeminiOptimizer()
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener muestra de datos de instituciones
    query = """
    SELECT codigo_modular, nombre_institucion, region, provincia, distrito, 
           modalidad, nivel_educativo, total_alumnos, total_docentes, es_rural
    FROM instituciones_educativas 
    LIMIT 15
    """
    
    df_sample = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Muestra de datos a analizar:")
    print(df_sample.head().to_string())
    print(f"\nEnviando {len(df_sample)} registros a Gemini para análisis...\n")
    
    # Analizar calidad con IA
    resultado = optimizer.analyze_data_quality("instituciones_educativas", df_sample)
    
    if resultado:
        print("=== RESULTADO ANÁLISIS IA ===")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Interpretar resultados
        print(f"\n=== INTERPRETACIÓN ===")
        print(f"Calidad General: {resultado.get('calidad_general', 'N/A')}")
        print(f"Completitud: {resultado.get('completitud_estimada', 0)*100:.1f}%")
        print(f"Consistencia: {resultado.get('consistencia_estimada', 0)*100:.1f}%")
        print(f"Prioridad Limpieza: {resultado.get('prioridad_limpieza', 'N/A')}")
        
        problemas = resultado.get('problemas_detectados', [])
        if problemas:
            print(f"\nProblemas detectados ({len(problemas)}):")
            for i, problema in enumerate(problemas, 1):
                print(f"  {i}. {problema}")
        
        recomendaciones = resultado.get('recomendaciones', [])
        if recomendaciones:
            print(f"\nRecomendaciones ({len(recomendaciones)}):")
            for i, rec in enumerate(recomendaciones, 1):
                print(f"  {i}. {rec}")
    else:
        print("[ERROR] No se pudo obtener análisis de calidad")

def demo_validacion_institucional():
    """Demo: Validación de consistencia de datos institucionales"""
    print("\n=== DEMO: VALIDACIÓN CONSISTENCIA INSTITUCIONAL ===\n")
    
    optimizer = GeminiOptimizer()
    conn = sqlite3.connect('reasis_database.db')
    
    # Obtener casos específicos para validar
    query = """
    SELECT codigo_modular, nombre_institucion, region, provincia, distrito, 
           modalidad, nivel_educativo, total_alumnos, total_docentes, 
           es_rural, latitud, longitud
    FROM instituciones_educativas 
    WHERE total_alumnos > 0 AND total_docentes > 0
    LIMIT 5
    """
    
    df_casos = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Validando consistencia de instituciones...")
    
    for idx, row in df_casos.iterrows():
        print(f"\n--- Institución {idx + 1}: {row['nombre_institucion']} ---")
        
        # Convertir fila a dict para enviar a IA
        row_dict = row.to_dict()
        
        # Validar con IA
        es_consistente = optimizer.validate_institutional_data(row_dict)
        
        status = "CONSISTENTE" if es_consistente else "INCONSISTENTE" if es_consistente is False else "INDETERMINADO"
        print(f"Resultado: {status}")
        
        if es_consistente is False:
            print("⚠️  REQUIERE REVISIÓN MANUAL")

def demo_normalizacion_columna():
    """Demo: Sugerencias de normalización para columnas específicas"""
    print("\n=== DEMO: SUGERENCIAS NORMALIZACIÓN ===\n")
    
    optimizer = GeminiOptimizer()
    conn = sqlite3.connect('reasis_database.db')
    
    # Analizar columna de modalidad
    query = "SELECT modalidad FROM instituciones_educativas WHERE modalidad IS NOT NULL"
    df_modalidad = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Analizando columna 'modalidad'...")
    print(f"Total registros: {len(df_modalidad)}")
    print(f"Valores únicos: {df_modalidad['modalidad'].nunique()}")
    
    resultado = optimizer.suggest_data_normalization(
        df_modalidad['modalidad'], 
        'modalidad'
    )
    
    if resultado:
        print("\n=== SUGERENCIAS NORMALIZACIÓN ===")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        if resultado.get('requiere_normalizacion'):
            print(f"\n✅ Normalización recomendada: {resultado.get('tipo_normalizacion')}")
            print(f"Confianza: {resultado.get('confianza', 0)*100:.1f}%")
            
            mapeo = resultado.get('mapeo_sugerido', {})
            if mapeo:
                print("\nMapeo sugerido:")
                for actual, normalizado in mapeo.items():
                    print(f"  '{actual}' → '{normalizado}'")
        else:
            print("✅ No requiere normalización")
    else:
        print("[ERROR] No se pudieron obtener sugerencias")

def demo_optimizacion_clustering():
    """Demo: Optimización de variables para clustering K-Means"""
    print("\n=== DEMO: OPTIMIZACIÓN VARIABLES CLUSTERING ===\n")
    
    optimizer = GeminiOptimizer()
    
    # Estado actual de variables
    variables_estado = {
        "Y1_ILA": {"disponible": True, "instituciones": 85, "calidad": "Alta"},
        "Y2_TD": {"disponible": True, "instituciones": 52, "calidad": "Media"},
        "Y3_PR": {"disponible": True, "instituciones": 85, "calidad": "Calculada"},
        "X1_NVC": {"disponible": True, "instituciones": 20, "calidad": "Alta"},
        "X2_TR": {"disponible": True, "instituciones": 87, "calidad": "Mejorada"},
        "X4_IDD": {"disponible": True, "instituciones": 66, "calidad": "Media"},
        "X6_CDD": {"disponible": True, "instituciones": 6, "calidad": "Limitada"},
        "X10_IE": {"disponible": True, "instituciones": 20, "calidad": "Alta"},
        "X11_RED": {"disponible": True, "instituciones": 378, "calidad": "Alta"},
        "X15_MEIB": {"disponible": True, "instituciones": 20, "calidad": "Alta"},
        "X5_ED": {"disponible": False, "instituciones": 0, "calidad": "Faltante"},
        "X12_TOE": {"disponible": False, "instituciones": 0, "calidad": "Faltante"}
    }
    
    schema = {
        "viabilidad_clustering": "Alta/Media/Baja",
        "variables_criticas": ["X1_NVC", "X2_TR"],
        "variables_prescindibles": ["X6_CDD"],
        "instituciones_minimas_recomendadas": 50,
        "metodo_clustering_optimo": "K-Means/Hierarchical/DBSCAN",
        "numero_clusters_sugerido": 4,
        "variables_para_validacion": ["Y1_ILA", "Y2_TD"],
        "limitaciones_detectadas": ["descripcion"],
        "recomendaciones": ["lista", "recomendaciones"],
        "confianza_analisis": 0.90
    }
    
    prompt = f"""
    Analiza este conjunto de variables para clustering de instituciones educativas:
    
    VARIABLES DISPONIBLES (10/12 = 83.3%):
    {json.dumps(variables_estado, indent=2, ensure_ascii=False)}
    
    OBJETIVO: Crear tipologías de instituciones educativas rurales
    
    Evalúa:
    1. ¿Es viable el clustering con estas variables?
    2. ¿Qué variables son más críticas?
    3. ¿Cuál es el número óptimo de clusters?
    4. ¿Qué limitaciones existen?
    5. ¿Qué método de clustering recomiendas?
    """
    
    resultado = optimizer.ask_structured_json(prompt, schema)
    
    if resultado:
        print("=== ANÁLISIS CLUSTERING IA ===")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        print(f"\n=== RECOMENDACIONES CLAVE ===")
        print(f"Viabilidad: {resultado.get('viabilidad_clustering', 'N/A')}")
        print(f"Método recomendado: {resultado.get('metodo_clustering_optimo', 'N/A')}")
        print(f"Clusters sugeridos: {resultado.get('numero_clusters_sugerido', 'N/A')}")
        print(f"Confianza: {resultado.get('confianza_analisis', 0)*100:.1f}%")
    else:
        print("[ERROR] No se pudo obtener análisis de clustering")

if __name__ == "__main__":
    print("🤖 GEMINI AI OPTIMIZATION PARA REASIS 🤖\n")
    
    try:
        # Demo 1: Análisis de calidad
        demo_analisis_calidad_datos()
        
        # Demo 2: Validación institucional  
        demo_validacion_institucional()
        
        # Demo 3: Normalización
        demo_normalizacion_columna()
        
        # Demo 4: Optimización clustering
        demo_optimizacion_clustering()
        
        print("\n🎯 TODOS LOS DEMOS COMPLETADOS")
        print("Gemini AI está listo para optimizar tu base de datos Reasis!")
        
    except Exception as e:
        print(f"[ERROR] Error en demo: {str(e)}")
        import traceback
        traceback.print_exc()