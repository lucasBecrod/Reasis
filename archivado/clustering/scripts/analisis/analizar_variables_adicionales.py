#!/usr/bin/env python3
"""
Script para analizar variables adicionales disponibles en instituciones_educativas
que podrian robustecer la metodologia de clustering K-Means
"""

import sqlite3
import pandas as pd
import numpy as np

def analizar_variables_adicionales():
    """
    Analiza variables de instituciones_educativas no usadas en indices_metodologicos
    """
    
    print("=== ANALISIS VARIABLES ADICIONALES PARA CLUSTERING ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener estructura de ambas tablas
    print("1. COMPARANDO ESTRUCTURAS DE TABLAS:")
    
    # Variables ya usadas en indices_metodologicos
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    cols_indices = [col[1] for col in cursor.fetchall()]
    
    # Variables disponibles en instituciones_educativas  
    cursor.execute('PRAGMA table_info(instituciones_educativas)')
    cols_instituciones = [col[1] for col in cursor.fetchall()]
    
    print(f"   Columnas en indices_metodologicos: {len(cols_indices)}")
    print(f"   Columnas en instituciones_educativas: {len(cols_instituciones)}")
    
    # 2. Identificar variables nuevas potenciales
    print(f"\n2. IDENTIFICANDO VARIABLES NUEVAS POTENCIALES:")
    
    variables_nuevas_candidatas = []
    for col in cols_instituciones:
        # Excluir variables ya presentes y variables administrativas
        if (col not in cols_indices and 
            col not in ['CODIGO_MODULAR', 'NOMBRE_INSTITUCION', 'NUMERO_FYA'] and
            not col.startswith('created_') and
            not col.startswith('updated_')):
            variables_nuevas_candidatas.append(col)
    
    print(f"   Variables nuevas identificadas: {len(variables_nuevas_candidatas)}")
    
    # 3. Analizar cada variable candidata
    print(f"\n3. ANALISIS DETALLADO DE VARIABLES CANDIDATAS:")
    
    df_instituciones = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
    variables_viables = []
    variables_descartadas = []
    
    for var in variables_nuevas_candidatas:
        print(f"\n   VARIABLE: {var}")
        
        try:
            serie = df_instituciones[var]
            
            # Estadisticas basicas
            total_registros = len(serie)
            no_nulls = serie.notna().sum()
            nulls = total_registros - no_nulls
            completitud = (no_nulls / total_registros) * 100
            
            print(f"     Total registros: {total_registros}")
            print(f"     Con datos: {no_nulls}")
            print(f"     NULLs: {nulls}")
            print(f"     Completitud: {completitud:.1f}%")
            
            # Analizar tipo de datos y valores
            if no_nulls > 0:
                valores_unicos = serie.nunique()
                muestra_valores = serie.dropna().unique()[:10]
                
                print(f"     Valores unicos: {valores_unicos}")
                print(f"     Muestra valores: {list(muestra_valores)}")
                
                # Determinar si es variable numerica viable
                es_numerica = False
                if serie.dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(serie):
                    es_numerica = True
                    if no_nulls > 0:
                        print(f"     Min: {serie.min()}, Max: {serie.max()}")
                        print(f"     Media: {serie.mean():.2f}, Std: {serie.std():.2f}")
                
                # Criterios de viabilidad para clustering
                criterios_viabilidad = {
                    'completitud_minima': completitud >= 50,  # Al menos 50% de datos
                    'variabilidad': valores_unicos > 1,       # Mas de un valor
                    'datos_suficientes': no_nulls >= 50,      # Al menos 50 instituciones con datos
                    'es_numerica_o_categorica': es_numerica or valores_unicos <= 10  # Numerica o pocos valores categoricos
                }
                
                viabilidad_total = all(criterios_viabilidad.values())
                
                print(f"     CRITERIOS VIABILIDAD:")
                for criterio, cumple in criterios_viabilidad.items():
                    status = "[OK]" if cumple else "[NO]"
                    print(f"       {status} {criterio}: {cumple}")
                
                # Clasificacion final
                if viabilidad_total:
                    variables_viables.append({
                        'nombre': var,
                        'completitud': completitud,
                        'valores_unicos': valores_unicos,
                        'es_numerica': es_numerica,
                        'registros_validos': no_nulls,
                        'tipo_recomendado': 'numerica' if es_numerica else 'categorica'
                    })
                    print(f"     [VIABLE] Variable candidata para clustering")
                else:
                    variables_descartadas.append({
                        'nombre': var,
                        'razon': 'No cumple criterios minimos de viabilidad'
                    })
                    print(f"     [DESCARTADA] No cumple criterios minimos")
            else:
                variables_descartadas.append({
                    'nombre': var,
                    'razon': 'Sin datos validos'
                })
                print(f"     [DESCARTADA] Sin datos validos")
                
        except Exception as e:
            variables_descartadas.append({
                'nombre': var,
                'razon': f'Error en analisis: {str(e)}'
            })
            print(f"     [ERROR] {str(e)}")
    
    # 4. Resumen de variables viables
    print(f"\n4. RESUMEN DE VARIABLES VIABLES PARA CLUSTERING:")
    print(f"   Total variables viables: {len(variables_viables)}")
    
    if variables_viables:
        print(f"\n   VARIABLES RECOMENDADAS:")
        variables_viables_sorted = sorted(variables_viables, key=lambda x: x['completitud'], reverse=True)
        
        for i, var in enumerate(variables_viables_sorted, 1):
            print(f"   {i:2d}. {var['nombre']}")
            print(f"       Completitud: {var['completitud']:.1f}%")
            print(f"       Registros validos: {var['registros_validos']}")
            print(f"       Valores unicos: {var['valores_unicos']}")
            print(f"       Tipo: {var['tipo_recomendado']}")
            print(f"       [POTENCIAL] Variable con alto potencial para clustering")
            print()
    
    # 5. Variables especificas mencionadas por usuario
    print(f"5. ANALISIS VARIABLES ESPECIFICAS MENCIONADAS:")
    
    variables_especificas = ['ALTITUD_MSNM']  # Usuario menciono altitud
    
    for var_esp in variables_especificas:
        if var_esp in df_instituciones.columns:
            serie_esp = df_instituciones[var_esp]
            completitud_esp = (serie_esp.notna().sum() / len(serie_esp)) * 100
            
            print(f"\n   {var_esp}:")
            print(f"     Completitud: {completitud_esp:.1f}%")
            if completitud_esp > 0:
                print(f"     Min: {serie_esp.min()}, Max: {serie_esp.max()}")
                print(f"     Media: {serie_esp.mean():.0f} msnm")
                print(f"     Variabilidad: {serie_esp.std():.0f} msnm")
                
                # Esta variable ya esta en indices_metodologicos?
                if var_esp in cols_indices:
                    print(f"     [INFO] Variable ya presente en indices_metodologicos")
                else:
                    print(f"     [NUEVA] Variable potencial para agregar")
        else:
            print(f"\n   {var_esp}: [NO ENCONTRADA] en instituciones_educativas")
    
    # 6. Generar recomendaciones finales
    print(f"\n6. RECOMENDACIONES FINALES PARA ROBUSTECER METODOLOGIA:")
    
    if len(variables_viables) > 0:
        top_variables = variables_viables_sorted[:5]  # Top 5 variables
        
        print(f"   TOP 5 VARIABLES RECOMENDADAS PARA INCORPORAR:")
        for i, var in enumerate(top_variables, 1):
            impacto_potencial = "ALTO" if var['completitud'] > 80 else "MEDIO" if var['completitud'] > 60 else "BAJO"
            print(f"   {i}. {var['nombre']} (Completitud: {var['completitud']:.1f}%, Impacto: {impacto_potencial})")
        
        print(f"\n   ESTRATEGIAS DE IMPLEMENTACION:")
        print(f"   1. Incorporar variables con >80% completitud directamente")
        print(f"   2. Variables 60-80% completitud: imputacion contextual")
        print(f"   3. Variables <60% completitud: evaluar relevancia teorica")
        print(f"   4. Testear clustering con variables adicionales progresivamente")
    else:
        print(f"   [ATENCION] No se identificaron variables adicionales viables")
        print(f"   Recomendacion: Optimizar variables existentes o buscar fuentes externas")
    
    conn.close()
    
    return variables_viables, variables_descartadas

if __name__ == "__main__":
    viables, descartadas = analizar_variables_adicionales()
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Variables viables identificadas: {len(viables)}")
    print(f"Variables descartadas: {len(descartadas)}")
    
    if viables:
        print(f"\n[ACCION SIGUIENTE] Implementar variables recomendadas en clustering")
    else:
        print(f"\n[ACCION SIGUIENTE] Optimizar metodologia con variables actuales")