#!/usr/bin/env python3
"""
Script para agregar poblacion_proyectada_2020_distrito como X25_POBLACION_DISTRITO
"""

import sqlite3
import pandas as pd

def agregar_poblacion_2020():
    """
    Agrega población proyectada 2020 como variable contextual
    """
    
    print("=== AGREGANDO POBLACION PROYECTADA 2020 ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar variable poblacion_proyectada_2020_distrito
    print("1. ANALIZANDO POBLACION PROYECTADA 2020:")
    
    df_poblacion = pd.read_sql_query("""
    SELECT codigo_modular, poblacion_proyectada_2020_distrito
    FROM instituciones_educativas
    WHERE poblacion_proyectada_2020_distrito IS NOT NULL
    """, conn)
    
    print(f"   Registros con datos: {len(df_poblacion)}")
    
    if len(df_poblacion) > 0:
        # Estadísticas
        poblacion_stats = df_poblacion['poblacion_proyectada_2020_distrito'].describe()
        print(f"   Estadísticas población 2020:")
        print(f"     Min: {poblacion_stats['min']:,.0f} habitantes")
        print(f"     Max: {poblacion_stats['max']:,.0f} habitantes")
        print(f"     Media: {poblacion_stats['mean']:,.0f} habitantes")
        print(f"     Mediana: {poblacion_stats['50%']:,.0f} habitantes")
        
        # Distribución por rangos
        bins = [0, 10000, 50000, 100000, 500000, float('inf')]
        labels = ['<10K', '10-50K', '50-100K', '100-500K', '>500K']
        df_poblacion['rango'] = pd.cut(df_poblacion['poblacion_proyectada_2020_distrito'], bins=bins, labels=labels)
        distribucion = df_poblacion['rango'].value_counts()
        
        print(f"   Distribución por rangos:")
        for rango, count in distribucion.items():
            print(f"     {rango}: {count} instituciones ({count/len(df_poblacion)*100:.1f}%)")
        
        # 2. Agregar columna
        print(f"\n2. AGREGANDO COLUMNA X25_POBLACION_DISTRITO:")
        
        try:
            cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X25_POBLACION_DISTRITO REAL")
            print(f"   [OK] Columna X25_POBLACION_DISTRITO agregada")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e).lower():
                print(f"   [EXISTE] Columna X25_POBLACION_DISTRITO ya existe")
            else:
                print(f"   [ERROR] No se pudo agregar columna: {str(e)}")
        
        # 3. Actualizar valores
        print(f"\n3. ACTUALIZANDO VALORES:")
        
        actualizaciones_exitosas = 0
        actualizaciones_fallidas = 0
        
        for _, row in df_poblacion.iterrows():
            codigo = row['codigo_modular']
            poblacion = row['poblacion_proyectada_2020_distrito']
            
            try:
                cursor.execute("""
                UPDATE indices_metodologicos 
                SET X25_POBLACION_DISTRITO = ?
                WHERE CODIGO_MODULAR = ?
                """, (float(poblacion), codigo))
                actualizaciones_exitosas += 1
            except sqlite3.Error as e:
                actualizaciones_fallidas += 1
                if actualizaciones_fallidas <= 3:
                    print(f"   [ERROR] {codigo}: {str(e)}")
        
        print(f"   [RESULTADO] {actualizaciones_exitosas} actualizaciones exitosas")
        print(f"   [RESULTADO] {actualizaciones_fallidas} actualizaciones fallidas")
        
        # 4. Verificar resultado
        print(f"\n4. VERIFICACION FINAL:")
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(X25_POBLACION_DISTRITO) as con_datos,
            COUNT(*) - COUNT(X25_POBLACION_DISTRITO) as nulls
        FROM indices_metodologicos
        """)
        stats = cursor.fetchone()
        completitud = (stats[1] / stats[0]) * 100 if stats[0] > 0 else 0
        
        print(f"   X25_POBLACION_DISTRITO:")
        print(f"     Total registros: {stats[0]}")
        print(f"     Con datos: {stats[1]}")
        print(f"     NULLs: {stats[2]}")
        print(f"     Completitud: {completitud:.1f}%")
        
        # Estadísticas de la variable integrada
        if stats[1] > 0:
            cursor.execute("""
            SELECT 
                MIN(X25_POBLACION_DISTRITO) as min_val,
                MAX(X25_POBLACION_DISTRITO) as max_val,
                AVG(X25_POBLACION_DISTRITO) as mean_val
            FROM indices_metodologicos
            WHERE X25_POBLACION_DISTRITO IS NOT NULL
            """)
            final_stats = cursor.fetchone()
            
            print(f"   Estadísticas finales:")
            print(f"     Min: {final_stats[0]:,.0f} hab")
            print(f"     Max: {final_stats[1]:,.0f} hab")
            print(f"     Media: {final_stats[2]:,.0f} hab")
    
    else:
        print(f"   [ERROR] No hay datos válidos de población 2020")
    
    # Commit cambios
    conn.commit()
    conn.close()
    
    print(f"\n[EXITO] Población proyectada 2020 agregada como X25_POBLACION_DISTRITO")
    return True

if __name__ == "__main__":
    resultado = agregar_poblacion_2020()
    
    if resultado:
        print(f"\n=== POBLACION AGREGADA EXITOSAMENTE ===")
        print(f"X25_POBLACION_DISTRITO: Población Proyectada 2020 Distrito")
        print(f"Variable contextual demográfica lista para clustering")
    else:
        print(f"\n=== PROBLEMA CON POBLACION ===")
        print(f"Revisar disponibilidad de datos")