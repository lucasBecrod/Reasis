"""
Script para aplicar X15_MEIB calculado a indices_metodologicos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_x15_meib_a_indices():
    """
    Aplica X15_MEIB desde CSV calculado con cascada
    """
    
    print("=== APLICANDO X15_MEIB A INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Cargar datos calculados
    csv_path = "temp_data/x15_meib_calculado_20250810_015906.csv"
    print(f"1. CARGANDO DATOS CALCULADOS: {csv_path}")
    
    try:
        df_x15meib = pd.read_csv(csv_path)
        print(f"   Registros cargados: {len(df_x15meib)}")
        
        # Distribución por categoría
        print(f"   Distribución por modalidad:")
        categorias = {0: 'No EIB', 1: 'EIB Fortalecimiento', 2: 'EIB Revitalización'}
        for categoria, count in df_x15meib['X15_MEIB'].value_counts().sort_index().items():
            nombre = categorias.get(categoria, f'Categoria_{categoria}')
            print(f"     {categoria} ({nombre}): {count} instituciones")
        
    except FileNotFoundError:
        print(f"   ERROR: Archivo no encontrado")
        return False
    
    # 2. Verificar/agregar columna X15_MEIB
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    if 'X15_MEIB' not in columnas:
        print("\n2. AGREGANDO COLUMNA X15_MEIB...")
        cursor.execute("ALTER TABLE indices_metodologicos ADD COLUMN X15_MEIB INTEGER")
        conn.commit()
    else:
        print("\n2. COLUMNA X15_MEIB YA EXISTE - ACTUALIZANDO...")
    
    # 3. Aplicar valores X15_MEIB
    print("\n3. ACTUALIZANDO VALORES X15_MEIB:")
    
    filas_actualizadas = 0
    for _, row in df_x15meib.iterrows():
        cursor.execute("""
            UPDATE indices_metodologicos 
            SET X15_MEIB = ? 
            WHERE CODIGO_MODULAR = ?
        """, (int(row['X15_MEIB']), row['codigo_target']))
        
        if cursor.rowcount > 0:
            filas_actualizadas += cursor.rowcount
    
    conn.commit()
    print(f"   Filas actualizadas: {filas_actualizadas}")
    
    # 4. Verificación final
    print("\n4. VERIFICACION FINAL:")
    
    result = cursor.execute("""
        SELECT COUNT(*) total,
               COUNT(X15_MEIB) con_x15_meib,
               COUNT(*) - COUNT(X15_MEIB) sin_x15_meib
        FROM indices_metodologicos
    """).fetchone()
    
    cobertura_pct = result[1]/result[0]*100
    print(f"   Total instituciones: {result[0]}")
    print(f"   Con X15_MEIB: {result[1]} ({cobertura_pct:.1f}%)")
    print(f"   Sin X15_MEIB: {result[2]}")
    
    # 5. Distribución en BD
    if result[1] > 0:
        print(f"\n5. DISTRIBUCION X15_MEIB EN BD:")
        
        distribucion_bd = cursor.execute("""
            SELECT X15_MEIB, COUNT(*) as cantidad
            FROM indices_metodologicos 
            WHERE X15_MEIB IS NOT NULL
            GROUP BY X15_MEIB
            ORDER BY X15_MEIB
        """).fetchall()
        
        categorias_nombres = {0: 'No EIB', 1: 'EIB Fortalecimiento', 2: 'EIB Revitalización'}
        
        for meib_value, cantidad in distribucion_bd:
            nombre = categorias_nombres.get(meib_value, f'Categoria_{meib_value}')
            porcentaje = cantidad/result[1]*100
            print(f"   {meib_value} ({nombre}): {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 6. Verificación coherencia con fuentes
    print(f"\n6. VERIFICACION COHERENCIA:")
    
    # Verificar instituciones EIB vs fuentes originales
    eib_bd = cursor.execute("""
        SELECT COUNT(*) 
        FROM indices_metodologicos 
        WHERE X15_MEIB IN (1, 2)
    """).fetchone()[0]
    
    eib_fuentes = cursor.execute("""
        SELECT COUNT(DISTINCT codigo_modular) 
        FROM (
            SELECT codigo_modular FROM datos_eib_minedu 
            UNION 
            SELECT codigo_modular FROM variables_eib_mejoradas_final
        )
    """).fetchone()[0]
    
    print(f"   Instituciones EIB en BD: {eib_bd}")
    print(f"   Instituciones EIB en fuentes: {eib_fuentes}")
    print(f"   Coherencia: {eib_bd <= eib_fuentes}")
    
    # 7. Respaldo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/indices_metodologicos_con_x15_meib_{timestamp}.csv"
    
    df_backup = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_backup.to_csv(backup_path, index=False)
    print(f"\n7. RESPALDO CREADO: {backup_path}")
    
    conn.close()
    
    # Evaluar éxito
    exito = result[2] == 0 and result[1] == result[0]
    
    if exito:
        print(f"\n[EXITO] X15_MEIB APLICADO COMPLETAMENTE")
    else:
        print(f"\n[PARCIAL] X15_MEIB APLICADO - revisar cobertura")
    
    return result[1], result[0], cobertura_pct

if __name__ == "__main__":
    con_x15meib, total, cobertura = aplicar_x15_meib_a_indices()
    
    print(f"\n=== RESULTADO FINAL X15_MEIB ===")
    print(f"Cobertura: {con_x15meib}/{total} instituciones ({cobertura:.1f}%)")
    
    if cobertura == 100:
        print(f"[PERFECTO] Variable X15_MEIB implementada al 100%")
        print(f"[IMPACTO] Completitud: 7 -> 8 variables metodologicas ({8/13*100:.1f}%)")
    else:
        print(f"[INFO] Implementacion parcial - evaluar si suficiente")