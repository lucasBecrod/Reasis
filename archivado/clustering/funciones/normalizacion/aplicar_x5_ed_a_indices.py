"""
Script para aplicar X5_ED - Estabilidad Docente a indices_metodologicos
Integra datos desde tabla x5_ed_estabilidad_docente existente

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x5_ed_a_indices():
    """
    Aplica X5_ED desde tabla x5_ed_estabilidad_docente
    usando ratio_nombrados como medida de estabilidad
    """
    
    print("=== APLICANDO X5_ED A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Verificar/agregar columna X5_ED
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X5_ED' not in columnas:
        print("1. AGREGANDO COLUMNA X5_ED...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X5_ED REAL")
        conn.commit()
    else:
        print("1. COLUMNA X5_ED YA EXISTE")
    
    # 2. Actualizar X5_ED usando JOIN con x5_ed_estabilidad_docente
    print("\n2. ACTUALIZANDO X5_ED DESDE TABLA EXISTENTE:")
    
    cursor.execute("""
        UPDATE indices_metodologicos 
        SET X5_ED = (
            SELECT ratio_nombrados 
            FROM x5_ed_estabilidad_docente 
            WHERE codigo_modular = indices_metodologicos.CODIGO_MODULAR
        )
        WHERE CODIGO_MODULAR IN (
            SELECT codigo_modular FROM x5_ed_estabilidad_docente
        )
    """)
    
    filas_actualizadas = cursor.rowcount
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 3. Verificar resultado
    print("\n3. VERIFICANDO RESULTADO:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X5_ED) con_x5_ed,
               COUNT(*) - COUNT(X5_ED) sin_x5_ed
        FROM indices_metodologicos
    """).fetchone()
    
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X5_ED: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Sin X5_ED: {result[2]}")
    
    # 4. Estadísticas X5_ED
    print("\n4. ESTADISTICAS X5_ED:")
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
    print(f"   Instituciones con datos: {stats[3]}")
    
    # 5. Distribución por rangos
    print("\n5. DISTRIBUCION POR RANGOS DE ESTABILIDAD:")
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
        print(f"   {rango}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 6. Verificar coincidencias con tabla fuente
    print("\n6. VERIFICACION CRUZADA:")
    verificacion = cursor.execute("""
        SELECT COUNT(*) as coincidencias_perfectas
        FROM indices_metodologicos im
        JOIN x5_ed_estabilidad_docente x5 ON im.CODIGO_MODULAR = x5.codigo_modular
        WHERE im.X5_ED = x5.ratio_nombrados
    """).fetchone()
    
    print(f"   Coincidencias perfectas: {verificacion[0]}/{result[1]}")
    
    # 7. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_x5_ed_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n7. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    porcentaje_cobertura = result[1]/result[0]*100
    exito_parcial = porcentaje_cobertura >= 30  # Al menos 30% de cobertura
    
    print(f"\n[{'PARCIAL' if exito_parcial else 'LIMITADO'}] X5_ED IMPLEMENTADO")
    print(f"[INFO] Cobertura: {result[1]}/{result[0]} instituciones ({porcentaje_cobertura:.1f}%)")
    
    return result[1], result[0], porcentaje_cobertura

if __name__ == "__main__":
    con_x5ed, total, cobertura = aplicar_x5_ed_a_indices()
    print(f"\n[RESULTADO] X5_ED: {con_x5ed}/{total} instituciones ({cobertura:.1f}% cobertura)")
    if cobertura >= 30:
        print("[EXITO] Variable X5_ED integrada exitosamente")
        print("[INFO] Datos disponibles para clustering con imputacion posterior")
    else:
        print("[ALERTA] Cobertura baja, evaluar alternativas")