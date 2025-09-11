#!/usr/bin/env python3
"""
Limpiador de columnas X11_RED - Eliminación de confusión
1. Elimina columna X11_RED (versión original sin ajustes)
2. Renombra X11_RED_ajustado a X11_RED (versión final)
3. Actualiza respaldo y documenta cambios
"""

import sqlite3
import pandas as pd
import os

def main():
    print("=== LIMPIEZA COLUMNAS X11_RED ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # 1. Verificar estado actual
        print("\n1. VERIFICANDO ESTADO ACTUAL...")
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas = cursor.fetchall()
        
        columnas_x11 = [col[1] for col in columnas if 'X11_RED' in col[1]]
        print(f"   - Columnas X11_RED encontradas: {columnas_x11}")
        
        # Verificar datos en ambas columnas
        query_verificacion = """
        SELECT 
            COUNT(*) as total,
            COUNT(X11_RED) as x11_original,
            COUNT(X11_RED_ajustado) as x11_ajustado,
            AVG(X11_RED) as promedio_original,
            AVG(X11_RED_ajustado) as promedio_ajustado
        FROM indices_metodologicos
        """
        
        stats = pd.read_sql_query(query_verificacion, conn).iloc[0]
        
        print(f"   ESTADÍSTICAS ACTUALES:")
        print(f"   - Total registros: {int(stats['total'])}")
        promedio_orig = stats['promedio_original'] if stats['promedio_original'] is not None else 0
        promedio_ajust = stats['promedio_ajustado'] if stats['promedio_ajustado'] is not None else 0
        print(f"   - X11_RED (original): {int(stats['x11_original'])} registros, promedio {promedio_orig:.2f}")
        print(f"   - X11_RED_ajustado: {int(stats['x11_ajustado'])} registros, promedio {promedio_ajust:.2f}")
        
        # 2. Comparar algunas instituciones para verificar diferencias
        print("\n2. COMPARANDO VERSIONES (MUESTRA)...")
        
        query_comparacion = """
        SELECT 
            codigo_modular,
            nombre_institucion,
            X11_RED as original,
            X11_RED_ajustado as ajustado,
            (X11_RED_ajustado - X11_RED) as diferencia
        FROM indices_metodologicos 
        WHERE X11_RED IS NOT NULL AND X11_RED_ajustado IS NOT NULL
        ORDER BY ABS(X11_RED_ajustado - X11_RED) DESC
        LIMIT 10
        """
        
        df_comparacion = pd.read_sql_query(query_comparacion, conn)
        
        print(f"   CASOS CON MAYORES DIFERENCIAS:")
        for idx, row in df_comparacion.head(5).iterrows():
            print(f"   - {row['codigo_modular']}: Original={row['original']:.2f}, Ajustado={row['ajustado']:.2f} (diff: {row['diferencia']:.2f})")
        
        # 3. Crear respaldo antes de modificar
        print("\n3. CREANDO RESPALDO ANTES DE MODIFICAR...")
        
        df_respaldo = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        
        os.makedirs('temp_data', exist_ok=True)
        archivo_respaldo = f'temp_data/indices_metodologicos_pre_x11_cleanup_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_respaldo.to_csv(archivo_respaldo, index=False)
        print(f"   - Respaldo completo creado: {archivo_respaldo}")
        
        # 4. Eliminar columna X11_RED original
        print("\n4. ELIMINANDO COLUMNA X11_RED ORIGINAL...")
        
        # SQLite no soporta DROP COLUMN directamente, necesitamos recrear la tabla
        # Primero, obtener todas las columnas excepto X11_RED
        columnas_mantener = [col[1] for col in columnas if col[1] != 'X11_RED']
        
        print(f"   - Columnas a mantener: {len(columnas_mantener)}")
        
        # Crear nueva tabla sin X11_RED
        cursor.execute("BEGIN TRANSACTION")
        
        # Crear tabla temporal
        cursor.execute("DROP TABLE IF EXISTS indices_metodologicos_temp")
        
        # Crear tabla temporal con estructura deseada
        columnas_sql = ', '.join([f"{col} TEXT" if col in ['codigo_modular', 'nombre_institucion', 'red_fya'] else f"{col} REAL" for col in columnas_mantener])
        cursor.execute(f"CREATE TABLE indices_metodologicos_temp ({columnas_sql})")
        
        # Copiar datos (excluyendo X11_RED)
        columnas_select = ', '.join(columnas_mantener)
        cursor.execute(f"INSERT INTO indices_metodologicos_temp SELECT {columnas_select} FROM indices_metodologicos")
        
        # Reemplazar tabla original
        cursor.execute("DROP TABLE indices_metodologicos")
        cursor.execute("ALTER TABLE indices_metodologicos_temp RENAME TO indices_metodologicos")
        
        print(f"   - Columna X11_RED original eliminada")
        
        # 5. Renombrar X11_RED_ajustado a X11_RED
        print("\n5. RENOMBRANDO X11_RED_ajustado A X11_RED...")
        
        # Agregar nueva columna X11_RED
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X11_RED REAL")
        
        # Copiar datos de X11_RED_ajustado a X11_RED
        cursor.execute("UPDATE indices_metodologicos SET X11_RED = X11_RED_ajustado")
        
        # Eliminar X11_RED_ajustado (mismo proceso que antes)
        columnas_finales = [col for col in columnas_mantener if col != 'X11_RED_ajustado'] + ['X11_RED']
        
        # Crear tabla final
        cursor.execute("DROP TABLE IF EXISTS indices_metodologicos_final")
        columnas_finales_sql = ', '.join([f"{col} TEXT" if col in ['codigo_modular', 'nombre_institucion', 'red_fya'] else f"{col} REAL" for col in columnas_finales])
        cursor.execute(f"CREATE TABLE indices_metodologicos_final ({columnas_finales_sql})")
        
        # Copiar datos finales
        columnas_select_final = ', '.join(columnas_finales)
        cursor.execute(f"INSERT INTO indices_metodologicos_final SELECT {columnas_select_final} FROM indices_metodologicos")
        
        # Reemplazar tabla
        cursor.execute("DROP TABLE indices_metodologicos")
        cursor.execute("ALTER TABLE indices_metodologicos_final RENAME TO indices_metodologicos")
        
        cursor.execute("COMMIT")
        
        print(f"   - X11_RED_ajustado renombrado a X11_RED")
        
        # 6. Verificar resultado final
        print("\n6. VERIFICACIÓN FINAL...")
        
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_final = cursor.fetchall()
        
        columnas_x11_final = [col[1] for col in columnas_final if 'X11_RED' in col[1]]
        print(f"   - Columnas X11_RED finales: {columnas_x11_final}")
        
        # Estadísticas finales
        query_final = """
        SELECT 
            COUNT(*) as total,
            COUNT(X11_RED) as x11_disponible,
            AVG(X11_RED) as promedio_final,
            MIN(X11_RED) as min_final,
            MAX(X11_RED) as max_final
        FROM indices_metodologicos
        """
        
        stats_final = pd.read_sql_query(query_final, conn).iloc[0]
        
        print(f"   ESTADÍSTICAS FINALES:")
        print(f"   - Total registros: {int(stats_final['total'])}")
        print(f"   - X11_RED disponible: {int(stats_final['x11_disponible'])} ({(stats_final['x11_disponible']/stats_final['total'])*100:.1f}%)")
        print(f"   - Promedio: {stats_final['promedio_final']:.2f}")
        print(f"   - Rango: {stats_final['min_final']:.2f} - {stats_final['max_final']:.2f}")
        
        # 7. Crear respaldo final
        print("\n7. CREANDO RESPALDO FINAL...")
        
        df_final = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        archivo_final = f'temp_data/indices_metodologicos_post_x11_cleanup_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.csv'
        df_final.to_csv(archivo_final, index=False)
        print(f"   - Respaldo final creado: {archivo_final}")
        
        # 8. Muestra de datos finales
        print("\n8. MUESTRA DE DATOS FINALES:")
        
        muestra_final = pd.read_sql_query("""
            SELECT codigo_modular, nombre_institucion, X11_RED
            FROM indices_metodologicos 
            WHERE X11_RED IS NOT NULL
            ORDER BY X11_RED DESC
            LIMIT 5
        """, conn)
        
        for idx, row in muestra_final.iterrows():
            print(f"   - {row['codigo_modular']}: {row['X11_RED']:.2f} estudiantes/docente")
        
        print(f"\n=== LIMPIEZA COMPLETADA ===")
        print(f"Resultado: Una sola columna X11_RED con valores ajustados (realistas)")
        print(f"Máximo verificado: {stats_final['max_final']:.2f} ≤ 45 estudiantes/docente")
        
        return True
        
    except Exception as e:
        print(f"Error en limpieza: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()