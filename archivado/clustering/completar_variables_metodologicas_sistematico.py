#!/usr/bin/env python3
"""
Completar variables metodológicas en indices_metodologicos de forma sistemática
Estrategia: Mapeo directo desde instituciones_educativas + imputación por RER cuando sea necesario
"""

import sqlite3
import pandas as pd
import numpy as np

def completar_variables_directas():
    """Completar variables que tienen mapeo directo desde instituciones_educativas"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== COMPLETANDO VARIABLES CON MAPEO DIRECTO ===")
    
    # Mapeo directo variable_indices <- columna_ie
    mapeo_directo = {
        'X13_TMATRC': 'X13_TMATRC',
        'X14_NIVEL_EDUCATIVO': 'nivel_educativo', 
        'X16_MODALIDAD': 'modalidad',
        'X17_GESTION': 'gestion',
        'X18_TURNO': 'turno',
        'X20_DIRECTIVOS_TOTAL': 'directivos_total',
        'X21_MULTIPLICIDAD1': 'multiplicidad1',
        'X22_MULTIPLICIDAD2': 'multiplicidad2',
        'X24_GPMD': 'grupo_pobreza_monetaria_distrito',
        'X25_POBLACION_DISTRITO': 'poblacion_proyectada_2020_distrito'
    }
    
    # Mapeo para variables categóricas que necesitan codificación
    codificaciones = {
        'X14_NIVEL_EDUCATIVO': {
            'Inicial': 1, 'Primaria': 2, 'Secundaria': 3, 'Básica Alternativa': 4,
            'Técnico-Productiva': 5, 'Superior No Universitaria': 6
        },
        'X16_MODALIDAD': {
            'EBR': 1, 'Básica Regular': 1, 'EBA': 2, 'EBE': 3, 'Básica Alternativa': 2
        },
        'X17_GESTION': {
            'Pública': 1, 'Privada': 2, 'Público': 1
        },
        'X18_TURNO': {
            'Mañana': 1, 'Tarde': 2, 'Noche': 3, 'Continuo': 4, 'Mixto': 5
        }
    }
    
    resultados = {}
    
    for var_indices, col_ie in mapeo_directo.items():
        print(f"\nProcesando {var_indices} <- {col_ie}:")
        
        try:
            if var_indices in codificaciones:
                # Variable categórica - necesita codificación
                df_datos = pd.read_sql_query(f"""
                    SELECT im.CODIGO_MODULAR, ie.{col_ie}
                    FROM indices_metodologicos im
                    JOIN instituciones_educativas ie ON im.CODIGO_MODULAR = ie.codigo_modular
                    WHERE ie.{col_ie} IS NOT NULL
                """, conn)
                
                if len(df_datos) > 0:
                    # Aplicar codificación
                    codigos = codificaciones[var_indices]
                    df_datos['valor_codificado'] = df_datos[col_ie].map(codigos)
                    
                    # Actualizar registros exitosos
                    actualizados = 0
                    for _, row in df_datos.iterrows():
                        if pd.notna(row['valor_codificado']):
                            cursor = conn.cursor()
                            cursor.execute(f"""
                                UPDATE indices_metodologicos 
                                SET {var_indices} = {row['valor_codificado']}
                                WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
                            """)
                            actualizados += 1
                    
                    conn.commit()
                    print(f"  [OK] {actualizados} registros codificados y actualizados")
                    resultados[var_indices] = actualizados
                else:
                    print(f"  [NO DATOS] No hay datos en {col_ie}")
                    resultados[var_indices] = 0
                    
            else:
                # Variable numérica - copia directa
                query_update = f"""
                UPDATE indices_metodologicos 
                SET {var_indices} = (
                    SELECT ie.{col_ie}
                    FROM instituciones_educativas ie 
                    WHERE ie.codigo_modular = indices_metodologicos.CODIGO_MODULAR
                    AND ie.{col_ie} IS NOT NULL
                )
                WHERE EXISTS (
                    SELECT 1 FROM instituciones_educativas ie 
                    WHERE ie.codigo_modular = indices_metodologicos.CODIGO_MODULAR
                    AND ie.{col_ie} IS NOT NULL
                )
                """
                
                cursor = conn.cursor()
                cursor.execute(query_update)
                actualizados = cursor.rowcount
                conn.commit()
                
                print(f"  [OK] {actualizados} registros actualizados directamente")
                resultados[var_indices] = actualizados
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            resultados[var_indices] = 0
    
    conn.close()
    return resultados

def imputar_por_distrito_poblacion():
    """Completar X25_POBLACION_DISTRITO usando otros registros del mismo distrito"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== IMPUTACION POR DISTRITO: X25_POBLACION_DISTRITO ===")
    
    # Encontrar registros sin población pero con distrito conocido
    df_sin_poblacion = pd.read_sql_query("""
        SELECT im.CODIGO_MODULAR, ie.distrito
        FROM indices_metodologicos im
        JOIN instituciones_educativas ie ON im.CODIGO_MODULAR = ie.codigo_modular
        WHERE im.X25_POBLACION_DISTRITO IS NULL 
        AND ie.distrito IS NOT NULL
    """, conn)
    
    print(f"Registros sin población: {len(df_sin_poblacion)}")
    
    imputados = 0
    for _, row in df_sin_poblacion.iterrows():
        # Buscar población de otras instituciones del mismo distrito
        df_poblacion = pd.read_sql_query(f"""
            SELECT DISTINCT ie.poblacion_proyectada_2020_distrito
            FROM instituciones_educativas ie
            WHERE ie.distrito = '{row['distrito']}'
            AND ie.poblacion_proyectada_2020_distrito IS NOT NULL
            LIMIT 1
        """, conn)
        
        if len(df_poblacion) > 0:
            poblacion = df_poblacion['poblacion_proyectada_2020_distrito'].iloc[0]
            
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE indices_metodologicos 
                SET X25_POBLACION_DISTRITO = {poblacion}
                WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
            """)
            imputados += 1
    
    conn.commit()
    print(f"[OK] {imputados} registros imputados por distrito")
    
    conn.close()
    return imputados

def imputar_por_rer():
    """Imputar valores faltantes usando promedio de la RER (NUMERO_FYA)"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== IMPUTACION POR RER: VARIABLES NUMERICAS ===")
    
    variables_numericas = ['X20_DIRECTIVOS_TOTAL', 'X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2', 
                          'X24_GPMD', 'X25_POBLACION_DISTRITO']
    
    resultados_imputacion = {}
    
    for variable in variables_numericas:
        print(f"\nImputando {variable}:")
        
        # Obtener registros que necesitan imputación
        df_necesitan = pd.read_sql_query(f"""
            SELECT CODIGO_MODULAR, NUMERO_FYA 
            FROM indices_metodologicos 
            WHERE {variable} IS NULL
        """, conn)
        
        imputados = 0
        for _, row in df_necesitan.iterrows():
            # Calcular promedio de la RER
            df_promedio = pd.read_sql_query(f"""
                SELECT AVG({variable}) as promedio_rer
                FROM indices_metodologicos 
                WHERE NUMERO_FYA = {row['NUMERO_FYA']}
                AND {variable} IS NOT NULL
            """, conn)
            
            if len(df_promedio) > 0 and pd.notna(df_promedio['promedio_rer'].iloc[0]):
                promedio = df_promedio['promedio_rer'].iloc[0]
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE indices_metodologicos 
                    SET {variable} = {promedio:.2f}
                    WHERE CODIGO_MODULAR = '{row['CODIGO_MODULAR']}'
                """)
                imputados += 1
        
        conn.commit()
        print(f"  [OK] {imputados} registros imputados por promedio RER")
        resultados_imputacion[variable] = imputados
    
    conn.close()
    return resultados_imputacion

def verificar_completitud():
    """Verificar completitud final de variables"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION DE COMPLETITUD FINAL ===")
    
    variables_completar = [
        'X13_TMATRC', 'X14_NIVEL_EDUCATIVO', 'X16_MODALIDAD', 'X17_GESTION', 
        'X18_TURNO', 'X20_DIRECTIVOS_TOTAL', 'X21_MULTIPLICIDAD1', 
        'X22_MULTIPLICIDAD2', 'X24_GPMD', 'X25_POBLACION_DISTRITO'
    ]
    
    df_total = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    total = df_total['total'].iloc[0]
    
    print(f"Total instituciones: {total}")
    print("\nCompletitud por variable:")
    
    for variable in variables_completar:
        df_completos = pd.read_sql_query(f"""
            SELECT COUNT(*) as completos 
            FROM indices_metodologicos 
            WHERE {variable} IS NOT NULL
        """, conn)
        completos = df_completos['completos'].iloc[0]
        completitud = (completos / total) * 100
        
        status = "[COMPLETO]" if completitud == 100 else f"[{completitud:.1f}%]"
        print(f"  {status} {variable}: {completos}/{total}")
    
    conn.close()

def main():
    """Función principal"""
    
    print("COMPLETAR VARIABLES METODOLOGICAS SISTEMATICAMENTE")
    print("=" * 60)
    print("Estrategia: Mapeo directo + Imputacion por distrito + Imputacion por RER")
    
    try:
        # 1. Completar variables con mapeo directo
        resultados_directos = completar_variables_directas()
        
        # 2. Imputación especial por distrito (población)
        imputados_distrito = imputar_por_distrito_poblacion()
        
        # 3. Imputación por RER para valores faltantes
        resultados_rer = imputar_por_rer()
        
        # 4. Verificar completitud final
        verificar_completitud()
        
        print("\n" + "=" * 60)
        print("[COMPLETADO] VARIABLES DIRECTAS PROCESADAS")
        print("Siguiente paso: Completar variables auxiliares (Y2_TD, Y3_PR, X5_ED, etc.)")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()