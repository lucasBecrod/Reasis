#!/usr/bin/env python3
"""
Análisis de datos disponibles para cálculo de X11_RED
Revisa completitud de total_docentes y total_alumnos en tabla instituciones_educativas
"""

import sqlite3
import pandas as pd
import numpy as np

def main():
    print("=== ANÁLISIS DE DATOS PARA X11_RED ===")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Analizar datos en tabla instituciones_educativas
        print("\n1. ANÁLISIS TABLA INSTITUCIONES_EDUCATIVAS")
        query_ie = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            total_docentes,
            total_alumnos,
            nombre_red_fya_matched as red_fya,
            entra_estudio_clustering
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        """
        
        df_ie = pd.read_sql_query(query_ie, conn)
        print(f"   - Total instituciones: {len(df_ie)}")
        
        # Análisis de completitud total_docentes
        docentes_no_null = df_ie['total_docentes'].notna().sum()
        docentes_completitud = (docentes_no_null / len(df_ie)) * 100
        
        print(f"   - Instituciones con total_docentes: {docentes_no_null} ({docentes_completitud:.1f}%)")
        
        # Análisis de completitud total_alumnos
        alumnos_no_null = df_ie['total_alumnos'].notna().sum()
        alumnos_completitud = (alumnos_no_null / len(df_ie)) * 100
        
        print(f"   - Instituciones con total_alumnos: {alumnos_no_null} ({alumnos_completitud:.1f}%)")
        
        # Instituciones con ambos datos
        ambos_datos = df_ie[(df_ie['total_docentes'].notna()) & (df_ie['total_alumnos'].notna())]
        ambos_completitud = (len(ambos_datos) / len(df_ie)) * 100
        
        print(f"   - Instituciones con AMBOS datos: {len(ambos_datos)} ({ambos_completitud:.1f}%)")
        
        # Estadísticas básicas de los que tienen datos
        if len(ambos_datos) > 0:
            print(f"\n   ESTADÍSTICAS DE INSTITUCIONES CON AMBOS DATOS:")
            print(f"   - Docentes promedio: {ambos_datos['total_docentes'].mean():.1f}")
            print(f"   - Docentes rango: {ambos_datos['total_docentes'].min()}-{ambos_datos['total_docentes'].max()}")
            print(f"   - Alumnos promedio: {ambos_datos['total_alumnos'].mean():.1f}")
            print(f"   - Alumnos rango: {ambos_datos['total_alumnos'].min()}-{ambos_datos['total_alumnos'].max()}")
        
        # 2. Analizar datos en tabla matriculas_siagie
        print("\n2. ANÁLISIS TABLA MATRICULAS_SIAGIE")
        query_siagie = """
        SELECT 
            codigo_modular_norm as codigo_modular,
            anio,
            COUNT(*) as registros_matricula,
            SUM(total_alumnos_norm) as total_matriculados
        FROM matriculas_siagie 
        WHERE anio = 2024
        GROUP BY codigo_modular_norm
        """
        
        df_siagie = pd.read_sql_query(query_siagie, conn)
        print(f"   - Instituciones con datos SIAGIE 2024: {len(df_siagie)}")
        
        if len(df_siagie) > 0:
            print(f"   - Matriculados promedio: {df_siagie['total_matriculados'].mean():.1f}")
            print(f"   - Matriculados rango: {df_siagie['total_matriculados'].min()}-{df_siagie['total_matriculados'].max()}")
        
        # 3. Cruce entre ambas fuentes
        print("\n3. CRUCE ENTRE FUENTES DE DATOS")
        
        # Convertir ambos códigos a string para el merge
        df_ie['codigo_modular_str'] = df_ie['codigo_modular'].astype(str)
        df_siagie['codigo_modular_str'] = df_siagie['codigo_modular'].astype(str)
        
        # Merge de ambas tablas
        df_cruce = df_ie.merge(df_siagie, left_on='codigo_modular_str', right_on='codigo_modular_str', 
                               how='outer', suffixes=('_ie', '_siagie'))
        
        # Instituciones que aparecen en ambas fuentes  
        en_ambas = df_cruce[(df_cruce['codigo_modular_ie'].notna()) & (df_cruce['codigo_modular_siagie'].notna())]
        print(f"   - Instituciones en AMBAS fuentes: {len(en_ambas)}")
        
        # De las que están en ambas, ¿cuántas tienen datos completos para RED?
        completas_ie = en_ambas[(en_ambas['total_docentes'].notna()) & (en_ambas['total_alumnos'].notna())]
        completas_siagie = en_ambas[(en_ambas['total_docentes'].notna()) & (en_ambas['total_matriculados'].notna())]
        
        print(f"   - Con datos completos IE: {len(completas_ie)}")
        print(f"   - Con datos completos SIAGIE: {len(completas_siagie)}")
        
        # 4. Comparación de totales (donde ambos están disponibles)
        print("\n4. COMPARACIÓN TOTALES ALUMNOS")
        
        comparables = en_ambas[(en_ambas['total_alumnos'].notna()) & (en_ambas['total_matriculados'].notna())]
        
        if len(comparables) > 0:
            print(f"   - Instituciones comparables: {len(comparables)}")
            
            comparables['diferencia_abs'] = abs(comparables['total_alumnos'] - comparables['total_matriculados'])
            comparables['diferencia_rel'] = (comparables['diferencia_abs'] / comparables['total_alumnos']) * 100
            
            print(f"   - Diferencia promedio absoluta: {comparables['diferencia_abs'].mean():.1f} estudiantes")
            print(f"   - Diferencia promedio relativa: {comparables['diferencia_rel'].mean():.1f}%")
            
            # Mostrar algunas comparaciones
            print(f"\n   MUESTRA DE COMPARACIONES:")
            muestra = comparables[['codigo_modular_ie', 'nombre_institucion', 'total_alumnos', 'total_matriculados', 'diferencia_abs', 'diferencia_rel']].head(10)
            for idx, row in muestra.iterrows():
                print(f"   {row['codigo_modular_ie']}: IE={row['total_alumnos']} vs SIAGIE={row['total_matriculados']} (diff: {row['diferencia_abs']:.0f}, {row['diferencia_rel']:.1f}%)")
        
        # 5. Recomendación
        print(f"\n=== RECOMENDACIÓN ===")
        
        if len(completas_ie) >= len(completas_siagie):
            print(f"MÉTODO RECOMENDADO: Tabla instituciones_educativas")
            print(f"- Cobertura: {len(completas_ie)} instituciones ({(len(completas_ie)/len(df_ie))*100:.1f}%)")
            print(f"- Ventaja: Datos directos total_docentes y total_alumnos")
        else:
            print(f"MÉTODO RECOMENDADO: Tabla matriculas_siagie + buscar docentes")
            print(f"- Cobertura potencial: {len(completas_siagie)} instituciones")
            print(f"- Ventaja: Datos más actualizados (2024)")
        
    except Exception as e:
        print(f"Error en el análisis: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()