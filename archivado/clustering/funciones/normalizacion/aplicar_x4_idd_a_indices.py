"""
Script para aplicar X4_IDD calculado a indices_metodologicos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x4_idd_a_indices():
    """
    Aplica X4_IDD desde CSV calculado con metodología mejorada
    """
    
    print("=== APLICANDO X4_IDD A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos calculados
    csv_path = "temp_data/x4_idd_mejorado_20250810_022523.csv"
    print(f"1. CARGANDO DATOS CALCULADOS: {csv_path}")
    
    try:
        df_x4idd = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_x4idd)}")
        
        # Distribución por fuente
        print(f"   Distribucion por fuente:")
        for fuente, count in df_x4idd['fuente'].value_counts().items():
            promedio = df_x4idd[df_x4idd['fuente'] == fuente]['X4_IDD'].mean()
            print(f"     {fuente}: {count} instituciones (IDD prom: {promedio:.1f})")
        
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/actualizar columna X4_IDD
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X4_IDD' not in columnas:
        print("\n2. AGREGANDO COLUMNA X4_IDD...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X4_IDD REAL")
        conn.commit()
    else:
        print("\n2. COLUMNA X4_IDD YA EXISTE - ACTUALIZANDO...")
    
    # 3. Aplicar valores X4_IDD
    print("\n3. ACTUALIZANDO VALORES X4_IDD:")
    
    filas_actualizadas = 0
    for _, row in df_x4idd.iterrows():
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET X4_IDD = ? 
            WHERE CODIGO_MODULAR = ?
        """, (float(row['X4_IDD']), row['codigo_target']))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificación final
    print("\n4. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X4_IDD) con_x4_idd,
               COUNT(*) - COUNT(X4_IDD) sin_x4_idd
        FROM indices_metodologicos
    """).fetchone()
    
    cobertura_pct = result[1]/result[0]*100
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X4_IDD: {result[1]} ({cobertura_pct:.1f}%)")
    print(f"   Sin X4_IDD: {result[2]}")
    
    # 5. Estadísticas descriptivas en BD
    if result[1] > 0:
        print(f"\n5. ESTADISTICAS X4_IDD EN BD:")
        
        estadisticas = cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(X4_IDD) as minimo,
                MAX(X4_IDD) as maximo,
                AVG(X4_IDD) as promedio
            FROM indices_metodologicos 
            WHERE X4_IDD IS NOT NULL
        """).fetchone()
        
        print(f"   Total registros: {estadisticas[0]}")
        print(f"   Rango: {estadisticas[1]:.1f} - {estadisticas[2]:.1f}")
        print(f"   Promedio: {estadisticas[3]:.1f}")
        
        # Distribución por cuartiles
        print(f"\n   Distribución por nivel IDD:")
        
        cuartiles = cursor.execute("""
            SELECT 
                CASE 
                    WHEN X4_IDD <= 7.5 THEN 'Bajo (0-7.5)'
                    WHEN X4_IDD <= 12.5 THEN 'Medio (7.6-12.5)'
                    WHEN X4_IDD <= 17.5 THEN 'Alto (12.6-17.5)'
                    ELSE 'Muy Alto (17.6-20)'
                END as nivel,
                COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X4_IDD IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN X4_IDD <= 7.5 THEN 'Bajo (0-7.5)'
                    WHEN X4_IDD <= 12.5 THEN 'Medio (7.6-12.5)'
                    WHEN X4_IDD <= 17.5 THEN 'Alto (12.6-17.5)'
                    ELSE 'Muy Alto (17.6-20)'
                END
            ORDER BY 
                CASE 
                    WHEN X4_IDD <= 7.5 THEN 1
                    WHEN X4_IDD <= 12.5 THEN 2
                    WHEN X4_IDD <= 17.5 THEN 3
                    ELSE 4
                END
        """).fetchall()
        
        for nivel, cantidad in cuartiles:
            porcentaje = cantidad/result[1]*100
            print(f"     {nivel}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 6. Coherencia metodológica
    print(f"\n6. COHERENCIA METODOLOGICA:")
    
    # Verificar correlación con otras variables disponibles
    correlaciones = cursor.execute("""
        SELECT 
            ROUND(
                (COUNT(*) * SUM(X4_IDD * X1_NVC) - SUM(X4_IDD) * SUM(X1_NVC)) /
                SQRT(
                    (COUNT(*) * SUM(X4_IDD * X4_IDD) - SUM(X4_IDD) * SUM(X4_IDD)) *
                    (COUNT(*) * SUM(X1_NVC * X1_NVC) - SUM(X1_NVC) * SUM(X1_NVC))
                ), 3
            ) as correlacion_x1_nvc,
            COUNT(*) as n_correlacion
        FROM indices_metodologicos 
        WHERE X4_IDD IS NOT NULL AND X1_NVC IS NOT NULL
    """).fetchone()
    
    if correlaciones[0] is not None:
        print(f"   Correlación X4_IDD vs X1_NVC: {correlaciones[0]} (n={correlaciones[1]})")
        print(f"   Interpretación: {'Negativa esperada' if correlaciones[0] < 0 else 'Positiva inesperada'} (vulnerabilidad vs desempeño)")
    
    # 7. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_x4_idd_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n7. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito = result[2] == 0 and result[1] == result[0]
    
    if exito:
        print(f"\n[EXITO] X4_IDD APLICADO COMPLETAMENTE")
    else:
        print(f"\n[PARCIAL] X4_IDD APLICADO - revisar cobertura")
    
    return result[1], result[0], cobertura_pct

if __name__ == "__main__":
    con_x4idd, total, cobertura = aplicar_x4_idd_a_indices()
    
    print(f"\n=== RESULTADO FINAL X4_IDD ===")
    print(f"Cobertura: {con_x4idd}/{total} instituciones ({cobertura:.1f}%)")
    
    if cobertura == 100:
        print(f"[PERFECTO] Variable X4_IDD implementada al 100%")
        print(f"[IMPACTO] Completitud: 9 -> 10 variables metodologicas ({10/13*100:.1f}%)")
        print(f"[METODOLOGIA] PADD real + Regresion contextual con R²=0.268")
    else:
        print(f"[INFO] Implementacion parcial - evaluar si suficiente")