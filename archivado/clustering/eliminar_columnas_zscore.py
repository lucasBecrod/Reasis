#!/usr/bin/env python3
"""
Eliminar columnas ZSCORE innecesarias de la tabla indices_metodologicos
"""

import sqlite3
import pandas as pd

def crear_respaldo_tabla():
    """Crear respaldo de la tabla antes de modificar"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== CREANDO RESPALDO DE SEGURIDAD ===")
    
    # Crear tabla de respaldo
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indices_metodologicos_backup AS 
        SELECT * FROM indices_metodologicos
    """)
    
    # Verificar respaldo
    df_backup = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos_backup", conn)
    print(f"[OK] Respaldo creado: {df_backup['total'].iloc[0]} registros")
    
    conn.commit()
    conn.close()

def eliminar_columnas_zscore():
    """Eliminar columnas ZSCORE de la tabla indices_metodologicos"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== ELIMINANDO COLUMNAS ZSCORE ===")
    
    # Lista de columnas ZSCORE a eliminar
    columnas_zscore = [
        'Y1_ILA_ZSCORE', 'Y2_TD_ZSCORE', 'Y3_PR_ZSCORE',
        'X1_NVC_ZSCORE', 'X4_IDD_ZSCORE', 'X5_ED_ZSCORE', 
        'X6_CDD_ZSCORE', 'X10_IE_ZSCORE', 'X11_RED_ZSCORE'
    ]
    
    # En SQLite necesitamos recrear la tabla sin las columnas ZSCORE
    print("Creando nueva tabla sin columnas ZSCORE...")
    
    # Obtener columnas actuales
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columnas_actuales = cursor.fetchall()
    
    # Filtrar columnas (mantener solo las que NO son ZSCORE)
    columnas_mantener = []
    for col in columnas_actuales:
        nombre_col = col[1]
        tipo_col = col[2]
        if 'ZSCORE' not in nombre_col:
            columnas_mantener.append(f"{nombre_col} {tipo_col}")
    
    print(f"Columnas a mantener: {len(columnas_mantener)}")
    print(f"Columnas a eliminar: {len(columnas_zscore)}")
    
    # Crear nueva tabla temporal
    estructura_nueva = ", ".join(columnas_mantener)
    cursor.execute(f"""
        CREATE TABLE indices_metodologicos_nuevo (
            {estructura_nueva}
        )
    """)
    
    # Copiar datos (solo columnas que NO son ZSCORE)
    columnas_nombres = [col.split()[0] for col in columnas_mantener]
    columnas_select = ", ".join(columnas_nombres)
    
    cursor.execute(f"""
        INSERT INTO indices_metodologicos_nuevo ({columnas_select})
        SELECT {columnas_select} FROM indices_metodologicos
    """)
    
    # Eliminar tabla original y renombrar la nueva
    cursor.execute("DROP TABLE indices_metodologicos")
    cursor.execute("ALTER TABLE indices_metodologicos_nuevo RENAME TO indices_metodologicos")
    
    conn.commit()
    print("[OK] Columnas ZSCORE eliminadas exitosamente")
    
    conn.close()

def verificar_estructura_final():
    """Verificar la estructura final de la tabla"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== VERIFICACION ESTRUCTURA FINAL ===")
    
    # Verificar estructura actual
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columnas_finales = cursor.fetchall()
    
    print(f"Total columnas finales: {len(columnas_finales)}")
    
    # Verificar que no hay columnas ZSCORE
    columnas_zscore_restantes = [col[1] for col in columnas_finales if 'ZSCORE' in col[1]]
    
    if len(columnas_zscore_restantes) == 0:
        print("[EXITO] No hay columnas ZSCORE restantes")
    else:
        print(f"[PROBLEMA] Columnas ZSCORE restantes: {columnas_zscore_restantes}")
    
    # Mostrar estructura final
    print("\nEstructura final de la tabla:")
    for i, col in enumerate(columnas_finales, 1):
        print(f"{i:2d}. {col[1]} ({col[2]})")
    
    # Verificar datos
    df_datos = pd.read_sql_query("SELECT COUNT(*) as total FROM indices_metodologicos", conn)
    print(f"\nDatos preservados: {df_datos['total'].iloc[0]} registros")
    
    conn.close()

def main():
    """Función principal"""
    
    print("ELIMINAR COLUMNAS ZSCORE DE indices_metodologicos")
    print("=" * 55)
    print("Objetivo: Limpiar tabla eliminando 9 columnas ZSCORE innecesarias")
    
    try:
        # 1. Crear respaldo de seguridad
        crear_respaldo_tabla()
        
        # 2. Eliminar columnas ZSCORE
        eliminar_columnas_zscore()
        
        # 3. Verificar estructura final
        verificar_estructura_final()
        
        print("\n" + "=" * 55)
        print("[COMPLETADO] Columnas ZSCORE eliminadas exitosamente")
        print("[OPTIMIZADO] Tabla indices_metodologicos limpia y optimizada")
        print("[RESPALDO] Datos originales guardados en indices_metodologicos_backup")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("[SOLUCION] Restaurar desde indices_metodologicos_backup si es necesario")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()