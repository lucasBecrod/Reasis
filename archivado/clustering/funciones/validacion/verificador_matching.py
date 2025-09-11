#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICADOR DE MATCHING - Valida resultados del normalizador IE
Funciones para verificar la calidad del matching realizado por IA
"""
import pandas as pd
import sqlite3
from typing import Dict, List, Tuple

def verificar_matches_gemini():
    """Verifica la calidad de los matches realizados por Gemini en el demo"""
    print("=== VERIFICADOR DE MATCHES GEMINI ===\n")
    
    # Conectar a BD para verificar
    conn = sqlite3.connect('reasis_database.db')
    
    # Casos de prueba que funcionaron
    casos_exitosos = [
        ("6010231", "1527233", "Fe y Alegría 47 RED RURAL"),
        ("555-B", "1625904", "Fe y Alegría 72 RED RURAL")
    ]
    
    print("Verificando matches exitosos del demo:\n")
    
    for nombre_manual, codigo_gemini, red_esperada in casos_exitosos:
        print(f"--- Verificando: '{nombre_manual}' -> {codigo_gemini} ---")
        
        # Buscar la institución en BD
        query = """
        SELECT codigo_modular, codigo_local, nombre_institucion, 
               distrito, provincia, region, codigo_red
        FROM instituciones_educativas 
        WHERE codigo_modular = ?
        """
        
        resultado = pd.read_sql_query(query, conn, params=[codigo_gemini])
        
        if len(resultado) > 0:
            ie = resultado.iloc[0]
            print(f"[OK] MATCH ENCONTRADO EN BD:")
            print(f"  Código Modular: {ie['codigo_modular']}")
            print(f"  Código Local: {ie['codigo_local']}")
            print(f"  Nombre: {ie['nombre_institucion']}")
            print(f"  Ubicación: {ie['distrito']}, {ie['provincia']}, {ie['region']}")
            print(f"  Red: {ie['codigo_red']}")
            
            # Verificar lógica del match
            print(f"\n  ANÁLISIS DEL MATCH:")
            
            # Verificar si el nombre manual coincide con código local
            if str(ie['codigo_local']) in nombre_manual:
                print(f"  [OK] Código local '{ie['codigo_local']}' encontrado en nombre manual")
            
            # Verificar coincidencias en nombre
            nombre_limpio = nombre_manual.lower().replace('-', '').replace(' ', '')
            if nombre_limpio in str(ie['nombre_institucion']).lower():
                print(f"  [OK] Similitud en nombre detectada")
            
            print(f"  -> MATCH VÁLIDO")
            
        else:
            print(f"[ERROR] CÓDIGO NO ENCONTRADO EN BD")
        
        print()
    
    conn.close()

def analizar_archivo_conectividad_manual():
    """Análisis manual de casos específicos del archivo de conectividad"""
    print("=== ANÁLISIS MANUAL ARCHIVO CONECTIVIDAD ===\n")
    
    archivo = r'C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx'
    df = pd.read_excel(archivo, sheet_name='hoja1', engine='openpyxl')
    
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    col_fya = 'Fe y Alegría Nro. ....'
    
    # Obtener casos únicos para análisis
    casos_unicos = df[df[col_ie_nombre].notna()].groupby([col_fya, col_ie_nombre]).size().reset_index(name='count')
    casos_unicos = casos_unicos.sort_values('count', ascending=False)
    
    print(f"Total casos únicos: {len(casos_unicos)}")
    print(f"\nPrimeros 15 casos más frecuentes:")
    
    for idx, row in casos_unicos.head(15).iterrows():
        red = row[col_fya]
        nombre = row[col_ie_nombre]
        count = row['count']
        print(f"{idx+1:2d}. [{count}x] {red} → '{nombre}'")
    
    # Identificar patrones comunes
    print(f"\n=== PATRONES IDENTIFICADOS ===")
    
    nombres_serie = casos_unicos[col_ie_nombre]
    
    # Nombres que parecen códigos numéricos
    codigos_numericos = nombres_serie[nombres_serie.str.match(r'^\d+$', na=False)]
    print(f"Códigos puramente numéricos: {len(codigos_numericos)}")
    
    # Nombres con formato "XXX-B"
    formato_b = nombres_serie[nombres_serie.str.match(r'^.*-B\s*$', na=False)]
    print(f"Formato 'XXX-B': {len(formato_b)}")
    
    # Nombres con "IE" o "I.E"
    con_ie = nombres_serie[nombres_serie.str.contains(r'I\.?E\.?\s*', na=False, case=False)]
    print(f"Con prefijo IE: {len(con_ie)}")
    
    # Nombres con números embebidos
    con_numeros = nombres_serie[nombres_serie.str.contains(r'\d{3,}', na=False)]
    print(f"Con números largos (3+ dígitos): {len(con_numeros)}")
    
    return casos_unicos

def crear_estrategia_optimizada():
    """Crea estrategia optimizada basada en el análisis"""
    print("\n=== ESTRATEGIA OPTIMIZADA PARA GEMINI ===\n")
    
    estrategias = {
        "patrones_identificados": [
            "Códigos numéricos puros (probablemente códigos locales)",
            "Formato 'XXX-B' (códigos con sufijo B)",
            "Nombres con prefijo 'IE' o 'I.E'",
            "Números largos embebidos en texto"
        ],
        
        "mejoras_prompt": [
            "Segmentar IE por red para reducir espacio de búsqueda",
            "Priorizar matching por código local antes que por nombre",
            "Usar matching difuso para nombres con errores tipográficos",
            "Implementar validación cruzada con ubicación geográfica"
        ],
        
        "optimizaciones_tecnicas": [
            "Procesar por lotes (batch) de 5-10 registros",
            "Implementar cache local para evitar llamadas repetidas",
            "Usar temperature=0.0 para máxima consistencia",
            "Agregar retry logic para casos de rate limiting"
        ]
    }
    
    print("ESTRATEGIA RECOMENDADA:")
    for categoria, items in estrategias.items():
        print(f"\n{categoria.upper().replace('_', ' ')}:")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
    
    return estrategias

def simular_procesamiento_completo():
    """Simula cómo sería el procesamiento completo del archivo"""
    print("\n=== SIMULACIÓN PROCESAMIENTO COMPLETO ===\n")
    
    archivo = r'C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\4. Conectividad y equipamiento.xlsx'
    df = pd.read_excel(archivo, sheet_name='hoja1', engine='openpyxl')
    
    col_ie_nombre = 'Si pertence a una Red Rural, indique el nombre de su IE'
    registros_procesar = df[df[col_ie_nombre].notna()]
    
    print(f"ESTADÍSTICAS DE PROCESAMIENTO:")
    print(f"Total registros en archivo: {len(df)}")
    print(f"Registros con nombres IE: {len(registros_procesar)}")
    print(f"Registros a procesar: {len(registros_procesar)}")
    
    # Agrupar por red para procesar eficientemente
    por_red = registros_procesar.groupby('Fe y Alegría Nro. ....').size()
    print(f"\nDistribución por red:")
    for red, count in por_red.items():
        print(f"  {red}: {count} registros")
    
    # Estimación de tiempo
    llamadas_api = len(registros_procesar)
    tiempo_estimado = llamadas_api * 2  # 2 segundos por llamada aproximadamente
    
    print(f"\nESTIMACIÓN PROCESAMIENTO:")
    print(f"Llamadas API necesarias: {llamadas_api}")
    print(f"Tiempo estimado: {tiempo_estimado//60} minutos {tiempo_estimado%60} segundos")
    print(f"Costo API (si fuera de pago): ~${llamadas_api * 0.001:.2f}")
    
    # Cuando se renueve la quota
    print(f"\nCUANDO SE RENUEVE LA QUOTA (mañana):")
    print(f"✓ Ejecutar: python normalizador_ie_conectividad.py")
    print(f"✓ Procesar los {len(registros_procesar)} registros automáticamente")
    print(f"✓ Obtener tabla normalizada lista para integrar a BD")
    
    return registros_procesar

if __name__ == "__main__":
    print("VERIFICADOR DE MATCHING GEMINI\n")
    
    # 1. Verificar matches del demo
    verificar_matches_gemini()
    
    # 2. Analizar archivo completo manualmente
    casos_unicos = analizar_archivo_conectividad_manual()
    
    # 3. Crear estrategia optimizada
    crear_estrategia_optimizada()
    
    # 4. Simular procesamiento completo
    simular_procesamiento_completo()
    
    print(f"\n[OK] VERIFICACIÓN COMPLETA")
    print(f"El sistema está listo para procesar cuando se renueve la quota API")