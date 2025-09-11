"""
Script para aplicar X5_ED expandido a indices_metodologicos
Usa datos de múltiples fuentes consolidados

Autor: Proyecto Reasis  
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x5_ed_expandido():
    """
    Aplica X5_ED expandido desde CSV consolidado
    """
    
    print("=== APLICANDO X5_ED EXPANDIDO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos expandidos
    csv_path = "temp_data/x5_ed_expandido_20250810_014240.csv"
    print(f"1. CARGANDO DATOS EXPANDIDOS: {csv_path}")
    
    try:
        df_x5ed = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_x5ed)}")
        
        # Mostrar distribución por fuente
        print(f"   Distribución por fuente:")
        for fuente, count in df_x5ed['fuente'].value_counts().items():
            print(f"     {fuente}: {count}")
            
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/agregar columna X5_ED
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X5_ED' not in columnas:
        print("\n2. AGREGANDO COLUMNA X5_ED...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X5_ED REAL")
        conn.commit()
    else:
        print("\n2. COLUMNA X5_ED YA EXISTE - ACTUALIZANDO...")
    
    # 3. Actualizar valores X5_ED
    print("\n3. ACTUALIZANDO VALORES X5_ED:")
    
    filas_actualizadas = 0
    for _, row in df_x5ed.iterrows():
        # Convertir código a formato correcto (7 dígitos)
        codigo_str = str(int(row['codigo_modular'])).zfill(7)
        
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET X5_ED = ? 
            WHERE CODIGO_MODULAR = ?
        """, (float(row['X5_ED']), codigo_str))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificar resultado final
    print("\n4. VERIFICANDO RESULTADO:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X5_ED) con_x5_ed,
               COUNT(*) - COUNT(X5_ED) sin_x5_ed
        FROM indices_metodologicos
    """).fetchone()
    
    cobertura_pct = result[1]/result[0]*100
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X5_ED: {result[1]} ({cobertura_pct:.1f}%)")
    print(f"   Sin X5_ED: {result[2]}")
    
    # 5. Estadísticas X5_ED
    if result[1] > 0:
        print("\n5. ESTADISTICAS X5_ED:")
        stats = cursor.execute("""
            SELECT 
                MIN(X5_ED) as minimo,
                MAX(X5_ED) as maximo,
                AVG(X5_ED) as promedio,
                COUNT(X5_ED) as total_con_datos
            FROM indices_metodologicos 
            WHERE X5_ED IS NOT NULL
        """).fetchone()
        
        print(f"   Minimo: {stats[0]:.3f}")
        print(f"   Maximo: {stats[1]:.3f}")
        print(f"   Promedio: {stats[2]:.3f}")
        
        # Distribución por rangos
        print(f"\n   Distribución por rangos:")
        rangos = cursor.execute("""
            SELECT 
                CASE 
                    WHEN X5_ED < 0.3 THEN 'Baja (0-0.3)'
                    WHEN X5_ED < 0.7 THEN 'Media (0.3-0.7)'
                    ELSE 'Alta (0.7-1.0)'
                END as rango,
                COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X5_ED IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN X5_ED < 0.3 THEN 'Baja (0-0.3)'
                    WHEN X5_ED < 0.7 THEN 'Media (0.3-0.7)'
                    ELSE 'Alta (0.7-1.0)'
                END
            ORDER BY cantidad DESC
        """).fetchall()
        
        for rango, cantidad in rangos:
            porcentaje = cantidad/stats[3]*100
            print(f"     {rango}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 6. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_x5_ed_expandido_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n6. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito = cobertura_pct >= 90  # 90% o más
    parcial = cobertura_pct >= 50  # Entre 50-90%
    
    if exito:
        status = "EXITO"
    elif parcial:
        status = "PARCIAL"
    else:
        status = "LIMITADO"
    
    print(f"\n[{status}] X5_ED EXPANDIDO IMPLEMENTADO")
    print(f"[INFO] Cobertura final: {result[1]}/{result[0]} ({cobertura_pct:.1f}%)")
    
    return result[1], result[0], cobertura_pct

if __name__ == "__main__":
    con_x5ed, total, cobertura = aplicar_x5_ed_expandido()
    print(f"\n[RESULTADO FINAL] X5_ED: {con_x5ed}/{total} instituciones ({cobertura:.1f}%)")
    
    if cobertura >= 90:
        print("[EXCELENTE] Cobertura alta - Variable lista para clustering")
    elif cobertura >= 50:
        print("[BUENO] Cobertura media - Variable viable con imputacion complementaria") 
    else:
        print("[MEJORABLE] Cobertura baja - Considerar alternativas")