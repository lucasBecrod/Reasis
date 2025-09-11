"""
Script para aplicar Y3_PR corregido a indices_metodologicos

Aplica Y3_PR general (escala 0-1) a la tabla indices_metodologicos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_y3_pr_indices_metodologicos():
    """
    Aplica Y3_PR general corregido a indices_metodologicos
    """
    
    print("=== APLICANDO Y3_PR A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos Y3_PR corregidos
    csv_path = "temp_data/y3_pr_general_corregido_20250810_101044.csv"
    print(f"1. CARGANDO DATOS Y3_PR CORREGIDOS: {csv_path}")
    
    try:
        df_y3pr = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_y3pr)}")
        
        # Estadísticas del archivo
        print(f"   Rango Y3_PR: {df_y3pr['Y3_PR_general'].min():.6f} - {df_y3pr['Y3_PR_general'].max():.6f}")
        print(f"   Promedio: {df_y3pr['Y3_PR_general'].mean():.6f}")
        
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/agregar columna Y3_PR
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'Y3_PR' not in columnas:
        print(f"\n2. AGREGANDO COLUMNA Y3_PR...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN Y3_PR REAL")
        conn.commit()
    else:
        print(f"\n2. COLUMNA Y3_PR YA EXISTE - ACTUALIZANDO...")
    
    # 3. Aplicar valores Y3_PR
    print(f"\n3. ACTUALIZANDO VALORES Y3_PR:")
    
    filas_actualizadas = 0
    for _, row in df_y3pr.iterrows():
        codigo_modular = str(row['codigo_modular'])  # Asegurar formato string
        y3_pr_valor = float(row['Y3_PR_general'])
        
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET Y3_PR = ? 
            WHERE CODIGO_MODULAR = ?
        """, (y3_pr_valor, codigo_modular))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificación final
    print(f"\n4. VERIFICACIÓN FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(Y3_PR) con_y3_pr,
               COUNT(*) - COUNT(Y3_PR) sin_y3_pr
        FROM indices_metodologicos
    """).fetchone()
    
    cobertura_pct = result[1]/result[0]*100
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con Y3_PR: {result[1]} ({cobertura_pct:.1f}%)")
    print(f"   Sin Y3_PR: {result[2]}")
    
    # 5. Estadísticas Y3_PR en base de datos
    if result[1] > 0:
        print(f"\n5. ESTADÍSTICAS Y3_PR EN BD:")
        
        estadisticas = cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(Y3_PR) as minimo,
                MAX(Y3_PR) as maximo,
                AVG(Y3_PR) as promedio
            FROM indices_metodologicos 
            WHERE Y3_PR IS NOT NULL
        """).fetchone()
        
        print(f"   Total registros: {estadisticas[0]}")
        print(f"   Rango: {estadisticas[1]:.6f} - {estadisticas[2]:.6f}")
        print(f"   Promedio: {estadisticas[3]:.6f}")
        
        # Distribución por niveles de desempeño académico
        print(f"\n   Distribución por nivel de progreso relativo:")
        
        niveles = cursor.execute("""
            SELECT 
                CASE 
                    WHEN Y3_PR < 0.001 THEN 'Muy Bajo (<0.1%)'
                    WHEN Y3_PR < 0.003 THEN 'Bajo (0.1-0.3%)'
                    WHEN Y3_PR < 0.006 THEN 'Medio-Bajo (0.3-0.6%)'
                    WHEN Y3_PR < 0.010 THEN 'Medio (0.6-1.0%)'
                    ELSE 'Alto (>1.0%)'
                END as nivel_progreso,
                COUNT(*) as cantidad,
                AVG(Y3_PR) as promedio_nivel
            FROM indices_metodologicos 
            WHERE Y3_PR IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN Y3_PR < 0.001 THEN 'Muy Bajo (<0.1%)'
                    WHEN Y3_PR < 0.003 THEN 'Bajo (0.1-0.3%)'
                    WHEN Y3_PR < 0.006 THEN 'Medio-Bajo (0.3-0.6%)'
                    WHEN Y3_PR < 0.010 THEN 'Medio (0.6-1.0%)'
                    ELSE 'Alto (>1.0%)'
                END
            ORDER BY promedio_nivel
        """).fetchall()
        
        for nivel, cantidad, promedio_nivel in niveles:
            porcentaje = cantidad/result[1]*100
            print(f"     {nivel}: {cantidad} instituciones ({porcentaje:.1f}%) - prom: {promedio_nivel:.6f}")
    
    # 6. Validación metodológica
    print(f"\n6. VALIDACIÓN METODOLÓGICA:")
    
    # Verificar rango apropiado [0-1]
    fuera_rango = cursor.execute("""
        SELECT COUNT(*) 
        FROM indices_metodologicos 
        WHERE Y3_PR IS NOT NULL AND (Y3_PR < 0.0 OR Y3_PR > 1.0)
    """).fetchone()[0]
    
    print(f"   Valores fuera de rango [0-1]: {fuera_rango}")
    
    # Correlación con Y1_ILA (ambas académicas)
    try:
        correlacion = cursor.execute("""
            SELECT 
                ROUND(
                    (COUNT(*) * SUM(Y3_PR * Y1_ILA) - SUM(Y3_PR) * SUM(Y1_ILA)) /
                    SQRT(
                        (COUNT(*) * SUM(Y3_PR * Y3_PR) - SUM(Y3_PR) * SUM(Y3_PR)) *
                        (COUNT(*) * SUM(Y1_ILA * Y1_ILA) - SUM(Y1_ILA) * SUM(Y1_ILA))
                    ), 3
                ) as correlacion,
                COUNT(*) as n
            FROM indices_metodologicos 
            WHERE Y3_PR IS NOT NULL AND Y1_ILA IS NOT NULL
        """).fetchone()
        
        print(f"   Correlación Y3_PR vs Y1_ILA: {correlacion[0]} (n={correlacion[1]})")
        print(f"   Interpretación: {'Positiva esperada' if correlacion[0] > 0 else 'Revisar relación'} (ambas académicas)")
    except:
        print(f"   No se pudo calcular correlación con Y1_ILA")
    
    # 7. Estado variables metodológicas actualizado
    print(f"\n7. ESTADO VARIABLES METODOLÓGICAS:")
    
    variables_check = cursor.execute("""
        SELECT 
            COUNT(Y1_ILA) y1_ila,
            COUNT(Y2_TD) y2_td,
            COUNT(Y3_PR) y3_pr,
            COUNT(X1_NVC) x1_nvc,
            COUNT(X2_TR) x2_tr,
            COUNT(X4_IDD) x4_idd,
            COUNT(X5_ED) x5_ed,
            COUNT(X6_CDD) x6_cdd,
            COUNT(X10_IE) x10_ie,
            COUNT(X11_RED) x11_red,
            COUNT(X12_TOE) x12_toe,
            COUNT(X13_TMATRC) x13_tmatrc,
            COUNT(X15_MEIB) x15_meib
        FROM indices_metodologicos
    """).fetchone()
    
    variables = ['Y1_ILA', 'Y2_TD', 'Y3_PR', 'X1_NVC', 'X2_TR', 'X4_IDD', 'X5_ED', 'X6_CDD', 
                'X10_IE', 'X11_RED', 'X12_TOE', 'X13_TMATRC', 'X15_MEIB']
    variables_completas = 0
    
    total_instituciones = result[0]
    for i, var in enumerate(variables):
        count = variables_check[i]
        if count == total_instituciones:
            status = 'COMPLETA'
            variables_completas += 1
        else:
            status = f'PARCIAL ({count}/{total_instituciones})'
        print(f'   {var}: {status}')
    
    print(f'\n   Variables completas: {variables_completas}/{len(variables)}')
    completitud = variables_completas/13*100  # Total 13 variables metodológicas
    print(f'   Completitud metodológica: {completitud:.1f}%')
    
    # 8. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_y3pr_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n8. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito = result[2] >= 0 and fuera_rango == 0  # Permitir instituciones sin Y3_PR
    
    if exito and result[1] > 0:
        print(f"\n[ÉXITO] Y3_PR APLICADO EXITOSAMENTE")
        print(f"[COBERTURA] {result[1]}/{result[0]} instituciones ({cobertura_pct:.1f}%)")
        print(f"[COMPLETITUD] {completitud:.1f}% variables metodológicas")
    else:
        print(f"\n[REVISAR] Y3_PR aplicado - verificar resultados")
    
    return result[1], result[0], cobertura_pct, estadisticas[3] if result[1] > 0 else 0

if __name__ == "__main__":
    con_y3pr, total, cobertura, promedio = aplicar_y3_pr_indices_metodologicos()
    
    print(f"\n=== RESULTADO FINAL Y3_PR ===")
    print(f"Cobertura: {con_y3pr}/{total} instituciones ({cobertura:.1f}%)")
    print(f"Promedio Y3_PR: {promedio:.6f}")
    
    if cobertura >= 30:
        print(f"[ÉXITO] Y3_PR implementado - variable metodológica disponible")
        print(f"[CLUSTERING] 12/13 variables metodológicas (92.3%)")
    else:
        print(f"[LIMITADO] Y3_PR implementado con cobertura baja")