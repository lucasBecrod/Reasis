#!/usr/bin/env python3
"""
Script para revisar las variables específicas aprobadas por el usuario
y analizar su contenido para codificación numérica
"""

import sqlite3
import pandas as pd

def revisar_variables_aprobadas():
    """
    Revisa las variables aprobadas para integración
    """
    
    print("=== REVISION VARIABLES APROBADAS PARA INTEGRACION ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Variables aprobadas por el usuario
    variables_aprobadas = [
        'ALTITUD',  # Ya está en indices_metodologicos
        'nivel_educativo',  # Variable contextual
        'modalidad',  # Escolarizada/No escolarizada (NULL = Escolarizada)
        'gestion',  # Pública/Privada
        'turno',  # Mañana, Tarde, Noche, combinaciones
        'codigo_carrera',  # Organización pedagógica
        'directivos_total',  # Número de directivos
        'multiplicidad1',  # Variable multiplicidad 1
        'multiplicidad2'   # Variable multiplicidad 2
    ]
    
    # Buscar variable de pobreza distrito
    print("1. BUSCANDO VARIABLE DE POBREZA DEL DISTRITO:")
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(instituciones_educativas)')
    cols_instituciones = [col[1] for col in cursor.fetchall()]
    
    variables_pobreza_candidatas = []
    for col in cols_instituciones:
        if any(term in col.lower() for term in ['pobreza', 'poverty', 'quintil', 'vulnerab', 'socio']):
            variables_pobreza_candidatas.append(col)
    
    print(f"   Variables relacionadas con pobreza encontradas: {len(variables_pobreza_candidatas)}")
    for var in variables_pobreza_candidatas:
        print(f"   - {var}")
    
    if variables_pobreza_candidatas:
        variables_aprobadas.extend(variables_pobreza_candidatas)
    
    print(f"\n2. ANALIZANDO VARIABLES APROBADAS:")
    
    # Cargar datos
    df_instituciones = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
    # Verificar cuáles ya están en indices_metodologicos
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    cols_indices = [col[1] for col in cursor.fetchall()]
    
    variables_analisis = {}
    
    for var in variables_aprobadas:
        print(f"\n   VARIABLE: {var}")
        
        # Verificar si ya existe
        var_upper = var.upper()
        if var_upper in cols_indices:
            print(f"     [YA EXISTE] Variable ya presente en indices_metodologicos")
            continue
            
        # Verificar si existe en instituciones_educativas
        if var not in df_instituciones.columns:
            print(f"     [NO ENCONTRADA] Variable no existe en instituciones_educativas")
            continue
        
        # Analizar contenido
        serie = df_instituciones[var]
        total_registros = len(serie)
        no_nulls = serie.notna().sum()
        nulls = total_registros - no_nulls
        completitud = (no_nulls / total_registros) * 100
        
        print(f"     Total registros: {total_registros}")
        print(f"     Con datos: {no_nulls}")
        print(f"     NULLs: {nulls}")
        print(f"     Completitud: {completitud:.1f}%")
        
        if no_nulls > 0:
            valores_unicos = serie.nunique()
            muestra_valores = serie.value_counts().head(10)
            
            print(f"     Valores unicos: {valores_unicos}")
            print(f"     Distribucion valores (top 10):")
            for valor, count in muestra_valores.items():
                print(f"       {valor}: {count} instituciones ({count/no_nulls*100:.1f}%)")
            
            # Propuesta de codificación numérica
            print(f"     PROPUESTA CODIFICACION NUMERICA:")
            
            if var == 'nivel_educativo':
                codificacion = {
                    'Inicial - Programa no escolarizado': 1,
                    'Inicial - Jardín': 2,
                    'Inicial - Cuna-jardín': 3,
                    'Primaria': 4,
                    'Secundaria': 5,
                    'Básica Alternativa-Inicial e Intermedio': 6,
                    'Básica Alternativa-Avanzado': 7,
                    'Técnico Productiva': 8,
                    'Instituto Superior Tecnológico': 9
                }
                
            elif var == 'modalidad':
                codificacion = {
                    'No escolarizada': 1,
                    'Escolarizada': 2,
                    'No aplica': 2,  # NULL también será 2
                    None: 2  # NULL = Escolarizada
                }
                
            elif var == 'gestion':
                codificacion = {
                    'Pública de gestión directa': 1,
                    'Pública de gestión privada': 2,
                    'Privada': 3
                }
                
            elif var == 'turno':
                codificacion = {
                    'Mañana': 1,
                    'Manana': 1,  # Variante sin tilde
                    'Tarde': 2,
                    'Noche': 3,
                    'Mañana-Tarde': 4,
                    'Manana-Tarde': 4,  # Variante sin tilde
                    'Tarde-Noche': 5,
                    'Mañana-Tarde-Noche': 6,
                    'Manana-Noche': 7
                }
                
            elif var == 'codigo_carrera':
                codificacion = {
                    'No aplica': 0,
                    'Unidocente multigrado': 1,
                    'Polidocente multigrado': 2,
                    'Polidocente Completo': 3
                }
                
            else:
                # Para variables numéricas (directivos_total, multiplicidad1, multiplicidad2)
                if pd.api.types.is_numeric_dtype(serie):
                    codificacion = "MANTENER_VALORES_NUMERICOS"
                else:
                    # Crear codificación automática para otras variables
                    valores_ordenados = sorted(serie.dropna().unique())
                    codificacion = {val: i+1 for i, val in enumerate(valores_ordenados)}
            
            print(f"       {codificacion}")
            
            variables_analisis[var] = {
                'completitud': completitud,
                'valores_unicos': valores_unicos,
                'codificacion': codificacion,
                'nulls': nulls,
                'distribucion': dict(muestra_valores)
            }
    
    print(f"\n3. RESUMEN VARIABLES PARA INTEGRACION:")
    print(f"   Variables analizadas: {len(variables_analisis)}")
    print(f"   Variables viables para integrar:")
    
    for var, info in variables_analisis.items():
        estado = "VIABLE" if info['completitud'] >= 80 else "REQUIERE_IMPUTACION"
        print(f"   - {var}: {info['completitud']:.1f}% completitud, {info['valores_unicos']} valores - [{estado}]")
    
    conn.close()
    
    return variables_analisis

if __name__ == "__main__":
    variables_info = revisar_variables_aprobadas()
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Variables listas para integración: {len(variables_info)}")
    
    if variables_info:
        print(f"\n[SIGUIENTE PASO] Implementar integración con codificación numérica")
    else:
        print(f"\n[ATENCION] Verificar disponibilidad de variables solicitadas")