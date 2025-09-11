"""
Script para calcular X2_TR directamente desde indices_metodologicos
vinculando con instituciones_educativas

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
from datetime import datetime

def calcular_x2_tr_directo():
    """
    Calcula X2_TR directamente en indices_metodologicos
    usando JOIN con instituciones_educativas
    """
    
    print("=== CALCULANDO X2_TR DIRECTO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar si columna X2_TR existe
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X2_TR' not in columnas:
        print("1. AGREGANDO COLUMNA X2_TR...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X2_TR INTEGER")
        conn.commit()
    else:
        print("1. COLUMNA X2_TR YA EXISTE")
    
    # 2. Actualizar X2_TR con JOIN directo
    print("\n2. ACTUALIZANDO X2_TR CON JOIN DIRECTO:")
    
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X2_TR = CASE 
            WHEN (SELECT es_rural FROM instituciones_educativas 
                  WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR) = 1 THEN 2  -- Rural
            WHEN (SELECT es_rural FROM instituciones_educativas 
                  WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR) = 0 THEN 1  -- Urbano
            ELSE NULL
        END
        WHERE CODIGO_MODULAR IN (SELECT codigo_modular FROM instituciones_educativas)
    """)
    
    filas_actualizadas = cursor.rowcount
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 3. Verificar resultado
    print("\n3. VERIFICANDO RESULTADO:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X2_TR) con_x2_tr,
               COUNT(*) - COUNT(X2_TR) sin_x2_tr
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X2_TR: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X2_TR: {result[2]}")
    
    # Distribución
    print("\n   Distribución X2_TR:")
    for row in cursor.execute("SELECT X2_TR, COUNT(*) FROM indices_metodologicos WHERE X2_TR IS NOT NULL GROUP BY X2_TR ORDER BY X2_TR"):
        categoria = "Urbano" if row[0] == 1 else "Rural" if row[0] == 2 else f"Categoria_{row[0]}"
        print(f"     X2_TR={row[0]} ({categoria}): {row[1]} instituciones")
    
    # 4. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_x2_tr_directo_{timestamp}.csv"
    
    import pandas as pd
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n4. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    exito = result[2] == 0
    print(f"\n[{'OK' if exito else 'PARCIAL'}] X2_TR {'COMPLETADO' if exito else 'APLICADO PARCIALMENTE'}")
    
    return exito, result[1], result[0]

if __name__ == "__main__":
    success, con_x2tr, total = calcular_x2_tr_directo()
    print(f"\n[RESULTADO] X2_TR: {con_x2tr}/{total} instituciones")
    if success:
        print("[EXITO] Variable X2_TR implementada completamente")
    else:
        print(f"[INFO] X2_TR implementada para instituciones con coincidencia en instituciones_educativas")