"""
Script para aplicar X2_TR calculado a la tabla indices_metodologicos

Autor: Proyecto Reasis  
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x2_tr_a_indices():
    """
    Aplica los valores X2_TR calculados a la tabla indices_metodologicos
    """
    
    print("=== APLICANDO X2_TR A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Cargar datos X2_TR desde CSV
    csv_path = "temp_data/x2_tr_preliminar_20250810_012649.csv"
    print(f"1. CARGANDO DATOS DESDE: {csv_path}")
    
    try:
        df_x2_tr = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_x2_tr)}")
        print(f"   Columnas: {list(df_x2_tr.columns)}")
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado: {csv_path}")
        return False
    
    # 2. Verificar estado actual tabla indices_metodologicos
    print("\n2. VERIFICANDO TABLA INDICES_METODOLOGICOS:")
    
    # Verificar si columna X2_TR ya existe
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X2_TR' not in columnas:
        print("   Agregando columna X2_TR...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X2_TR INTEGER")
        conn.commit()
    else:
        print("   Columna X2_TR ya existe")
    
    # 3. Actualizar valores X2_TR
    print("\n3. ACTUALIZANDO VALORES X2_TR:")
    print("   Convirtiendo códigos modulares a formato string con ceros...")
    
    filas_actualizadas = 0
    for _, row in df_x2_tr.iterrows():
        # Convertir código a string con formato correcto (7 dígitos con ceros)
        codigo_str = str(int(row['codigo_modular'])).zfill(7)
        
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET X2_TR = ? 
            WHERE CODIGO_MODULAR = ?
        """, (int(row['X2_TR']), codigo_str))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificar resultado final
    print("\n4. VERIFICANDO RESULTADO:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total, 
               COUNT(X2_TR) con_x2_tr,
               COUNT(*) - COUNT(X2_TR) sin_x2_tr
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X2_TR: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X2_TR: {result[2]}")
    
    # Distribución por categoría
    print("\n   Distribución X2_TR:")
    for row in cursor.execute("SELECT X2_TR, COUNT(*) FROM indices_metodologicos WHERE X2_TR IS NOT NULL GROUP BY X2_TR ORDER BY X2_TR"):
        categoria = "Urbano" if row[0] == 1 else "Rural" if row[0] == 2 else f"Categoria_{row[0]}"
        print(f"     X2_TR={row[0]} ({categoria}): {row[1]} instituciones")
    
    # 5. Crear respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_x2_tr_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n5. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Resultado
    exito = result[2] == 0  # Sin X2_TR debe ser 0
    print(f"\n[{'OK' if exito else 'ERROR'}] X2_TR {'APLICADO EXITOSAMENTE' if exito else 'APLICACION INCOMPLETA'}")
    
    return exito

if __name__ == "__main__":
    success = aplicar_x2_tr_a_indices()
    if success:
        print("\n[EXITO] Variable X2_TR integrada completamente")
        print("[INFO] Completitud: 5 -> 6 variables metodologicas")
    else:
        print("\n[ERROR] Error en aplicacion de X2_TR")