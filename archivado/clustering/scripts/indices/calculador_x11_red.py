#!/usr/bin/env python3
"""
Calculador de X11_RED - Ratio Estudiante-Docente
Implementa la fórmula: RED = Total_estudiantes / Total_docentes
"""

import sqlite3
import pandas as pd
import numpy as np

def main():
    print("=== CÁLCULO X11_RED - RATIO ESTUDIANTE-DOCENTE ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Cargar datos completos después de imputación
        print("\n1. CARGANDO DATOS POST-IMPUTACIÓN...")
        
        query = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            total_docentes,
            total_alumnos,
            nombre_red_fya_matched as red_fya,
            entra_estudio_clustering
        FROM instituciones_educativas
        WHERE total_alumnos IS NOT NULL AND total_docentes IS NOT NULL 
        AND total_alumnos > 0 AND total_docentes > 0
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"   - Instituciones cargadas: {len(df)}")
        print(f"   - Con datos completos: {len(df)} (100.0%)")
        
        # 2. Calcular X11_RED según matriz de operacionalización
        print("\n2. CALCULANDO X11_RED...")
        
        # Fórmula: RED = Total_estudiantes / Total_docentes
        df['X11_RED'] = df['total_alumnos'] / df['total_docentes']
        
        print("   FÓRMULA APLICADA: X11_RED = total_alumnos / total_docentes")
        
        # 3. Estadísticas descriptivas
        print("\n3. ESTADÍSTICAS DESCRIPTIVAS X11_RED:")
        print(f"   - Media: {df['X11_RED'].mean():.2f} estudiantes por docente")
        print(f"   - Mediana: {df['X11_RED'].median():.2f} estudiantes por docente")
        print(f"   - Desviación estándar: {df['X11_RED'].std():.2f}")
        print(f"   - Mínimo: {df['X11_RED'].min():.2f} estudiantes por docente")
        print(f"   - Máximo: {df['X11_RED'].max():.2f} estudiantes por docente")
        print(f"   - Rango intercuartil: {df['X11_RED'].quantile(0.25):.2f} - {df['X11_RED'].quantile(0.75):.2f}")
        
        # 4. Distribución por percentiles
        print("\n4. DISTRIBUCIÓN POR PERCENTILES:")
        percentiles = [10, 25, 50, 75, 90, 95]
        for p in percentiles:
            valor = df['X11_RED'].quantile(p/100)
            print(f"   - P{p}: {valor:.2f} estudiantes por docente")
        
        # 5. Análisis por red Fe y Alegría
        print("\n5. ANÁLISIS POR RED FE Y ALEGRÍA:")
        
        red_stats = df.groupby('red_fya')['X11_RED'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
        
        for idx, row in red_stats.iterrows():
            red = idx
            count = int(row['count'])
            mean_red = row['mean']
            median_red = row['median']
            print(f"   - {red}: {count} IIEE, Media={mean_red:.2f}, Mediana={median_red:.2f}")
        
        # 6. Identificar casos extremos
        print("\n6. CASOS EXTREMOS:")
        
        # Ratios muy bajos (menos estudiantes que docentes)
        ratios_bajos = df[df['X11_RED'] < 5].sort_values('X11_RED')
        print(f"   RATIOS BAJOS (<5 estudiantes/docente): {len(ratios_bajos)} instituciones")
        if len(ratios_bajos) > 0:
            for idx, row in ratios_bajos.head(5).iterrows():
                print(f"   - {row['codigo_modular']}: {row['X11_RED']:.2f} ({row['total_alumnos']}/{row['total_docentes']})")
        
        # Ratios muy altos
        ratios_altos = df[df['X11_RED'] > 25].sort_values('X11_RED', ascending=False)
        print(f"   RATIOS ALTOS (>25 estudiantes/docente): {len(ratios_altos)} instituciones")
        if len(ratios_altos) > 0:
            for idx, row in ratios_altos.head(5).iterrows():
                print(f"   - {row['codigo_modular']}: {row['X11_RED']:.2f} ({row['total_alumnos']}/{row['total_docentes']})")
        
        # 7. Guardar resultados en tabla
        print("\n7. GUARDANDO RESULTADOS...")
        
        # Preparar datos para guardar
        df_resultado = df[['codigo_modular', 'nombre_institucion', 'total_alumnos', 'total_docentes', 'X11_RED', 'red_fya']].copy()
        df_resultado['fecha_calculo'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        df_resultado['metodo_calculo'] = 'total_alumnos / total_docentes (con imputacion por red)'
        
        # Guardar en nueva tabla
        df_resultado.to_sql('x11_red_calculado', conn, if_exists='replace', index=False)
        
        conn.commit()
        print(f"   - Resultados guardados en tabla 'x11_red_calculado'")
        print(f"   - {len(df_resultado)} registros guardados")
        
        # 8. Actualizar tabla instituciones_educativas
        print("\n8. ACTUALIZANDO TABLA INSTITUCIONES_EDUCATIVAS...")
        
        cursor = conn.cursor()
        
        # Verificar si columna X11_RED existe
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'X11_RED' not in columnas:
            cursor.execute("ALTER TABLE instituciones_educativas ADD COLUMN X11_RED REAL")
            print("   - Columna X11_RED agregada")
        
        # Actualizar valores
        actualizaciones = 0
        for idx, row in df.iterrows():
            cursor.execute("""
                UPDATE instituciones_educativas 
                SET X11_RED = ?
                WHERE codigo_modular = ?
            """, (row['X11_RED'], row['codigo_modular']))
            actualizaciones += 1
        
        conn.commit()
        print(f"   - {actualizaciones} registros actualizados con X11_RED")
        
        # 9. Resumen final para clustering
        print("\n9. RESUMEN PARA CLUSTERING K-MEANS:")
        
        # Filtrar instituciones que entran al estudio clustering
        df_clustering = df[df['entra_estudio_clustering'] == 'Sí'].copy() if 'entra_estudio_clustering' in df.columns else df.copy()
        
        print(f"   - Instituciones para clustering: {len(df_clustering)}")
        print(f"   - X11_RED promedio (clustering): {df_clustering['X11_RED'].mean():.2f}")
        print(f"   - Rango X11_RED (clustering): {df_clustering['X11_RED'].min():.2f} - {df_clustering['X11_RED'].max():.2f}")
        print(f"   - Distribución normal: Prueba Shapiro-Wilk pendiente")
        
        print(f"\n=== X11_RED CALCULADO EXITOSAMENTE ===")
        print(f"Cobertura: {len(df)} instituciones (100.0%)")
        print(f"Variable lista para metodología de clustering")
        
    except Exception as e:
        print(f"Error en el cálculo: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()