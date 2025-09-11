"""
Script para aplicar X1_NVC calculado a indices_metodologicos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x1_nvc_a_indices():
    """
    Aplica X1_NVC desde CSV calculado con cascada
    """
    
    print("=== APLICANDO X1_NVC A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos calculados
    csv_path = "temp_data/x1_nvc_calculado_20250810_020639.csv"
    print(f"1. CARGANDO DATOS CALCULADOS: {csv_path}")
    
    try:
        df_x1nvc = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_x1nvc)}")
        
        # Distribución por categoría
        print(f"   Distribucion por vulnerabilidad:")
        categorias = {
            1: 'Vulnerabilidad Minima', 
            2: 'Vulnerabilidad Baja',
            3: 'Vulnerabilidad Media',
            4: 'Vulnerabilidad Alta', 
            5: 'Vulnerabilidad Maxima'
        }
        for categoria, count in df_x1nvc['X1_NVC'].value_counts().sort_index().items():
            nombre = categorias.get(categoria, f'Categoria_{categoria}')
            print(f"     {categoria} ({nombre}): {count} instituciones")
        
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/agregar columna X1_NVC
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X1_NVC' not in columnas:
        print("\n2. AGREGANDO COLUMNA X1_NVC...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X1_NVC INTEGER")
        conn.commit()
    else:
        print("\n2. COLUMNA X1_NVC YA EXISTE - ACTUALIZANDO...")
    
    # 3. Aplicar valores X1_NVC
    print("\n3. ACTUALIZANDO VALORES X1_NVC:")
    
    filas_actualizadas = 0
    for _, row in df_x1nvc.iterrows():
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET X1_NVC = ? 
            WHERE CODIGO_MODULAR = ?
        """, (int(row['X1_NVC']), row['codigo_target']))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificación final
    print("\n4. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X1_NVC) con_x1_nvc,
               COUNT(*) - COUNT(X1_NVC) sin_x1_nvc
        FROM indices_metodologicos
    """).fetchone()
    
    cobertura_pct = result[1]/result[0]*100
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X1_NVC: {result[1]} ({cobertura_pct:.1f}%)")
    print(f"   Sin X1_NVC: {result[2]}")
    
    # 5. Distribución en BD
    if result[1] > 0:
        print(f"\n5. DISTRIBUCION X1_NVC EN BD:")
        
        distribucion_bd = cursor.execute("""
            SELECT X1_NVC, COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X1_NVC IS NOT NULL
            GROUP BY X1_NVC
            ORDER BY X1_NVC
        """).fetchall()
        
        categorias_nombres = {
            1: 'Vulnerabilidad Minima', 
            2: 'Vulnerabilidad Baja',
            3: 'Vulnerabilidad Media',
            4: 'Vulnerabilidad Alta', 
            5: 'Vulnerabilidad Maxima'
        }
        
        for nvc_value, cantidad in distribucion_bd:
            nombre = categorias_nombres.get(nvc_value, f'Categoria_{nvc_value}')
            porcentaje = cantidad/result[1]*100
            print(f"   {nvc_value} ({nombre}): {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 6. Verificación coherencia con fuentes
    print(f"\n6. VERIFICACION COHERENCIA:")
    
    # Verificar instituciones con datos EIB vs fuentes originales
    con_datos_eib = cursor.execute("""
        SELECT COUNT(*) 
        FROM indices_metodologicos 
        WHERE X1_NVC IS NOT NULL
    """).fetchone()[0]
    
    instituciones_eib_fuentes = cursor.execute("""
        SELECT COUNT(DISTINCT codigo_modular) 
        FROM (
            SELECT codigo_modular FROM datos_eib_minedu WHERE quintil_pobreza IS NOT NULL
            UNION 
            SELECT codigo_modular FROM variables_eib_mejoradas_final WHERE quintil_pobreza IS NOT NULL
        )
    """).fetchone()[0]
    
    print(f"   Instituciones con X1_NVC en BD: {con_datos_eib}")
    print(f"   Instituciones EIB en fuentes: {instituciones_eib_fuentes}")
    print(f"   Coherencia: {con_datos_eib >= instituciones_eib_fuentes}")
    
    # 7. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_x1_nvc_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n7. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito = result[2] == 0 and result[1] == result[0]
    
    if exito:
        print(f"\n[EXITO] X1_NVC APLICADO COMPLETAMENTE")
    else:
        print(f"\n[PARCIAL] X1_NVC APLICADO - revisar cobertura")
    
    return result[1], result[0], cobertura_pct

if __name__ == "__main__":
    con_x1nvc, total, cobertura = aplicar_x1_nvc_a_indices()
    
    print(f"\n=== RESULTADO FINAL X1_NVC ===")
    print(f"Cobertura: {con_x1nvc}/{total} instituciones ({cobertura:.1f}%)")
    
    if cobertura == 100:
        print(f"[PERFECTO] Variable X1_NVC implementada al 100%")
        print(f"[IMPACTO] Completitud: 8 -> 9 variables metodologicas ({9/13*100:.1f}%)")
    else:
        print(f"[INFO] Implementacion parcial - evaluar si suficiente")